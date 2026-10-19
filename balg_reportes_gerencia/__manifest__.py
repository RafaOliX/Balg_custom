{
    'name': "balg_reportes_gerenciales",
    'summary': "Dashboard de reportes gerenciales",
    'description': "Tarjetas para acceder a reportes de ventas, existencias y producción.",
    'author': "Balgres",
    'website': "https://www.balgres.com",
    'license': 'LGPL-3', 
    'category': 'Uncategorized',
    'version': '16.0.1.29',   # Incrementa para futuras actualizaciones
    'depends': ['base', 'web'],  # Ya no depende de bi_sql_editor (opcional)
    'data': [
        'security/security.xml',
        'views/views.xml',
        'views/cuentas_por_clientes_views.xml',
        'security/ir.model.access.csv',
        'views/reporte_existencias_formato_views.xml',
        'views/reporte_existencias_contable_views.xml',

    ],
    'post_init_hook': 'post_init_hook',
}