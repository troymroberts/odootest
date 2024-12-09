# payment_wipay/tests/test_security.py

import time
from freezegun import freeze_time
from unittest.mock import patch

from odoo.tests import tagged
from odoo.exceptions import SecurityError
from .common import WiPayCommon
from ..models.security_utils import WiPaySecurityUtils

@tagged('post_install', '-at_install')
class WiPaySecurityTest(WiPayCommon):

    def setUp(self):
        super().setUp()
        self.security_utils = WiPaySecurityUtils()
        self.test_payload = {
            'amount': '100.00',
            'currency': 'USD',
            'reference': 'TEST123'
        }
        self.timestamp = str(int(time.time()))

    def test_signature_generation(self):
        """Test HMAC signature generation and verification."""
        # Generate signature
        signature = self.security_utils.generate_signature(
            self.wipay.wipay_api_key,
            self.test_payload,
            self.timestamp
        )
        
        # Verify valid signature
        self.assertTrue(
            self.security_utils.verify_signature(
                self.wipay.wipay_api_key,
                self.test_payload,
                self.timestamp,
                signature
            )
        )
        
        # Test invalid signature
        with self.assertRaises(SecurityError):
            self.security_utils.verify_signature(
                self.wipay.wipay_api_key,
                self.test_payload,
                self.timestamp,
                'invalid_signature'
            )

    @freeze_time("2024-11-29")
    def test_timestamp_validation(self):
        """Test timestamp freshness validation."""
        old_timestamp = str(int(time.time()) - 400)  # 400 seconds old
        
        signature = self.security_utils.generate_signature(
            self.wipay.wipay_api_key,
            self.test_payload,
            old_timestamp
        )
        
        with self.assertRaises(SecurityError):
            self.security_utils.verify_signature(
                self.wipay.wipay_api_key,
                self.test_payload,
                old_timestamp,
                signature,
                max_age=300  # 300 seconds max age
            )

    def test_card_data_encryption(self):
        """Test encryption of sensitive card data."""
        test_card_data = {
            'card_number': '4111111111111111',
            'cvv': '123',
            'expiry': '12/25'
        }
        
        encrypted_data = self.security_utils.encrypt_card_data(test_card_data)
        
        # Verify data is encrypted
        for value in encrypted_data.values():
            self.assertNotEqual(value, test_card_data.values())

    def test_response_sanitization(self):
        """Test sanitization of sensitive data in responses."""
        test_response = {
            'status': 'success',
            'card_number': '4111111111111111',
            'authorization': 'secret_auth_token',
            'amount': '100.00',
            'nested': {
                'cvv': '123',
                'api_key': 'secret_key'
            }
        }
        
        sanitized = self.security_utils.sanitize_response(test_response)
        
        self.assertEqual(sanitized['card_number'], '***')
        self.assertEqual(sanitized['authorization'], '***')
        self.assertEqual(sanitized['nested']['cvv'], '***')
        self.assertEqual(sanitized['nested']['api_key'], '***')
        self.assertEqual(sanitized['amount'], '100.00')

    @patch('odoo.http.request')
    def test_security_middleware(self, mock_request):
        """Test security middleware decorator."""
        from ..controllers.security_middleware import security_check
        
        # Mock request object
        mock_request.httprequest.remote_addr = '127.0.0.1'
        mock_request.httprequest.headers = {
            'X-Wipay-Timestamp': self.timestamp,
            'X-Wipay-Signature': 'valid_signature'
        }
        
        # Test decorator
        @security_check
        def test_method():
            return {'success': True}
            
        with patch.object(
            WiPaySecurityUtils,
            'verify_signature',
            return_value=True
        ):
            result = test_method()
            self.assertTrue(result['success'])

        # Test with invalid signature
        with patch.object(
            WiPaySecurityUtils,
            'verify_signature',
            return_value=False
        ):
            result = test_method()
            self.assertEqual(result['error'], 'Security check failed')