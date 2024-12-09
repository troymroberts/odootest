# payment_wipay/tests/test_wipay.py

import hashlib
from unittest.mock import patch
from freezegun import freeze_time

from werkzeug.exceptions import Forbidden

from odoo.tests import tagged
from odoo.tools import mute_logger
from odoo.exceptions import ValidationError

from .common import WiPayCommon

@tagged('post_install', '-at_install')
class WiPayTest(WiPayCommon):

    def test_compatible_providers(self):
        """Test the compatible providers for WiPay."""
        providers = self.env['payment.provider']._get_compatible_providers(
            self.company.id,
            self.partner.id,
            self.test_amount,
            currency_id=self.currency_usd.id,
        )
        self.assertIn(self.wipay, providers)

    def test_processing_values(self):
        """Test the processing values for a WiPay payment."""
        tx = self._create_transaction(flow='redirect')
        
        with mute_logger('odoo.addons.payment.models.payment_transaction'):
            processing_values = tx._get_processing_values()

        self.assertEqual(processing_values['amount'], self.test_amount)
        self.assertEqual(processing_values['currency_code'], self.currency.name)
        self.assertEqual(processing_values['reference'], self.reference)

    def test_validation_amount(self):
        """Test the validation amount for WiPay."""
        self.assertEqual(self.wipay._get_validation_amount(), 1.00)

    @freeze_time('2024-11-29')
    def test_fee_computation(self):
        """Test the fee computation for different scenarios."""
        tx = self._create_transaction(flow='redirect')
        
        # Test customer pays fee
        self.wipay.write({'wipay_fee_structure': 'customer_pay'})
        fee = tx._compute_fees(1000.00, 'USD', 'TT')
        self.assertEqual(fee, 35.25)  # 3.5% + $0.25 USD
        
        # Test merchant absorbs fee
        self.wipay.write({'wipay_fee_structure': 'merchant_absorb'})
        fee = tx._compute_fees(1000.00, 'USD', 'TT')
        self.assertEqual(fee, 35.25)  # Same calculation, different payer
        
        # Test split fee
        self.wipay.write({'wipay_fee_structure': 'split'})
        fee = tx._compute_fees(1000.00, 'USD', 'TT')
        self.assertEqual(fee, 35.25)  # Total fee same, will be split later

    def test_api_url_generation(self):
        """Test API URL generation for different countries and environments."""
        # Test sandbox URL
        self.wipay.write({'state': 'test'})
        self.assertEqual(
            self.wipay._wipay_get_api_url(),
            'https://tt.wipayfinancial.com/plugins/payments/request'
        )
        
        # Test production URLs for different countries
        self.wipay.write({'state': 'enabled'})
        
        # Trinidad and Tobago
        self.wipay.write({'wipay_country_code': 'TT'})
        self.assertEqual(
            self.wipay._wipay_get_api_url(),
            'https://tt.wipayfinancial.com/plugins/payments/request'
        )
        
        # Jamaica
        self.wipay.write({'wipay_country_code': 'JM'})
        self.assertEqual(
            self.wipay._wipay_get_api_url(),
            'https://jm.wipayfinancial.com/plugins/payments/request'
        )
        
        # Barbados
        self.wipay.write({'wipay_country_code': 'BB'})
        self.assertEqual(
            self.wipay._wipay_get_api_url(),
            'https://bb.wipayfinancial.com/plugins/payments/request'
        )

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_validation_success(self):
        """Test the validation of successful transaction data."""
        tx = self._create_transaction(flow='redirect')
        
        # Calculate proper hash
        hash_string = f"{self.notification_data['transaction_id']}{self.notification_data['total']}{self.wipay.wipay_api_key}"
        self.notification_data['hash'] = hashlib.md5(hash_string.encode()).hexdigest()
        
        with patch('odoo.addons.payment.models.payment_transaction.PaymentTransaction'
                  '._handle_notification_data') as handle_notification_data:
            handle_notification_data.return_value = True
            tx._process_notification_data(self.notification_data)
            self.assertEqual(tx.state, 'done')
            self.assertEqual(tx.provider_reference, self.notification_data['transaction_id'])

    @mute_logger('odoo.addons.payment.models.payment_transaction')
    def test_validation_error(self):
        """Test the validation of erroneous transaction data."""
        tx = self._create_transaction(flow='redirect')
        
        error_data = dict(self.notification_data, status='error')
        with self.assertRaises(ValidationError):
            tx._process_notification_data(error_data)

    def test_invalid_hash(self):
        """Test the validation of transaction with invalid hash."""
        tx = self._create_transaction(flow='redirect')
        
        invalid_data = dict(self.notification_data, hash='invalid_hash')
        with self.assertRaises(ValidationError), mute_logger('odoo.addons.payment.models.payment_transaction'):
            tx._process_notification_data(invalid_data)

    def test_missing_notification_data(self):
        """Test the validation of incomplete transaction data."""
        tx = self._create_transaction(flow='redirect')
        
        incomplete_data = {
            'status': 'success'  # Missing other required fields
        }
        with self.assertRaises(ValidationError), mute_logger('odoo.addons.payment.models.payment_transaction'):
            tx._process_notification_data(incomplete_data)

    def test_webhook_validation(self):
        """Test the webhook validation process."""
        tx = self._create_transaction(flow='redirect')
        
        # Calculate proper hash
        hash_string = f"{self.notification_data['transaction_id']}{self.notification_data['total']}{self.wipay.wipay_api_key}"
        self.notification_data['hash'] = hashlib.md5(hash_string.encode()).hexdigest()
        
        with patch('odoo.addons.payment.models.payment_transaction.PaymentTransaction'
                  '._handle_notification_data') as handle_notification_data:
            handle_notification_data.return_value = True
            
            # Test valid webhook
            response = self.env['payment.transaction']._handle_notification_data(
                'wipay',
                self.notification_data
            )
            self.assertTrue(response)
            
            # Test invalid hash
            invalid_data = dict(self.notification_data, hash='invalid')
            with self.assertRaises(ValidationError):
                self.env['payment.transaction']._handle_notification_data(
                    'wipay',
                    invalid_data
                )