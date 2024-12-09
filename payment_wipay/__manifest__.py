{
    'name': 'WiPay Payment Provider',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'Process payments through WiPay Caribbean payment gateway',
    'description': """Accept payments through WiPay's payment gateway.""",
    'author': 'Troy Roberts',
    'website': 'https://github.com/troymroberts/payment_wipay',
    'depends': [
        'payment',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_provider_views.xml',
        'views/payment_wipay_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_wipay/static/src/js/payment_form.js',
            'payment_wipay/static/src/scss/payment_form.scss',
        ],
    },
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'installable': True,
}