import logging
import hashlib
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class WipayController(http.Controller):
    @http.route('/payment/wipay/return', type='http', auth='public', csrf=False)
    def wipay_return(self, **post):
        _logger.info("Wipay return with data: %s", post)
        tx = request.env['payment.transaction'].sudo()._handle_notification('wipay', post)
        return request.redirect('/payment/status')

    @http.route('/payment/wipay/notify', type='http', auth='public', csrf=False, methods=['POST'])
    def wipay_notify(self, **post):
        _logger.info("Wipay notification with data: %s", post)
        provider = request.env['payment.provider'].sudo().search([('code', '=', 'wipay')], limit=1)
        if provider:
            hash_str = post.get('transaction_id') + post.get('total') + provider.wipay_api_key
            hash_value = hashlib.md5(hash_str.encode()).hexdigest()
            if hash_value == post.get('hash'):
                tx = request.env['payment.transaction'].sudo()._handle_notification('wipay', post)
                return 'OK'
        return 'Invalid hash'