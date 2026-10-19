# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteExistenciasContable(models.Model):
    _name = 'balg_reportes_gerencia.reporte_existencias_contable'
    _description = 'Reporte de Existencias Contable'
    _auto = False
    _rec_name = 'x_producto'

    id = fields.Integer(string="ID", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_variante_referencia = fields.Char(string="Referencia", readonly=True)
    x_ubicacion = fields.Char(string="Ubicación", readonly=True)   # nombre de ubicación
    x_calidad = fields.Char(string="Calidad", readonly=True)
    x_tono = fields.Char(string="Tono", readonly=True)
    x_stock_actual_fisico = fields.Float(string="Stock Actual", readonly=True)
    x_stock_reservado = fields.Float(string="Stock Reservado", readonly=True)
    x_formato = fields.Char(string="Formato", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US') AS x_producto,
                    pp.default_code AS x_variante_referencia,
                    sl.name::varchar AS x_ubicacion,
                    SUBSTRING(pp.default_code, 11, 1) AS x_calidad,
                    SUBSTRING(pp.default_code FROM '[A-Z]([0-9]+)$') AS x_tono,
                    SUM(sq.quantity) AS x_stock_actual_fisico,
                    SUM(sq.reserved_quantity) AS x_stock_reservado,
                    COALESCE(pf.name::varchar, 'SIN FORMATO') AS x_formato
                FROM stock_quant sq
                JOIN product_product pp ON sq.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN stock_location sl ON sq.location_id = sl.id
                LEFT JOIN product_format pf ON pt.product_format_id = pf.id
                WHERE pt.categ_id IN (SELECT id FROM product_category WHERE name = 'PRODUCTOS TERMINADOS-25')
                  AND sq.location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
                  AND sq.company_id = 2
                  AND sq.location_id = 166
                GROUP BY pf.name, pt.name, pp.default_code, sl.name
                ORDER BY pt.name, pp.default_code ASC
            )
        """)