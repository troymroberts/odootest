
import json
import logging
import pprint
import hashlib

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class WipayController(http.Controller):
    _return_url = '/payment/wipay/return'
    _webhook_url = '/payment/wipay/webhook'
    _pay_route = '/payment/wipay/pay'

    @http.route('/payment/wipay/return', type='http', auth='public', website=True)
    def wipay_return(self, **kwargs):
        tx_ref = kwargs.get('order_id') or kwargs.get('transaction_id')
        message = kwargs.get('message', '')
        status = kwargs.get('status', 'failed')

        tx = request.env['payment.transaction'].sudo().search([('reference', '=', tx_ref)], limit=1)
        if tx:

            # Update status
            if status == 'success':
                tx._set_done()  # ✅ Odoo standard for marking transaction as paid
            else:

                tx._set_error(f"Payment declined: {message}")

        request.env['payment.transaction'].sudo()._handle_notification_data('wipay',kwargs)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def wipay_webhook(self, **data):
        """ Process the notification data sent by Wipay to the webhook."""
        _logger.info("Received Wipay webhook data:\n%s", pprint.pformat(data))
        
        # If the data is in the request body rather than in the query parameters
        if not data and request.httprequest.data:
            try:
                data = json.loads(request.httprequest.data)
            except (ValueError, json.JSONDecodeError):
                _logger.exception("Unable to decode webhook data from Wipay")
                raise Forbidden()
        
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('wipay', data)
        except ValidationError:
            _logger.exception("Unable to handle notification data from Wipay")
            return 'ko'
        
        return 'ok'
        
    @http.route(_pay_route, type='json', auth='public')
    def wipay_pay(self, provider_id, payment_method_id=233, amount=None, flow=None, currency_id=None,
                  partner_id=None, invoice_id=None, access_token=None, **kwargs):

        base_url = request.env['payment.provider'].get_base_url()
        
        # Create the transaction
        provider_sudo = request.env['payment.provider'].sudo().browse(provider_id)
        reference = request.env['payment.transaction']._compute_reference(
            provider_code=provider_sudo.code, prefix=kwargs.get('prefix')
        )


        tx_sudo = request.env['payment.transaction'].sudo().create({
            'provider_id': provider_id,
            'reference': reference,
            'amount': amount,
            'currency_id': currency_id,
            'partner_id': partner_id,
            'operation': 'online_direct',
            'payment_method_line_id': 233,
            'payment_method_id': 233,
            'invoice_ids': [(6, 0, [invoice_id])] if invoice_id else None,
        })
        
        # Process payment and get redirect
        return tx_sudo._get_processing_values()