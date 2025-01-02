{
    'name': 'Wipay Payment Provider',
    'version': '18.0.1.0',
    'category': 'Payment',
    'summary': 'Integrate Wipay payment processor with Odoo',
    'description': 'This module integrates Wipay payment processor with Odoo 18.',
    'author': 'Paxgenesis',
    'website': 'https://www.paxgenesis.com',
    'depends': ['payment'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_provider_data.xml',  # Add this line
        'views/payment_provider_views.xml',
        'views/payment_templates.xml',
    ],
    'installable': True,
    'application': True,
}