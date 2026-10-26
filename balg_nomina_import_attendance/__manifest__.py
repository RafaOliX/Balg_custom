{
    'name': 'Importador de Marcajes RRHH',
    'version': '16.0.1.0.0',
    'author': 'BalgresIT',
    'summary': 'Permite a RRHH subir los Excel del reloj y generar asistencias.',
    'depends': ['hr', 'hr_work_entry'],
    'external_dependencies': {
        'python': ['pandas', 'xlrd', 'openpyxl'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
