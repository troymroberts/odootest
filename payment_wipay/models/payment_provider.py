# -*- coding: utf-8 -*-

import logging
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.website.models import ir_http

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wipay', "Wipay")],
        ondelete={'wipay': 'set default'},
    )
    wipay_merchant_account_id = fields.Char(
        string="Merchant Account ID",
        help="The merchant account identifier provided by Wipay",
        default='1234567890'
    )
    wipay_api_key = fields.Char(
        string="API Key",
        help="The API key provided by Wipay",
        default='123'
    )
    wipay_secret_key = fields.Char(
        string="Secret Key",
        help="The secret key provided by Wipay for signature verification",
        default='123'
    )
    wipay_api_url = fields.Char(
        string="API URL",
        help="The base URL for WiPay API requests",
    )

    wipay_currency = fields.Selection([
        ('TTD', 'TTD'),
        ('JMD', 'JMD'),
        ('USD', 'USD'),
    ], string='WiPay Currency', required=True, default='USD')

    @api.onchange('wipay_currency')
    def _onchange_wipay_currency(self):
        """Auto-update the API URL when the currency is changed."""
        currency_url_map = {
            'TTD': 'https://tt.wipayfinancial.com/plugins/payments/request',
            'JMD': 'https://jm.wipayfinancial.com/plugins/payments/request',
            'USD': 'https://tt.wipayfinancial.com/plugins/payments/request',  # Defaulting USD to TT
        }

        self.wipay_api_url = currency_url_map.get(self.wipay_currency, '')



    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.code != 'wipay':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_wipay.payment_method_wipay').id
        
    def _should_show_payment_icon_wizard(self):
        self.ensure_one()
        return self.code == 'wipay' or super()._should_show_payment_icon_wizard()
        
    def _is_missing_required_fields(self):
        self.ensure_one()
        
        # For Wipay, we only require the merchant account ID and API key
        if self.code == 'wipay':
            return not (self.wipay_merchant_account_id and self.wipay_api_key and self.wipay_api_url)
        
        return super()._is_missing_required_fields()
        
    def _is_publishable_in_website(self, website=None):

        self.ensure_one()
        if self.code != 'wipay':
            return super()._is_publishable_in_website(website=website)

        # For Wipay, allow publishing when the provider is not disabled
        return self.state != 'disabled'
        
    def _compute_website_url(self):
        """ Override to set the right URL for Wipay providers """
        for provider in self:
            if provider.code == 'wipay':
                provider.website_url = '/shop/payment'
            else:
                super()._compute_website_url()
        
    @api.model
    def create(self, values):
        """ Override to force publish Wipay providers upon creation """
        res = super().create(values)
        if res.code == 'wipay' and res.state != 'disabled' and 'is_published' not in values:
            res.write({'is_published': True})
        return res
        
        
    def _get_payment_product_id(self):
        """ Override of payment to return the Wipay payment product. """
        self.ensure_one()
        if self.code != 'wipay':
            return super()._get_payment_product_id()
        return self.env['product.product'].search([('detailed_type', '=', 'service'), ('sale_ok', '=', True)], limit=1).id
        
    def _should_show_in_website_express_checkout(self):
        """ Override to enable express checkout for Wipay. """
        if self.code == 'wipay':
            return True
        return super()._should_show_in_website_express_checkout()
        
    def _is_available_for_country(self, country_code=None):

        if self.code == 'wipay':
            # Make Wipay available for all countries in test mode
            if self.state == 'test':
                return True
                

            available_countries = ['TT']  # Add other countries as needed
            if not country_code or country_code in available_countries:
                return True
            return False
        return super()._is_available_for_country(country_code)
        
    def _is_available_for_sale_order(self, sale_order):
        """ Override to make Wipay available for sale orders.
        
        :param record sale_order: The sale order
        :return: Whether the payment provider is available for the sale order
        :rtype: bool 
        """
        self.ensure_one()
        if self.code == 'wipay':
            # Available for all sale orders
            return True
        return super()._is_available_for_sale_order(sale_order)
        
    def _get_website_payment_form_data(self, partner_id, amount, currency_id, reference, payment_option_id, additional_context=None):

        res = super()._get_website_payment_form_data(
            partner_id, amount, currency_id, reference, payment_option_id, additional_context
        )
        if self.code != 'wipay':
            return res
            
        # Get the partner and currency records
        partner = self.env['res.partner'].browse(partner_id)
        currency = self.env['res.currency'].browse(currency_id)
        
        res.update({
            'provider_name': self.name,
            'reference': reference,
            'currency': currency.name,
            'amount': amount,
            'partner_email': partner.email,
        })
        return res
        
    def _get_default_payment_method_codes(self):
        """ Override of payment to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'wipay':
            return default_codes
        return ['wipay']
        
    def _compute_feature_support_fields(self):
        """ Override of payment to enable additional features. """
        super()._compute_feature_support_fields()
        if self.code != 'wipay':
            return
            
        # In Odoo 18, the field names might have changed
        # Use hasattr to check which fields exist and set them accordingly
        if hasattr(self, 'support_fees'):
            self.support_fees = True  # Support payment fees
        if hasattr(self, 'fees_active'):
            self.fees_active = True  # Support payment fees (new name)
        if hasattr(self, 'allow_express_checkout'):
            self.allow_express_checkout = True
        if hasattr(self, 'support_manual_capture'):
            self.support_manual_capture = False
        if hasattr(self, 'capture_manually'):
            self.capture_manually = False
        if hasattr(self, 'support_refund'):
            self.support_refund = 'partial'
        if hasattr(self, 'support_tokenization'):
            self.support_tokenization = False
        if hasattr(self, 'allow_tokenization'):
            self.allow_tokenization = False