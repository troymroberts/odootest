# -*- coding: utf-8 -*-
{
    'name' : 'Website Chatter Enterprise',
    'version' : '17.0.0.1',
    'summary': 'Website Chatter',
    'category': 'Website',
    'depends': ['website'],
    'data': [
        'data/chatter_fields_data.xml',
        'security/ir.model.access.csv',
        'views/chatter_fields_views.xml',
        'views/chatter_fields_menu.xml',
    ],
    'installable': True,
    'application': True
}
