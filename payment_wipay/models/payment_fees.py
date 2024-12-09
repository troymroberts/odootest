# payment_wipay/models/payment_fees.py

from odoo import models, fields, api
import math

class PaymentFeesWiPay(models.Model):
    _inherit = 'payment.transaction'

    def _compute_wipay_fees(self):
        """Compute WiPay transaction fees based on country and fee structure."""
        self.ensure_one()
        
        if self.provider_code != 'wipay':
            return 0.0

        amount = self.amount
        country = self.provider_id.wipay_country_code
        fee_structure = self.provider_id.wipay_fee_structure
        
        # Base rates by country
        rates = {
            'TT': {
                'percentage': 3.50,
                'fixed_usd': 0.25,
                'premium_percentage': 3.00
            },
            'JM': {
                'percentage': 4.20,
                'gct': 0.15,  # 15% General Consumption Tax
                'premium_percentage': 3.50
            },
            'BB': {
                'percentage': 3.80,
                'tax': 0.15,  # 15% Tax
                'premium_percentage': 3.80
            }
        }

        # Get country-specific rates
        country_rates = rates.get(country, rates['TT'])
        
        # Calculate base fee
        if self.provider_id.state != 'enabled':  # If in test mode, use default rate
            percentage = country_rates['percentage']
        else:
            percentage = country_rates.get('premium_percentage', country_rates['percentage'])

        fee = (amount * percentage) / 100

        # Add fixed USD fee for TT
        if country == 'TT' and self.currency_id.name in ['USD', 'TTD']:
            if self.currency_id.name == 'TTD':
                fee += country_rates['fixed_usd'] * 6.80  # Convert USD to TTD
            else:
                fee += country_rates['fixed_usd']

        # Add tax/GCT for JM and BB
        if country in ['JM', 'BB']:
            fee = fee * (1 + country_rates.get('tax', country_rates.get('gct', 0)))

        # Apply fee structure
        if fee_structure == 'merchant_absorb':
            return 0.0  # Merchant absorbs fee, customer pays none
        elif fee_structure == 'split':
            return fee / 2  # Split fee between merchant and customer
        else:  # customer_pay
            return fee

    def _compute_fees(self):
        """Override to add WiPay fee computation."""
        res = super()._compute_fees()
        if self.provider_code == 'wipay':
            self.fees = self._compute_wipay_fees()
        return res