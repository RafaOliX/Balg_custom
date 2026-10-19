{
    'name': 'Hide Studio Button',
    'version': '1.0.3',
    'category': 'Hidden',
    'summary': 'Oculta el botón de Odoo Studio para usuarios específicos',
    'description': 'Permite ocultar Studio manteniendo el permiso de Ajustes',
    'author': 'Tu Nombre',
    'license': 'LGPL-3', 
    'depends': ['web'],
    'data': [
        'security/security.xml',
        # 'views/assets.xml',  # <-- Elimina esta línea
    ],
    'assets': {
        'web.assets_backend': [
            'hide_studio_button/static/src/js/studio_hide.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}