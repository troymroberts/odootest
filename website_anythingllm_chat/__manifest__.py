# -*- coding: utf-8 -*-
{
    'name': 'Odoo LLM Chat Integration',
    'version': '17.0.0.1',
    'summary': 'Integrate LLM with Odoo Chat',
    'category': 'Discuss',
    'depends': [
        'base',
        'mail',
        'web',
        'base_setup'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/llm_chat_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}