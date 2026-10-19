{
    'name': 'Custom Invoice Dashboard',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Agrega Importe Adeudado en Facturacion de los provedores',
    'description': """
        This module adds the 'Amount Due' (amount_residual) and 
        'Tax Due' (amount_residual_signed_rate) columns to the bill dashboard tree view.
    """,
    'author': 'BalgresIT',
    'depends': ['account', 'l10n_ve_currency_rate'],
    'license': 'LGPL-3', # Dependencias necesarias
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}