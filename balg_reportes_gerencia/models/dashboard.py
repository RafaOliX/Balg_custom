# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class DashboardReport(models.Model):
    _name = 'dashboard.report'
    _description = 'Tarjeta de Reporte Gerencial'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    icon = fields.Char(string='Icono', default='fa-file-text-o')
    color = fields.Char(string='Color', default='#3498db')
    action_id = fields.Many2one('ir.actions.act_window', string='Acción', required=True)
    sequence = fields.Integer(string='Orden', default=10)
    active = fields.Boolean(string='Activo', default=True)

    def action_open_report(self):
        self.ensure_one()
        if self.action_id:
            return self.action_id.read()[0]
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _sync_dashboard_cards(self):
        """
        Sincroniza las tarjetas definidas en cards_data.
        - Crea/actualiza tarjetas según la lista.
        - NO elimina tarjetas existentes (permite personalización).
        - Para eliminar una tarjeta, simplemente quítala de la lista y ejecuta
          la sincronización; luego bórrala manualmente si quieres.
        """
        cards_data = [
            {
                'xml_id': 'dashboard_report_precio_promedio',
                'name': 'Precio Promedio',
                'description': 'Precio promedio ponderado por producto',
                'icon': 'fa-money',
                'color': '#f39c12',
                'action_xml_id': 'action_reporte_precio_promedio',
                'sequence': 50,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_produccion_porcentaje',
                'name': 'Porcentaje de Producción',
                'description': 'Distribución de calidad en producción',
                'icon': 'fa-pie-chart',
                'color': '#2ecc71',
                'action_xml_id': 'action_reporte_produccion_porcentaje',
                'sequence': 30,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_ventas_cliente',
                'name': 'Ventas por Cliente',
                'description': 'Ventas facturadas por cliente',
                'icon': 'fa-users',
                'color': '#3498db',
                'action_xml_id': 'action_reporte_ventas_cliente',
                'sequence': 15,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias',
                'name': 'Existencias',
                'description': 'Stock actual en almacén de despacho',
                'icon': 'fa-cubes',
                'color': '#27ae60',
                'action_xml_id': 'action_reporte_existencias',
                'sequence': 20,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias_contable',
                'name': 'Existencias Contable',
                'description': 'Stock actual en almacén contable',
                'icon': 'fa-book',
                'color': '#8e44ad',   # púrpura para distinguir
                'action_xml_id': 'action_reporte_existencias_contable',
                'sequence': 23,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias_formato',
                'name': 'Existencias por Formato',
                'description': 'Stock actual agrupado por formato',
                'icon': 'fa-th-large',   
                'color': '#2c3e50',
                'action_xml_id': 'action_reporte_existencias_formato',
                'sequence': 21,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_ventas_formato',
                'name': 'Ventas por Formato',
                'description': 'Ventas agrupadas por formato de producto',
                'icon': 'fa-table',
                'color': '#e67e22',
                'action_xml_id': 'action_reporte_ventas_formato',
                'sequence': 16,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_ventas_serie',
                'name': 'Ventas por Serie',
                'description': 'Ventas agrupadas por serie de producto',
                'icon': 'fa-tags',
                'color': '#8e44ad',
                'action_xml_id': 'action_reporte_ventas_serie',
                'sequence': 17,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_cuentas_por_clientes',
                'name': 'Cuentas por Clientes',
                'description': 'Cuentas por cobrar de clientes',
                'icon': 'fa-address-book',          # o 'fa-handshake-o'
                'color': '#e74c3c',                 # rojo para cuentas por cobrar
                'action_xml_id': 'action_reporte_cuentas_por_clientes',
                'sequence': 25,
                'active': True,
            },
            # ... más tarjetas según necesites
        ]

        _logger.info("=== INICIANDO SINCRONIZACIÓN DE TARJETAS ===")

        for card_data in cards_data:
            try:
                # Obtener la acción usando el XML ID completo
                action = self.env.ref(
                    f"balg_reportes_gerencia.{card_data['action_xml_id']}",
                    raise_if_not_found=False
                )
                if not action:
                    _logger.warning(f"Acción no encontrada: {card_data['action_xml_id']} – omitiendo tarjeta")
                    continue

                # Buscar si la tarjeta ya existe (por su xml_id)
                existing = self.env['ir.model.data'].search([
                    ('model', '=', self._name),
                    ('name', '=', card_data['xml_id']),
                    ('module', '=', 'balg_reportes_gerencia')
                ])

                vals = {
                    'name': card_data['name'],
                    'description': card_data['description'],
                    'icon': card_data['icon'],
                    'color': card_data['color'],
                    'action_id': action.id,
                    'sequence': card_data['sequence'],
                    'active': card_data.get('active', True),
                }

                if existing:
                    record = self.browse(existing.res_id)
                    if record:
                        record.write(vals)
                        _logger.info(f"Tarjeta actualizada: {card_data['name']}")
                else:
                    record = self.create(vals)
                    self.env['ir.model.data'].create({
                        'module': 'balg_reportes_gerencia',
                        'name': card_data['xml_id'],
                        'model': self._name,
                        'res_id': record.id,
                        'noupdate': True,
                    })
                    _logger.info(f"Tarjeta creada: {card_data['name']}")
            except Exception as e:
                _logger.error(f"Error al procesar tarjeta {card_data.get('name')}: {e}")

        _logger.info("=== SINCRONIZACIÓN FINALIZADA ===")
        return True