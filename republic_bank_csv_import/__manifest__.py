{
    "name": "Republic Bank Trinidad Bank CSV Import",
    "version": "17.0.0.1",
    "author": "Nikunj Dhameliya",
    "summary": "Bank statement import",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account", "account_accountant"],
    "data": [
        'security/ir.model.access.csv',
        'views/import_transaction_wizard_view.xml',
        'views/menu_item.xml',
    ],
    "auto_install": False,
    "installable": True
}
