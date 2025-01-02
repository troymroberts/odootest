import logging
import requests
from requests.exceptions import Timeout
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # Fields
    code = fields.Selection(
        selection_add=[('wipay', 'Wipay')],
        ondelete={'wipay': 'set default'}
    )
    wipay_api_key = fields.Char(string='Wipay API Key', required_if_provider='wipay')
    wipay_account_number = fields.Char(string='Wipay Account Number', required_if_provider='wipay')
    wipay_environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('live', 'Live')
    ], string='Environment', default='sandbox', required_if_provider='wipay')
    wipay_avs_enabled = fields.Boolean(string='Enable AVS', default=False)
    wipay_tokenization_enabled = fields.Boolean(string='Enable Tokenization', default=False)

    # Field Validation
    @api.constrains('wipay_api_key')
    def _check_wipay_api_key(self):
        for provider in self:
            if provider.code == 'wipay' and not provider.wipay_api_key:
                raise ValidationError("Wipay API Key is required for Wipay providers.")

    @api.constrains('wipay_account_number')
    def _check_wipay_account_number(self):
        for provider in self:
            if provider.code == 'wipay' and not provider.wipay_account_number:
                raise ValidationError("Wipay Account Number is required for Wipay providers.")

    # Fee Calculation
    def _compute_fee(self, amount, currency):
        if self.code != 'wipay':
            return super()._compute_fee(amount, currency)
        if self.wipay_environment == 'live':
            if currency == 'USD':
                return amount * 0.038 + 0.25
            elif currency == 'TTD':
                return amount * 0.035 + 0.25
            elif currency == 'JMD':
                return amount * 0.042
        return 0

    # API Request Handling
    def _wipay_make_request(self, endpoint, data):
        """
        Make a request to the Wipay API.

        :param endpoint: The API endpoint to request.
        :param data: The data to send in the request.
        :return: The JSON response from the API.
        :raise ValidationError: If the request fails or times out.
        """
        _logger.info("Making request to Wipay API: %s", endpoint)
        data.update({
            'account_number': self.wipay_account_number,
            'api_key': self.wipay_api_key,
            'environment': self.wipay_environment,
        })
        if self.wipay_avs_enabled:
            data['avs'] = '1'
        if self.wipay_tokenization_enabled:
            data['tokenize'] = '1'
        try:
            response = requests.post(endpoint, data=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get('status') == 'success':
                self.env['payment.transaction'].sudo()._set_transaction_done()
            elif response_data.get('status') == 'failed':
                self.env['payment.transaction'].sudo()._set_transaction_cancel()
            _logger.info("Wipay API response: %s", response_data)
            return response_data
        except Timeout:
            _logger.error("Wipay API request timed out")
            raise ValidationError("Wipay API request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            _logger.error("Wipay API HTTP error: %s", e)
            raise ValidationError("Wipay API HTTP error. Please check your settings.")
        except Exception as e:
            _logger.error("Wipay API request failed: %s", e)
            raise ValidationError("Wipay API request failed. Please check your settings.")

    # Default Payment Method
    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.code != 'wipay':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment.payment_method_wipay').id