# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteVentasCorporacionAdriatica(models.Model):
    _name = 'balg_reportes_tiendas.ventas_supertuy'
    _description = 'Ventas Corporación SuperTuy'
    _auto = False
    _rec_name = 'x_cliente'

    id = fields.Integer(string="ID", readonly=True)
    x_compania = fields.Char(string="Compañía", readonly=True)
    x_company_id = fields.Integer(string="ID Compañía", readonly=True)
    x_cliente = fields.Char(string="Cliente", readonly=True)
    x_estado = fields.Char(string="Estado", readonly=True)
    x_ciudad = fields.Char(string="Ciudad", readonly=True)
    x_fecha_factura = fields.Date(string="Fecha Factura", readonly=True)
    x_numero_factura = fields.Char(string="Número Factura", readonly=True)
    x_producto = fields.Char(string="Producto", readonly=True)
    x_variante_referencia = fields.Char(string="Referencia", readonly=True)
    x_unidad_medida = fields.Char(string="Unidad de Medida", readonly=True)
    x_categoria = fields.Char(string="Categoría", readonly=True)
    x_cantidad_facturada = fields.Float(string="Cantidad", readonly=True)
    x_subtotal = fields.Float(string="Subtotal", readonly=True)
    x_subtotal_us = fields.Float(string="Subtotal US$", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    aml.id AS id,
                    rc.name::varchar AS x_compania,
                    aml.company_id AS x_company_id,
                    p.name::varchar AS x_cliente,
                    rcs.name::varchar AS x_estado,
                    p.city::varchar AS x_ciudad,
                    am.invoice_date AS x_fecha_factura,
                    am.invoice_number_next::varchar AS x_numero_factura,
                    COALESCE(pt.name->>'es_VE', pt.name->>'en_US', pt.name->>'es_ES')::varchar AS x_producto,
                    pp.default_code::varchar AS x_variante_referencia,
                    COALESCE(uom.name->>'es_VE', uom.name->>'en_US', uom.name->>'es_ES')::varchar AS x_unidad_medida,
                    pc.name AS x_categoria,
                    aml.quantity::numeric AS x_cantidad_facturada,
                    aml.price_subtotal::numeric AS x_subtotal,
                    aml.price_subtotal_rate::numeric AS x_subtotal_us
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN res_company rc ON am.company_id = rc.id
                JOIN res_partner p ON am.partner_id = p.id
                LEFT JOIN res_country_state rcs ON p.state_id = rcs.id
                LEFT JOIN crm_team ct ON am.team_id = ct.id
                JOIN product_product pp ON aml.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pt.categ_id = pc.id
                LEFT JOIN uom_uom uom ON aml.product_uom_id = uom.id
                WHERE am.move_type IN ('out_invoice')
                  AND am.state = 'posted'
                  AND am.company_id = 4
                  AND aml.display_type = 'product'
            )
        """)