# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReportePrecioPromedio(models.Model):
    _name = 'balg_reportes_gerencia.reporte_precio_promedio'
    _description = 'Reporte de Precio Promedio'
    _auto = False
    _rec_name = 'x_producto'

    id = fields.Integer(string="ID", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_cantidad_total = fields.Float(string="Cantidad Total", readonly=True)
    x_subtotal_total = fields.Float(string="Subtotal Total", readonly=True)
    x_precio_promedio = fields.Float(string="Precio Promedio", readonly=True, digits=(12, 2))

    def init(self):
        # 1. Eliminar la vista si ya existe
        tools.drop_view_if_exists(self.env.cr, self._table)
        # 2. Crear la vista con la nueva definición
        self.env.cr.execute("""
            CREATE VIEW balg_reportes_gerencia_reporte_precio_promedio AS (
                SELECT
                    MIN(aml.id) AS id,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US', pt.name->>'es_ES')::varchar AS x_producto,
                    SUM(aml.quantity)::numeric AS x_cantidad_total,
                    SUM(aml.price_subtotal)::numeric AS x_subtotal_total,
                    ROUND(SUM(aml.price_subtotal) / NULLIF(SUM(aml.quantity), 0), 2)::numeric AS x_precio_promedio
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN product_product pp ON aml.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE am.move_type IN ('out_invoice')
                  AND am.state = 'posted'
                  AND am.company_id = 2
                  AND aml.display_type = 'product'
                GROUP BY pt.name
            )
        """)