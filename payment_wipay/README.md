# WiPay Payment Provider for Odoo 17.0

## Overview
This module integrates WiPay's payment gateway with Odoo, enabling credit/debit card payments for businesses in the Caribbean region. It supports multiple currencies, configurable fee structures, and includes advanced features like AVS (Address Verification Service) and card tokenization.

## Features
- Credit/debit card processing
- Multiple currency support (TTD, USD, JMD, BBD)
- Configurable fee structures
- AVS (Address Verification Service)
- Card tokenization
- Comprehensive security features
- Test/Sandbox environment support
- Detailed transaction reporting

## Installation

### Prerequisites
- Odoo 17.0
- A verified WiPay Business Account
- WiPay API credentials

### Steps
1. Copy the `payment_wipay` module to your Odoo addons directory
2. Update your addons list: `./odoo-bin -u payment_wipay -d your_database`
3. Install the module through Odoo's Apps menu

## Configuration

### Initial Setup
1. Navigate to `Invoicing/Accounting → Configuration → Payment Providers`
2. Create or edit the WiPay payment provider
3. Configure the following required settings:
   - WiPay Account Number
   - API Key
   - Country Code
   - Fee Structure

### Fee Structures
Configure how transaction fees are handled:
- Customer Pays Fee
- Merchant Absorbs Fee
- Split Fee

### AVS Configuration
Enable and configure Address Verification Service:
1. Enable AVS in provider settings
2. Set AVS security level:
   - None (accept all transactions)
   - Partial Match Required
   - Full Match Required

### Testing
Use test card numbers provided by WiPay:
```
Visa: 4111111111111111
Mastercard: 5555555555554444
```

Set provider to 'Test Mode' for sandbox transactions.

## Usage

### Basic Implementation
```python
# Create payment transaction
tx_values = {
    'amount': 100.00,
    'currency_id': currency_id,
    'partner_id': partner_id,
    'provider_id': wipay_provider_id,
}
transaction = env['payment.transaction'].create(tx_values)
```

### Handling Responses
```python
# Example response handling
@http.route(['/payment/wipay/return'], type='http', auth='public')
def wipay_return(self, **post):
    # Validate the response
    tx = request.env['payment.transaction'].sudo()._handle_feedback_data(
        'wipay', post
    )
    return tx._get_processing_values()
```

## Security Features
- Request signing with HMAC
- Timestamp validation
- IP validation
- Rate limiting
- Data encryption
- XSS prevention
- Response sanitization

## Webhook Integration
Configure webhook URL in your WiPay dashboard:
```
https://your-domain.com/payment/wipay/webhook
```

## Error Handling
The module includes comprehensive error handling:
```python
try:
    # Process payment
    response = tx._send_payment_request()
except ValidationError as e:
    _logger.error("Payment validation error: %s", str(e))
except Exception as e:
    _logger.error("Payment processing error: %s", str(e))
```

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Support
For support:
1. Check the documentation
2. Contact WiPay support for gateway-specific issues
3. Submit issues on the repository for module-specific problems

## Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
This module is licensed under LGPL-3...