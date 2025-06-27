# -*- coding: utf-8 -*-
{
    'name': 'Wipay Payment Acquirer',
    'version': '1.2',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 380,
    'summary': 'Payment Acquirer: Wipay Implementation',
    'description': """Wipay Payment Acquirer""",
    'depends': ['payment', 'website_payment', 'website', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_wipay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',

    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_frontend': [
            '/payment_wipay/static/src/js/payment_form.js',
            '/payment_wipay/static/src/xml/template.xml',
        ],
    },
    'author': 'PaxGenesis',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'website': 'https://www.paxgenesis.com',
}
