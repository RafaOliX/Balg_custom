# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteProduccionPorcentaje(models.Model):
    _name = 'balg_reportes_gerencia.reporte_produccion_porcentaje'
    _description = 'Reporte de Porcentaje de Producción'
    _auto = False

    id = fields.Integer(string="ID", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_fecha_movimiento = fields.Date(string="Fecha Movimiento", readonly=True)
    x_turno = fields.Char(string="Turno", readonly=True)
    x_stock_actual_fisico = fields.Float(string="Cantidad Total", readonly=True)
    x_total_a = fields.Float(string="Total A", readonly=True)
    x_total_b = fields.Float(string="Total B", readonly=True)
    x_total_c = fields.Float(string="Total C", readonly=True)
    x_total_d = fields.Float(string="Total D", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)  # ← Elimina la vista si existe
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW balg_reportes_gerencia_reporte_produccion_porcentaje AS (

                SELECT 
                    ROW_NUMBER() OVER () AS id, 
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US') AS x_producto, 
                    sp.scheduled_date::date AS x_fecha_movimiento, 
                    sp.origin x_turno, 
                    
                    -- Cantidades Totales
                    SUM(sm.quantity_done) AS x_stock_actual_fisico, 
                    SUM(CASE WHEN SUBSTRING(pp.default_code, 11, 1) = 'A' THEN sm.quantity_done ELSE 0 END) AS x_total_a, 
                    SUM(CASE WHEN SUBSTRING(pp.default_code, 11, 1) = 'B' THEN sm.quantity_done ELSE 0 END) AS x_total_b, 
                    SUM(CASE WHEN SUBSTRING(pp.default_code, 11, 1) = 'C' THEN sm.quantity_done ELSE 0 END) AS x_total_c, 
                    SUM(CASE WHEN SUBSTRING(pp.default_code, 11, 1) = 'D' THEN sm.quantity_done ELSE 0 END) AS x_total_d
                
                    -- ELIMINA LAS COLUMNAS x_por_a, x_por_b, etc. DE AQUÍ
                
                FROM stock_move sm 
                JOIN stock_picking sp ON sm.picking_id = sp.id 
                JOIN product_product pp ON sm.product_id = pp.id 
                JOIN product_template pt ON pp.product_tmpl_id = pt.id 
                WHERE sm.state = 'done' 
                  AND pt.categ_id IN (SELECT id FROM product_category WHERE name = 'PRODUCTOS TERMINADOS-25') 
                  AND sm.company_id = 2 
                  AND sm.location_dest_id = 136 
                GROUP BY pt.id, sp.origin, pt.name, sp.scheduled_date::date
            )
        """)