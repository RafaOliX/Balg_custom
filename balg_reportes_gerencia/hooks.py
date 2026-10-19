from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Crear las vistas SQL
    env['balg_reportes_gerencia.reporte_precio_promedio'].init()
    env['balg_reportes_gerencia.reporte_produccion_porcentaje'].init()
    # Sincronizar tarjetas
    env['dashboard.report']._sync_dashboard_cards()