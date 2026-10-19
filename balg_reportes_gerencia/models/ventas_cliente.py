# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteVentasPorCliente(models.Model):
    _name = 'balg_reportes_gerencia.reporte_ventas_cliente'
    _description = 'Reporte de Ventas por Cliente'
    _auto = False

    id = fields.Integer(string="ID", readonly=True)
    x_cliente = fields.Char(string="Cliente", readonly=True)
    x_estado = fields.Char(string="Estado", readonly=True)
    x_ciudad = fields.Char(string="Ciudad", readonly=True)
    x_equipo_ventas = fields.Char(string="Equipo Ventas", readonly=True)
    x_fecha_factura = fields.Date(string="Fecha Factura", readonly=True)
    x_numero_factura = fields.Char(string="Número Factura", readonly=True)
    x_n_f = fields.Char(string="N/F", readonly=True)        # <--- Nuevo campo
    x_producto = fields.Char(string="Producto", readonly=True)
    x_variante_referencia = fields.Char(string="Referencia", readonly=True)
    x_calidad = fields.Char(string="Calidad", readonly=True)
    x_unidad_medida = fields.Char(string="Unidad", readonly=True)
    x_cantidad_facturada = fields.Float(string="Cantidad", readonly=True)
    x_subtotal = fields.Float(string="Subtotal", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    aml.id AS id,
                    p.name::varchar AS x_cliente,
                    rcs.name::varchar AS x_estado,
                    p.city::varchar AS x_ciudad,
                    COALESCE(ct.name->>'es_VE', ct.name::text)::varchar AS x_equipo_ventas,
                    am.invoice_date AS x_fecha_factura,
                    am.invoice_number_next::varchar AS x_numero_factura,
                    CASE 
                        WHEN am.invoice_number_control::varchar = '1' THEN 'F' 
                        ELSE 'N' 
                    END AS x_n_f,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US', pt.name->>'es_ES')::varchar AS x_producto,
                    pp.default_code::varchar AS x_variante_referencia,
                    CASE 
                        WHEN SUBSTRING(pp.default_code, 11, 1) IN ('A', 'B', 'C', 'D') 
                        THEN SUBSTRING(pp.default_code, 11, 1)::varchar 
                        ELSE 'NA' 
                    END AS x_calidad,
                    COALESCE(uom.name->>'es_VE', uom.name->>'en_US', uom.name->>'es_ES')::varchar AS x_unidad_medida,
                    aml.quantity::numeric AS x_cantidad_facturada,
                    aml.price_subtotal::numeric AS x_subtotal
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN res_partner p ON am.partner_id = p.id
                LEFT JOIN res_country_state rcs ON p.state_id = rcs.id
                LEFT JOIN crm_team ct ON am.team_id = ct.id
                JOIN product_product pp ON aml.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN uom_uom uom ON aml.product_uom_id = uom.id
                WHERE am.move_type IN ('out_invoice')
                  AND am.state = 'posted'
                  AND am.company_id = 2
                  AND aml.display_type = 'product'
            )
        """)