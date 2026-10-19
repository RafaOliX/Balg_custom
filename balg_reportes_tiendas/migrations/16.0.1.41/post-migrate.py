from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Inicializar las vistas SQL de todos los reportes
    env['balg_reportes_tiendas.ventas_corporaccion_adriatica'].init()
    # Agregar aquí las nuevas vistas
    env['tiendas.dashboard.report']._sync_dashboard_cards()