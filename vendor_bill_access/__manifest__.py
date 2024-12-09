{
    'name': 'Vendor Bill Access',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom access rights for vendor bill upload',
    'description': """
        This module provides restricted access for users to only upload and manage vendor bills
        without access to other accounting features.
    """,
    'depends': ['base', 'account', 'account_edi'],  # Added account_edi
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/vendor_bill_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}