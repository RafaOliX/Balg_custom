{
    'name': 'Límite de Crédito en USD',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Límite de crédito en USD por compañía, sin conversión de moneda',
    'description': """
        Permite definir el límite de crédito de clientes en USD por compañía.
        Solo considera facturas y órdenes emitidas en USD (sin conversión),
        replicando el comportamiento del reporte de seguimiento de Odoo.
    """,
    'author': 'BALG',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}