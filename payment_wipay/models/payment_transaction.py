# Updated WiPay payment integration with fixed error handling

import datetime
import logging
import pdb
import pprint
import requests
import json
import hashlib
from werkzeug import urls

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    wipay_payment_id = fields.Char("Wipay Payment ID")

    def _get_payment_method_line_fields(self):
        res = super()._get_payment_method_line_fields()
        if self.provider_code == 'wipay' and not res.get('payment_method_line_id'):
            journal = self.acquirer_id.journal_id
            method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', journal.id),
                ('payment_method_id.code', '=', 'manual'),
            ], limit=1)
            if method_line:
                res['payment_method_line_id'] = method_line.id
        return res

    def _get_specific_rendering_values(self, processing_values):
        try:
            res = super()._get_specific_rendering_values(processing_values)
            if self.provider_code != 'wipay':
                return res
            base_url = self.provider_id.get_base_url()
            return_url = urls.url_join(base_url, '/payment/wipay/return')
            notify_url = urls.url_join(base_url, '/payment/wipay/webhook')
            origin = "WiPay"
            country_code = self.partner_id.country_id.code
            payment_data = {
                'account_number': self.provider_id.wipay_merchant_account_id,
                'order_id': self.reference,
                'environment': 'live' if self.provider_id.state == 'enable' else 'sandbox',
                'response_url': return_url,
                'webhook_url': notify_url,
                'email': self.partner_email,
                'name': self.partner_name,
                'phone': self.partner_phone,
                'zipcode': self.partner_zip,
                'addr1': self.partner_address,
                'addr2': self.partner_city,
                'origin': origin,
                'fee_structure': 'customer_pay',
                'method': 'credit_card',
                'description': f"Payment for {self.reference}"
            }

            if self.provider_id.wipay_api_key:
                signature_string = f"{self.provider_id.wipay_api_key}{self.provider_id.wipay_merchant_account_id}{self.amount:.2f}{self.reference}"
                signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
                payment_data['signature'] = signature

            try:
                _logger.info("Making request to Wipay with data: %s", pprint.pformat(payment_data))
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                if self.provider_id.wipay_api_key:
                    headers['Authorization'] = f"Bearer {self.provider_id.wipay_api_key}"

                if country_code not in ['TT', 'BB', 'JM']:
                    self._set_error(f"Wipay: Country {self.partner_id.country_id.name} not supported, Check your Billing Address.")
                    raise UserError(_("Wipay: Country %s not supported, Check your Billing Address.") % self.partner_id.country_id.name)

                pay_currency = self.currency_id.name
                if pay_currency != self.provider_id.wipay_currency:
                    src_currency = self.env['res.currency'].search([('name', '=', self.provider_id.wipay_currency)])
                    print(self.amount)
                    print(src_currency.name)

                    print(self.currency_id.name)
                    pay_amount = self.currency_id._convert(self.amount, src_currency)
                else:
                    pay_amount = self.amount

                print(pay_amount)

                payment_data['country_code'] = country_code
                payment_data['currency'] = self.provider_id.wipay_currency
                payment_data['total'] = f"{pay_amount:.2f}"

                response = requests.post(self.provider_id.wipay_api_url, data=payment_data, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                _logger.info("Received response from Wipay: %s", pprint.pformat(response_data))
                self.provider_reference = response_data.get('transaction_id')
                if response_data.get('url'):
                    self.wipay_payment_id = response_data.get('transaction_id')
                    payment_data.update({
                        'payment_url': response_data.get('url'),
                        'reference': self.reference,
                        'provider_reference': response_data.get('transaction_id'),
                        'post_params': payment_data
                    })
                    return payment_data
                else:
                    error_msg = response_data.get('message', 'Unknown error')
                    _logger.error("Wipay payment error: %s", error_msg)
                    raise UserError(_("Wipay: %s") % error_msg)

            except (requests.exceptions.RequestException, ValueError) as e:
                _logger.exception("Error contacting Wipay API %s", str(e))
                raise UserError(_("Could not establish connection with Wipay API: %s") % str(e))

        except Exception as e:
            raise UserError(_("Could not establish connection with Wipay API: %s") % str(e))

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'wipay' or tx:
            return tx

        reference = notification_data.get('order_id')
        if not reference:
            raise UserError(_("Wipay: No transaction found matching reference %s.") % reference)

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'wipay')])
        if not tx:
            raise UserError(_("Wipay: No transaction found matching reference %s.") % reference)
        return tx

    def _get_specific_checkout_rendering_values(self, payment_method_id=None):
        res = super()._get_specific_checkout_rendering_values(payment_method_id)
        if self.provider_code != 'wipay':
            return res
        self.provider_id.sudo().write({
            'state': 'enabled' if self.provider_id.state == 'test' else self.provider_id.state,
        })
        return {
            'provider_code': 'wipay',
            'provider_name': self.provider_id.name,
            'reference': self.reference,
        }

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'wipay':
            return

        transaction_id = notification_data.get('transaction_id')
        payment_status = notification_data.get('status')
        received_signature = notification_data.get('signature')

        if received_signature and self.provider_id.wipay_secret_key:
            signature_string = f"{self.provider_id.wipay_secret_key}{transaction_id}{self.reference}"
            expected_signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
            if received_signature != expected_signature:
                _logger.warning("Received invalid signature from Wipay")
                raise UserError(_("Wipay: Invalid signature received."))

        self.wipay_payment_id = transaction_id
        payment_method = self.env['payment.method'].search([('code', '=', 'wipay')], limit=1)
        if not payment_method:
            raise UserError(_("Wipay: Payment method not found."))
        self.payment_method_id = payment_method.id

        if payment_status == 'success':
            self._set_done()
        elif payment_status == 'pending':
            self._set_pending()
        elif payment_status == 'failed':
            self._set_canceled(_("Wipay: Payment failed."))
        else:
            _logger.warning("Received unrecognized payment status from Wipay: %s", payment_status)
            self._set_error(_("Wipay: Received unrecognized payment status: %s") % payment_status)

    def _generate_payment_vals_from_tx(self, tx):
        vals = super()._generate_payment_vals_from_tx(tx)
        if tx.provider_code == 'wipay':
            journal = tx.acquirer_id.journal_id
            method_line = tx.env['account.payment.method.line'].search([
                ('journal_id', '=', journal.id),
                ('payment_method_id.code', 'in', ['manual', 'electronic']),
            ], limit=1)
            if method_line:
                vals['payment_method_line_id'] = method_line.id
            else:
                _logger.warning("⚠️ No payment method line found for WiPay journal: %s", journal.name)
        return vals

