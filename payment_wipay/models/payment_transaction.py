# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import logging
import pdb
import pprint
import requests
import json
import hashlib
from werkzeug import urls

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    wipay_payment_id = fields.Char("Wipay Payment ID")

    def _get_payment_method_line_fields(self):
        """Ensure payment_method_line_id is correctly set before post-processing"""
        res = super()._get_payment_method_line_fields()
        if self.provider_code == 'wipay' and not res.get('payment_method_line_id'):
            journal = self.acquirer_id.journal_id
            method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', journal.id),
                ('payment_method_id.code', '=', 'manual'),  # or 'electronic' if you're using that
            ], limit=1)
            if method_line:
                res['payment_method_line_id'] = method_line.id
        return res

    def _get_specific_rendering_values(self, processing_values):

        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'wipay':
            return res

        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, '/payment/wipay/return')
        notify_url = urls.url_join(base_url, '/payment/wipay/webhook')
        origin = "WiPay-example_app"

        # Prepare the payment request to Wipay
        payment_data = {
            'account_number': self.provider_id.wipay_merchant_account_id,
            'total': f"{self.amount:.2f}",
            'currency': 'TTD',  # self.currency_id.name,
            'order_id': self.reference,
            'country_code': 'TT',  # self.company_id.country_id.code or
            'environment': 'sandbox',
            'response_url': return_url,
            'webhook_url': notify_url,
            'email': self.partner_email,
            'name': self.partner_name,
            'origin': origin,
            'fee_structure': 'customer_pay',
            'method': 'credit_card',
            'description': f"Payment for {self.reference}"
        }

        # Create signature for the request if api key is provided
        if self.provider_id.wipay_api_key:
            signature_string = f"{self.provider_id.wipay_api_key}{self.provider_id.wipay_merchant_account_id}{self.amount:.2f}{self.reference}"
            signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
            payment_data['signature'] = signature

        # Make request to Wipay to get payment URL
        try:
            _logger.info("Making request to Wipay with data: %s", pprint.pformat(payment_data))
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'

            }

            # Add authorization header if API key is available
            if self.provider_id.wipay_api_key:
                headers['Authorization'] = f"Bearer {self.provider_id.wipay_api_key}"

            response = requests.post(
                self.provider_id.wipay_api_url,
                data=payment_data,  # NOT json=
                headers=headers
            )

            print(response.text)
            # print(response.result)
            response.raise_for_status()
            response_data = response.json()
            _logger.info("Received response from Wipay: %s", pprint.pformat(response_data))

            if response_data.get('url'):
                self.wipay_payment_id = response_data.get('transaction_id')
                payment_data.update({
                    'payment_url': response_data.get('url'),
                    'reference': self.reference,
                    'post_params': payment_data  # ✅ NOT json.dumps
                })
                return payment_data


            else:
                error_msg = response_data.get('message', 'Unknown error')
                _logger.error("Wipay payment error: %s", error_msg)
                raise ValidationError(_("Wipay: %s", error_msg))

        except (requests.exceptions.RequestException, ValueError) as e:
            _logger.exception(f"Error contacting Wipay API {e}")
            raise ValidationError(_("Could not establish connection with Wipay API: %s", str(e)))

        return res

    def _get_tx_from_feedback_data(self, provider_code, data):
        """ Override of payment to find the transaction based on Wipay data.
        """
        tx = super()._get_tx_from_feedback_data(provider_code, data)
        if provider_code != 'wipay' or tx:
            return tx

        reference = data.get('order_id')
        if reference:
            tx = self.search([('reference', '=', reference), ('provider_code', '=', 'wipay')])
        return tx

    def _get_specific_checkout_rendering_values(self, payment_method_id=None):
        """ Override of payment to return Wipay-specific checkout rendering values.
        
        :param int payment_method_id: The optional payment method used for the checkout
        :return: The dict of provider-specific checkout rendering values
        :rtype: dict
        """
        res = super()._get_specific_checkout_rendering_values(payment_method_id)
        if self.provider_code != 'wipay':
            return res

        # Store transaction reference for later use
        self.provider_id.sudo().write({
            'state': 'enabled' if self.provider_id.state == 'test' else self.provider_id.state,
        })

        return {
            'provider_code': 'wipay',
            'provider_name': self.provider_id.name,
            'reference': self.reference,
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):

        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'wipay' or tx:
            return tx

        # Find transaction based on order_id (our reference)
        reference = notification_data.get('order_id')
        if not reference:
            raise ValidationError("Wipay: " + _("No transaction found matching reference %s.", reference))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'wipay')])
        if not tx:
            raise ValidationError("Wipay: " + _("No transaction found matching reference %s.", reference))

        return tx

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
                raise ValidationError(_("Wipay: Invalid signature received."))

        self.wipay_payment_id = transaction_id

        # ✅ Dynamically fetch method instead of hardcoding
        payment_method = self.env['payment.method'].search([('code', '=', 'wipay')], limit=1)
        if not payment_method:
            raise ValidationError(_("Wipay: Payment method not found."))
        self.payment_method_id = payment_method.id

        if payment_status == 'success':
            self._set_done()
        elif payment_status == 'pending':
            self._set_pending()
        elif payment_status == 'failed':
            self._set_canceled("Wipay: " + _("Payment failed."))
        else:
            _logger.warning("Received unrecognized payment status from Wipay: %s", payment_status)

            self._set_error("Wipay: " + _("Received unrecognized payment status: %s", payment_status))

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
