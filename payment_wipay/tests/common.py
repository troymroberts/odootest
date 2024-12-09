# payment_wipay/tests/common.py

from odoo.addons.payment.tests.common import PaymentCommon

class WiPayCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.wipay = cls._prepare_provider('wipay', update_values={
            'wipay_account_number': '1234567890',
            'wipay_api_key': 'test_key_123',
            'wipay_country_code': 'TT',
            'wipay_fee_structure': 'customer_pay',
        })
        
        cls.provider = cls.wipay
        cls.currency = cls.currency_usd

        # Test data
        cls.test_amount = 1000.00  # $1000 USD
        cls.notification_data = {
            'transaction_id': 'test_tx_123',
            'order_id': cls.reference,
            'total': str(cls.test_amount),
            'status': 'success',
            'message': '[1-R1]: Transaction is approved.',
            'card': 'XXXXXXXXXXXX1111',
            'date': '2024-11-29 10:00:00',
            'currency': 'USD',
            'hash': '123abc'  # Will be updated in tests
        }