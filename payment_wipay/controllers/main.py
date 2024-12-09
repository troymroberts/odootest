# payment_wipay/controllers/main.py

import logging
import pprint
import json
from werkzeug.exceptions import Forbidden
from werkzeug.urls import url_join

from odoo import http, _, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo.tools import html_escape
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

class WiPayController(http.Controller):
    _return_url = '/payment/wipay/return'
    _webhook_url = '/payment/wipay/webhook'
    _api_url = '/payment/wipay/api'
    _cancel_url = '/payment/wipay/cancel'

    @http.route(['/payment/wipay/get_processing_values'], type='json', auth='public')
    def wipay_get_processing_values(self, **data):
        """Get processing values for WiPay payment form.
        
        Returns:
            dict: Processing values including API URL and parameters
        """
        try:
            # Extract reference from data
            reference = data.get('reference')
            if not reference:
                raise ValidationError(_("Missing transaction reference"))

            # Get transaction
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'wipay')
            ], limit=1)
            
            if not tx_sudo:
                raise ValidationError(_("Transaction not found"))
            
            # Get processing values
            processing_values = tx_sudo._get_specific_rendering_values({})
            api_url = tx_sudo.provider_id._wipay_get_api_url()
            
            return {
                'api_url': api_url,
                'api_params': processing_values,
                'reference': reference
            }
            
        except Exception as e:
            _logger.exception("Error getting WiPay processing values")
            raise ValidationError(_("WiPay: %s", str(e)))

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def wipay_return_from_checkout(self, **data):
        """Handle the response from WiPay after payment.
        
        Returns:
            http.Response: Redirect to payment status page
        """
        _logger.info(
            "handling redirection from WiPay with data:\n%s", 
            pprint.pformat(data)
        )
        
        try:
            # Clean received data
            cleaned_data = {
                k: html_escape(str(v)) if isinstance(v, (str, int, float)) else v
                for k, v in data.items() if v is not None
            }
            
            # Handle the notification data
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'wipay', 
                cleaned_data
            )
            
        except ValidationError as e:
            _logger.exception(
                "unable to handle the notification data: %s", 
                str(e)
            )
        except Exception as e:
            _logger.exception(
                "error while handling notification data: %s", 
                str(e)
            )
        
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def wipay_webhook(self):
        """Handle asynchronous notifications from WiPay.
        
        Returns:
            dict: Status indication
        """
        data = json.loads(request.httprequest.data)
        _logger.info(
            "handling webhook notification from WiPay with data:\n%s",
            pprint.pformat(data)
        )

        try:
            # Verify webhook authenticity
            if not self._verify_webhook_signature(data):
                _logger.warning("Invalid webhook signature")
                raise Forbidden()

            # Clean the received data
            cleaned_data = {
                k: html_escape(str(v)) if isinstance(v, (str, int, float)) else v
                for k, v in data.items() if v is not None
            }
            
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'wipay', 
                cleaned_data
            )
            
        except ValidationError as e:
            _logger.exception(
                "unable to handle the webhook notification data: %s", 
                str(e)
            )
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            _logger.exception(
                "error while handling webhook notification data: %s", 
                str(e)
            )
            return {'status': 'error', 'message': 'Internal server error'}
            
        return {'status': 'ok'}

    @http.route(_cancel_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def wipay_cancel(self, **data):
        """Handle payment cancellation.
        
        Returns:
            http.Response: Redirect to payment status page
        """
        _logger.info(
            "handling cancellation from WiPay with data:\n%s",
            pprint.pformat(data)
        )
        
        try:
            # Clean received data
            cleaned_data = {
                k: html_escape(str(v)) if isinstance(v, (str, int, float)) else v
                for k, v in data.items() if v is not None
            }
            
            # Add cancellation status
            cleaned_data['status'] = 'failed'
            cleaned_data['message'] = 'Payment was cancelled by the user'
            
            # Handle the notification data
            request.env['payment.transaction'].sudo()._handle_notification_data(
                'wipay', 
                cleaned_data
            )
            
        except ValidationError as e:
            _logger.exception(
                "unable to handle the cancellation data: %s", 
                str(e)
            )
        except Exception as e:
            _logger.exception(
                "error while handling cancellation data: %s", 
                str(e)
            )
        
        return request.redirect('/payment/status')

    @http.route([_api_url], type='json', auth='public', csrf=False)
    def wipay_api(self, **data):
        """Handle API requests for WiPay integration.
        
        Returns:
            dict: API response
        """
        try:
            command = data.get('command')
            if not command:
                raise ValidationError(_("Missing command parameter"))

            if command == 'check_status':
                return self._check_transaction_status(data)
            elif command == 'get_fees':
                return self._calculate_fees(data)
            else:
                raise ValidationError(_("Invalid command"))
                
        except ValidationError as e:
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            _logger.exception("WiPay API error")
            return {'status': 'error', 'message': 'Internal server error'}

    def _verify_webhook_signature(self, data):
        """Verify the authenticity of the webhook notification.
        
        Args:
            data (dict): The notification data
            
        Returns:
            bool: True if signature is valid
        """
        if not data.get('hash'):
            _logger.warning("received webhook notification without hash")
            return False
            
        try:
            tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'wipay', 
                data
            )
            expected_hash = tx._wipay_calculate_hash(data)
            return data.get('hash') == expected_hash
        except ValidationError:
            return False
        except Exception as e:
            _logger.exception("error verifying webhook signature: %s", str(e))
            return False

    def _check_transaction_status(self, data):
        """Check the status of a transaction.
        
        Args:
            data (dict): Request data including reference
            
        Returns:
            dict: Transaction status
        """
        reference = data.get('reference')
        if not reference:
            raise ValidationError(_("Missing transaction reference"))
            
        tx_sudo = request.env['payment.transaction'].sudo().search([
            ('reference', '=', reference),
            ('provider_code', '=', 'wipay')
        ], limit=1)
        
        if not tx_sudo:
            raise ValidationError(_("Transaction not found"))
            
        return {
            'status': 'success',
            'transaction_status': tx_sudo.state,
            'reference': tx_sudo.reference,
            'amount': float_round(tx_sudo.amount, 2),
            'currency': tx_sudo.currency_id.name,
            'date': tx_sudo.create_date.strftime('%Y-%m-%d %H:%M:%S') if tx_sudo.create_date else None,
        }

    def _calculate_fees(self, data):
        """Calculate transaction fees.
        
        Args:
            data (dict): Request data including amount and currency
            
        Returns:
            dict: Fee calculation
        """
        try:
            amount = float(data.get('amount', 0))
            currency = data.get('currency')
            country_code = data.get('country_code')
            
            if not all([amount, currency, country_code]):
                raise ValidationError(_("Missing required parameters"))
                
            if amount <= 0:
                raise ValidationError(_("Invalid amount"))
                
            provider = request.env['payment.provider'].sudo().search([
                ('code', '=', 'wipay'),
                ('state', 'in', ['enabled', 'test'])
            ], limit=1)
            
            if not provider:
                raise ValidationError(_("WiPay provider not found or not enabled"))
                
            # Create temporary transaction for fee calculation
            tx_sudo = request.env['payment.transaction'].sudo().create({
                'amount': amount,
                'currency_id': request.env['res.currency'].search([('name', '=', currency)], limit=1).id,
                'provider_id': provider.id,
            })
            
            fees = tx_sudo._compute_fees(amount, currency, country_code)
            
            return {
                'status': 'success',
                'amount': float_round(amount, 2),
                'currency': currency,
                'fees': float_round(fees, 2),
                'total': float_round(amount + fees, 2)
            }
            
        except Exception as e:
            _logger.exception("Error calculating fees")
            raise ValidationError(str(e))