from odoo.tests.common import TransactionCase

class TestWipayPayment(TransactionCase):
    def setUp(self):
        super(TestWipayPayment, self).setUp()
        self.wipay_provider = self.env['payment.provider'].create({
            'name': 'Wipay',
            'code': 'wipay',
            'wipay_api_key': 'test_api_key',
            'wipay_account_number': '1234567890',
            'wipay_environment': 'sandbox',
        })

    def test_wipay_provider_creation(self):
        self.assertEqual(self.wipay_provider.code, 'wipay')
        self.assertEqual(self.wipay_provider.wipay_api_key, 'test_api_key')
        self.assertEqual(self.wipay_provider.wipay_account_number, '1234567890')
        self.assertEqual(self.wipay_provider.wipay_environment, 'sandbox')

    def test_wipay_fee_calculation(self):
        fee = self.wipay_provider._compute_fee(100, 'USD')
        self.assertEqual(fee, 100 * 0.038 + 0.25)

    def test_wipay_api_request(self):
        with self.assertRaises(ValidationError):
            self.wipay_provider._wipay_make_request('https://invalid.url', {})