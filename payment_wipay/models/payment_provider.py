# payment_wipay/models/payment_provider.py - Add to existing file

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # Add AVS fields
    wipay_enable_avs = fields.Boolean(
        string="Enable Address Verification",
        help="Enable Address Verification Service for credit card transactions",
        default=False
    )
    
    wipay_avs_decline_level = fields.Selection([
        ('none', 'Accept All Transactions'),
        ('partial', 'Require Partial Match'),
        ('full', 'Require Full Match')
    ], string="AVS Security Level",
       help="Determine how strict the address verification should be",
       default='partial',
       required_if_provider='wipay')

    def _wipay_validate_avs_response(self, avs_response):
        """Validate AVS response based on configured security level.
        
        Args:
            avs_response (str): AVS response code from WiPay
            
        Returns:
            bool: Whether the transaction should be accepted
        """
        self.ensure_one()
        
        if not self.wipay_enable_avs:
            return True
            
        # AVS Response codes from WiPay documentation
        full_match_codes = ['Y', 'X', 'D', 'F', 'M']  # Address and ZIP match
        partial_match_codes = ['A', 'B', 'P', 'W', 'Z']  # Partial matches
        
        if self.wipay_avs_decline_level == 'none':
            return True
        elif self.wipay_avs_decline_level == 'partial':
            return avs_response in (full_match_codes + partial_match_codes)
        else:  # full
            return avs_response in full_match_codes