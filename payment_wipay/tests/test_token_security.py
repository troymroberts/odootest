# payment_wipay/tests/test_token_security.py

import jwt
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests import tagged
from odoo.exceptions import SecurityError
from .common import WiPayCommon
from ..models.security_utils import WiPaySecurityUtils

@tagged('post_install', '-at_install')
class WiPayTokenSecurityTest(WiPayCommon):

    def setUp(self):
        super().setUp()
        self.token_data = {
            'provider_id': self.wipay.id,
            'partner_id': self.partner.id,
            'token': 'test_token_123',
            'card_type': 'visa',
            'last4': '1111',
            'expiry': '12/25'
        }

    def test_token_encryption(self):
        """Test that token data is properly encrypted."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Verify token is encrypted in database
        self.assertNotEqual(token.wipay_token, 'test_token_123')
        
        # Verify token can be decrypted
        decrypted_token = self.env['payment.token']._decrypt_token(token.wipay_token)
        self.assertEqual(decrypted_token, 'test_token_123')

    def test_token_expiration(self):
        """Test token expiration handling."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Set token as expired
        token.write({
            'wipay_expiry': (datetime.now() - timedelta(days=1)).strftime('%m/%y')
        })
        
        with self.assertRaises(ValidationError):
            token._validate_token()

    def test_token_usage_tracking(self):
        """Test token usage tracking and limits."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Simulate multiple token uses
        for _ in range(5):
            token._track_token_usage()
            
        # Verify usage count
        self.assertEqual(token.usage_count, 5)
        
        # Test usage limits
        token.write({'usage_limit': 3})
        with self.assertRaises(ValidationError):
            token._validate_token()

    def test_token_ip_restriction(self):
        """Test token IP address restrictions."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Add IP restriction
        token.write({'allowed_ips': '192.168.1.1,192.168.1.2'})
        
        # Test valid IP
        self.assertTrue(token._validate_ip('192.168.1.1'))
        
        # Test invalid IP
        self.assertFalse(token._validate_ip('192.168.1.3'))

    def test_token_device_binding(self):
        """Test token device binding security."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Bind token to device
        device_id = 'test_device_123'
        token._bind_to_device(device_id)
        
        # Test valid device
        self.assertTrue(token._validate_device(device_id))
        
        # Test invalid device
        self.assertFalse(token._validate_device('other_device'))

    def test_token_audit_trail(self):
        """Test token usage audit trail."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Create audit entry
        token._log_token_usage({
            'ip': '192.168.1.1',
            'device_id': 'test_device',
            'amount': 100.00,
            'currency': 'USD'
        })
        
        # Verify audit trail
        audit_entries = self.env['payment.token.audit'].search([
            ('token_id', '=', token.id)
        ])
        self.assertEqual(len(audit_entries), 1)
        self.assertEqual(audit_entries.ip_address, '192.168.1.1')

    def test_token_breach_detection(self):
        """Test token breach detection system."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Simulate suspicious activities
        suspicious_activities = [
            {'ip': '192.168.1.1', 'amount': 1000.00},
            {'ip': '192.168.1.2', 'amount': 2000.00},
            {'ip': '192.168.1.3', 'amount': 3000.00}
        ]
        
        for activity in suspicious_activities:
            token._log_token_usage(activity)
            
        # Test breach detection
        self.assertTrue(token._detect_suspicious_activity())

    def test_token_security_downgrade(self):
        """Test token security level downgrade prevention."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Set high security level
        token.write({'security_level': 'high'})
        
        # Attempt to downgrade security
        with self.assertRaises(SecurityError):
            token.write({'security_level': 'low'})