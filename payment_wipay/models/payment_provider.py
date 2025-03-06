from odoo import api, fields, models

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wipay', 'WiPay')],
        ondelete={'wipay': 'set default'}
    )
    
    wipay_account_number = fields.Char(
        string="Account Number",
        help="The WiPay account number.",
        required_if_provider='wipay'
    )
    
    wipay_api_key = fields.Char(
        string="API Key",
        help="The WiPay API key.",
        required_if_provider='wipay'
    )
    
    wipay_country_code = fields.Selection([
        ('TT', 'Trinidad and Tobago'),
        ('JM', 'Jamaica'),
        ('BB', 'Barbados')
    ], string="Country", 
       required_if_provider='wipay')
       
    wipay_fee_structure = fields.Selection([
        ('customer_pay', 'Customer Pays Fee'),
        ('merchant_absorb', 'Merchant Absorbs Fee'),
        ('split', 'Split Fee')
    ], string="Fee Structure",
       default='customer_pay',
       required_if_provider='wipay')

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.code != 'wipay':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment.payment_method_card').id

    @api.model
    def _get_compatible_payment_methods(self, *args, **kwargs):
        """Override to filter available payment methods."""
        methods = super()._get_compatible_payment_methods(*args, **kwargs)
        if self.code != 'wipay':
            return methods
        return methods.filtered(lambda m: m.code in ['card'])