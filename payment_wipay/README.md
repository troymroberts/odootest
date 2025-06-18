# Wipay Payment Provider for Odoo 18

This module integrates Wipay payment processing with Odoo 18, allowing customers to make payments through Wipay's payment gateway.

## Features

- Secure payment processing
- Transaction status tracking
- Webhook support for payment notifications
- Support for refunds

## Configuration

After installation, you'll need to configure the Wipay payment provider:

1. Go to Invoicing/Accounting > Configuration > Payment Providers
2. Create a new provider or edit the Wipay provider
3. Set the following required fields:
   - Merchant Account ID: Your Wipay merchant account identifier
   - API Key: Your Wipay API key
   - Secret Key: Your Wipay secret key for signature verification
   - API URL: The base URL for API requests (defaults to https://tt.wipayfinancial.com/plugins/payments/request)

## Technical Information

This module implements:
- Payment provider form extension
- Redirect payment flow
- Callback handling
- Webhook support for transaction updates
- Transaction status management

## Support

For issues or questions, please contact your Odoo service provider or report issues via GitHub.

## License

This module is licensed under LGPL-3.