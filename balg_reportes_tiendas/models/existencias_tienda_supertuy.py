# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteExistenciasTiendaAdriatica(models.Model):
    _name = 'balg_reportes_tiendas.existencias_tienda_supertuy'
    _description = 'Existencias Tienda SuperTuy'
    _auto = False
    _rec_name = 'x_producto'

    id = fields.Integer(string="ID", readonly=True)
    x_product_id = fields.Integer(string="ID Producto", readonly=True)
    x_ubicacion = fields.Integer(string="Ubicación", readonly=True)
    x_categoria = fields.Char(string="Categoría", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_unidad_medida = fields.Char(string="Unidad de Medida", readonly=True)
    x_stock_actual_fisico = fields.Float(string="Stock Actual Físico", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sq.product_id) AS id,
                    sq.product_id AS x_product_id,
                    sq.location_id AS x_ubicacion,
                    pc.name::varchar AS x_categoria,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US', pt.name->>'es_ES', 'Sin Nombre')::varchar AS x_producto,
                    COALESCE(uom.name->>'es_VE', uom.name->>'en_US', uom.name->>'es_ES')::varchar AS x_unidad_medida,
                    SUM(sq.quantity)::numeric AS x_stock_actual_fisico
                FROM stock_quant sq 
                JOIN product_product pp ON sq.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pt.categ_id = pc.id
                LEFT JOIN uom_uom uom ON pt.uom_id = uom.id
                WHERE sq.company_id = 4 
                  AND sq.location_id = 258
                  AND pt.active = true
                  AND pp.active = true
                GROUP BY 
                    sq.product_id,
                    sq.location_id, 
                    pc.name,
                    pt.name,
                    uom.name
            )
        """)