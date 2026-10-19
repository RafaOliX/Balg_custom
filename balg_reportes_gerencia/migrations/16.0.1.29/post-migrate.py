from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Crear las nuevas vistas (con la nueva convención)
    env['balg_reportes_gerencia.reporte_precio_promedio'].init()
    env['balg_reportes_gerencia.reporte_produccion_porcentaje'].init()
    # Sincronizar tarjetas (usando cards_data actualizada)
    env['dashboard.report']._sync_dashboard_cards()