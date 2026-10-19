from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Inicializar las vistas SQL de todos los reportes
    env['balg_reportes_tiendas.ventas_corporaccion_adriatica'].init()
    env['balg_reportes_tiendas.existencias_tienda_adriatica'].init()
    env['balg_reportes_tiendas.ventas_supertuy'].init()
    env['balg_reportes_tiendas.existencias_tienda_supertuy'].init()
    env['balg_reportes_tiendas.ventas_supergres'].init()
    env['balg_reportes_tiendas.existencias_tienda_supergres'].init()
    # Sincronizar tarjetas
    env['tiendas.dashboard.report']._sync_dashboard_cards()