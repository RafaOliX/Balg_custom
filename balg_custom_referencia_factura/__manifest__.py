{
    'name': 'BALG- Custom Account Move Reason Editable',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Make reason field editable in draft state',
    'description': """
        Hace editable el campo reason en facturas rectificativas en estado borrador.
    """,
    'author': 'BalgresIT',
    'license': 'LGPL-3', 
    'depends': ['account', 'l10n_ve_account_sequence_number'],  # Dependencia del módulo que contiene la vista
    'data': [
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}