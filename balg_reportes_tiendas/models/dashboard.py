# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class TiendaDashboardReport(models.Model):
    _name = 'tiendas.dashboard.report'
    _description = 'Tarjeta de Reporte Tiendas'
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
        """
        cards_data = [
            {
                'xml_id': 'dashboard_report_ventas_corporaccion_adriatica',
                'name': 'Ventas Corporación Adriatica',
                'description': 'Ventas detallada',
                'icon': 'fa-building',
                'color': '#2980b9',
                'action_xml_id': 'action_reporte_ventas_corporaccion_adriatica',
                'sequence': 10,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias_tienda_adriatica',
                'name': 'Existencias Corporación Adriatica',
                'description': 'Stock físico actual',
                'icon': 'fa-cubes',
                'color': '#2980b9',
                'action_xml_id': 'action_reporte_existencias_tienda_adriatica',
                'sequence': 11,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_compras_corporaccion_adriatica',
                'name': 'Compras Corporación Adriática',
                'description': 'Compras de proveedores publicadas',
                'icon': 'fa-truck',
                'color': '#2980b9',
                'action_xml_id': 'action_reporte_compras_corporaccion_adriatica',
                'sequence': 12, 
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_ventas_supertuy',
                'name': 'Ventas SUPERTUY',
                'description': 'Ventas detallada',
                'icon': 'fa-building',
                'color': '#ff9900',
                'action_xml_id': 'action_reporte_ventas_supertuy',
                'sequence': 20,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias_tienda_supertuy',
                'name': 'Existencias SUPERTUY',
                'description': 'Stock físico actual',
                'icon': 'fa-cubes',
                'color': '#ff9900',
                'action_xml_id': 'action_reporte_existencias_tienda_supertuy',
                'sequence': 21,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_compras_supertuy',
                'name': 'Compras SUPERTUY',
                'description': 'Compras de proveedores publicadas',
                'icon': 'fa-truck',
                'color': '#ff9900',
                'action_xml_id': 'action_reporte_compras_supertuy',
                'sequence': 22, 
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_ventas_supergres',
                'name': 'Ventas SUPERGRES',
                'description': 'Ventas detallada',
                'icon': 'fa-building',
                'color': '#00f0ff',
                'action_xml_id': 'action_reporte_ventas_supergres',
                'sequence': 30,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_existencias_tienda_supergres',
                'name': 'Existencias SUPERGRES',
                'description': 'Stock físico actual',
                'icon': 'fa-cubes',
                'color': '#00f0ff',
                'action_xml_id': 'action_reporte_existencias_tienda_supergres',
                'sequence': 31,
                'active': True,
            },
            {
                'xml_id': 'dashboard_report_compras_supergres',
                'name': 'Compras SUPERGRES',
                'description': 'Compras de proveedores publicadas',
                'icon': 'fa-truck',
                'color': '#00f0ff',
                'action_xml_id': 'action_reporte_compras_supergres',
                'sequence': 32, 
                'active': True,
            },
        ]

        _logger.info("=== INICIANDO SINCRONIZACIÓN DE TARJETAS TIENDAS ===")

        for card_data in cards_data:
            try:
                action = self.env.ref(
                    f"balg_reportes_tiendas.{card_data['action_xml_id']}",
                    raise_if_not_found=False
                )
                if not action:
                    _logger.warning(f"Acción no encontrada: {card_data['action_xml_id']} – omitiendo tarjeta")
                    continue

                existing = self.env['ir.model.data'].search([
                    ('model', '=', self._name),
                    ('name', '=', card_data['xml_id']),
                    ('module', '=', 'balg_reportes_tiendas')
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
                        'module': 'balg_reportes_tiendas',
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