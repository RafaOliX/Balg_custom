# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteExistencias(models.Model):
    _name = 'balg_reportes_gerencia.reporte_existencias'
    _description = 'Reporte de Existencias'
    _auto = False

    id = fields.Integer(string="ID", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_variante_referencia = fields.Char(string="Referencia", readonly=True)
    x_ubicacion = fields.Char(string="Ubicación", readonly=True)
    x_calidad = fields.Char(string="Calidad", readonly=True)
    x_tono = fields.Char(string="Tono", readonly=True)
    x_stock_actual_fisico = fields.Float(string="Stock Actual", readonly=True)
    x_stock_reservado = fields.Float(string="Stock Reservado", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US') AS x_producto,
                    pp.default_code AS x_variante_referencia,
                    sq.location_id AS x_ubicacion,
                    SUBSTRING(pp.default_code, 11, 1) AS x_calidad,
                    SUBSTRING(pp.default_code FROM '[A-Z]([0-9]+)$') AS x_tono,
                    SUM(sq.quantity) AS x_stock_actual_fisico,
                    SUM(sq.reserved_quantity) AS x_stock_reservado   
                FROM stock_quant sq
                JOIN product_product pp ON sq.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE pt.categ_id IN (SELECT id FROM product_category WHERE name = 'PRODUCTOS TERMINADOS-25')
                  AND sq.location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
                  AND sq.company_id = 2
                  AND sq.location_id = 130   
                GROUP BY pt.name, pp.default_code, sq.location_id
            )
        """)