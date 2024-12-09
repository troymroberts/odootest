# payment_wipay/tests/test_avs_tokenization.py

import json
from unittest.mock import patch
from freezegun import freeze_time
from datetime import datetime

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import WiPayCommon

@tagged('post_install', '-at_install')
class WiPayAVSTokenizationTest(WiPayCommon):

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        
        # Set up test AVS data
        self.avs_data = {
            'addr1': '123 Test St',
            'addr2': 'Apt 4B',
            'city': 'Test City',
            'state': 'TS',
            'zipcode': '12345',
            'country': 'TT',
            'phone': '+18681234567',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        # Enable AVS on provider
        self.wipay.write({
            'wipay_enable_avs': True,
            'wipay_avs_decline_level': 'partial'
        })
        
        # Set up test token data
        self.token_data = {
            'provider_id': self.wipay.id,
            'partner_id': self.partner.id,
            'token': 'test_token_123',
            'card_type': 'visa',
            'last4': '1111',
            'expiry': '12/25'
        }

    def test_avs_validation_full_match(self):
        """Test AVS validation with full address match."""
        self.wipay.write({'wipay_avs_decline_level': 'full'})
        
        # Test full match
        self.assertTrue(
            self.wipay._wipay_validate_avs_response('Y')  # Full match
        )
        
        # Test partial match (should fail with full validation)
        self.assertFalse(
            self.wipay._wipay_validate_avs_response('A')  # Partial match
        )

    def test_avs_validation_partial_match(self):
        """Test AVS validation with partial address match."""
        self.wipay.write({'wipay_avs_decline_level': 'partial'})
        
        # Test full match
        self.assertTrue(
            self.wipay._wipay_validate_avs_response('Y')  # Full match
        )
        
        # Test partial match
        self.assertTrue(
            self.wipay._wipay_validate_avs_response('A')  # Partial match
        )
        
        # Test no match
        self.assertFalse(
            self.wipay._wipay_validate_avs_response('N')  # No match
        )

    def test_avs_data_in_transaction(self):
        """Test AVS data inclusion in transaction processing."""
        tx = self._create_transaction(flow='direct')
        
        # Update partner with AVS data
        self.partner.write({
            'street': self.avs_data['addr1'],
            'street2': self.avs_data['addr2'],
            'city': self.avs_data['city'],
            'state_id': self.env['res.country.state'].create({
                'name': 'Test State',
                'code': 'TS',
                'country_id': self.env['res.country'].search(
                    [('code', '=', 'TT')], limit=1
                ).id
            }).id,
            'zip': self.avs_data['zipcode'],
            'phone': self.avs_data['phone'],
            'email': self.avs_data['email']
        })

        rendering_values = tx._get_specific_rendering_values({})
        
        # Verify AVS data in rendering values
        self.assertEqual(rendering_values['avs'], '1')
        self.assertEqual(rendering_values['addr1'], self.avs_data['addr1'])
        self.assertEqual(rendering_values['city'], self.avs_data['city'])
        self.assertEqual(rendering_values['zipcode'], self.avs_data['zipcode'])

    def test_token_creation(self):
        """Test payment token creation and validation."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        self.assertEqual(token.wipay_token, 'test_token_123')
        self.assertEqual(token.wipay_card_type, 'visa')
        self.assertEqual(token.wipay_last4, '1111')
        self.assertEqual(token.wipay_expiry, '12/25')
        self.assertTrue(token.verified)

    def test_token_invalid_data(self):
        """Test token creation with invalid data."""
        invalid_data = self.token_data.copy()
        del invalid_data['token']
        
        with self.assertRaises(ValidationError):
            self.env['payment.token'].wipay_create(invalid_data)

    @freeze_time('2024-11-29')
    def test_token_payment_processing(self):
        """Test payment processing using stored token."""
        # Create token
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Create transaction with token
        tx = self._create_transaction(flow='token', token=token)
        
        with patch('odoo.addons.payment.models.payment_transaction.PaymentTransaction'
                  '._send_payment_request') as mock_send:
            mock_send.return_value = None
            tx._send_payment_request()
            
            # Verify token data was used
            mock_send.assert_called_once()
            self.assertEqual(tx.token_id, token)

    def test_token_deactivation(self):
        """Test token deactivation process."""
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        with patch('odoo.addons.payment_wipay.models.payment_token.PaymentToken'
                  '._handle_deactivation_request') as mock_deactivate:
            token.action_deactivate()
            mock_deactivate.assert_called_once()

    def test_avs_decline_transaction(self):
        """Test transaction decline due to AVS failure."""
        tx = self._create_transaction(flow='direct')
        
        notification_data = {
            'status': 'success',
            'avs_response': 'N',  # No match
            'transaction_id': 'test_tx_123'
        }
        
        self.wipay.write({'wipay_avs_decline_level': 'partial'})
        
        with self.assertRaises(ValidationError):
            tx._process_notification_data(notification_data)
            self.assertEqual(tx.state, 'error')

    def test_recurring_payment_with_token(self):
        """Test recurring payment setup with tokenization."""
        # Enable recurring payments
        self.wipay.write({
            'wipay_tokenization_enabled': True,
            'wipay_recurring_enabled': True
        })
        
        # Create token
        token = self.env['payment.token'].wipay_create(self.token_data)
        
        # Create recurring payment
        recurring = self.env['payment.recurring.wipay'].create({
            'name': 'Test Recurring Payment',
            'partner_id': self.partner.id,
            'token_id': token.id,
            'amount': 100.00,
            'currency_id': self.currency_usd.id,
            'interval': 'monthly',
            'next_payment': datetime.now().date()
        })
        
        self.assertEqual(recurring.state, 'active')
        self.assertEqual(recurring.payment_count, 0)
        
        # Test payment processing
        with patch('odoo.addons.payment.models.payment_transaction.PaymentTransaction'
                  '._send_payment_request') as mock_send:
            mock_send.return_value = None
            recurring._process_recurring_payment()
            
            self.assertEqual(recurring.payment_count, 1)
            self.assertNotEqual(recurring.next_payment, datetime.now().date())