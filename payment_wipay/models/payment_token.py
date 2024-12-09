# payment_wipay/models/payment_token.py

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    wipay_token = fields.Char('WiPay Token Reference', readonly=True)
    wipay_card_type = fields.Selection([
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
    ], string='Card Type', readonly=True)
    wipay_last4 = fields.Char('Last 4 Digits', readonly=True)
    wipay_expiry = fields.Char('Expiry Date', readonly=True)

    @api.model
    def wipay_create(self, values):
        """Create a new token from WiPay response data."""
        # Validate required fields
        if not all(k in values for k in ['token', 'card_type', 'last4', 'expiry']):
            raise ValidationError(_("Incomplete token data received from WiPay"))

        return self.create({
            'provider_id': values['provider_id'],
            'partner_id': values['partner_id'],
            'wipay_token': values['token'],
            'wipay_card_type': values['card_type'],
            'wipay_last4': values['last4'],
            'wipay_expiry': values['expiry'],
            'verified': True,
        })

    def _handle_deactivation_request(self):
        """Deactivate token on WiPay's side."""
        for token in self:
            if token.provider_id.code != 'wipay':
                continue
            
            # Call WiPay API to deactivate token
            provider = token.provider_id
            try:
                # Implement actual API call here
                pass
            except Exception as e:
                raise ValidationError(_(
                    "Failed to deactivate token on WiPay: %s", str(e)
                ))

    def _get_payment_details(self):
        self.ensure_one()
        if self.provider_id.code != 'wipay':
            return super()._get_payment_details()
        return {
            'token': self.wipay_token,
            'card_type': self.wipay_card_type,
            'last4': self.wipay_last4,
            'expiry': self.wipay_expiry,
        }