{
    'name': 'Balg - Retención IVA - Formato Nuevo Ajustado',
    'version': '16.0.1.0.0',
    'author': 'Tu nombre',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte alternativo de retención de IVA con texto ajustado',
    'depends': ['l10n_ve_iva_retention'],
    'data': [
        'report/report_iva_new.xml',
        'views/ir_action_report.xml',
        'views/retention_iva_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}