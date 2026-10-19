from odoo import fields, models, tools

class SalePriceHistoryBalg(models.Model):
    _name = 'sale.price.history.balg'
    _description = 'Sale Price History (Balg)'
    _auto = False
    _order = 'sale_order_date desc'

    name = fields.Char(string="Línea de factura")
    partner_id = fields.Many2one("res.partner", string="Cliente")
    user_id = fields.Many2one("res.users", string="Vendedor")
    product_id = fields.Many2one("product.product", string="Producto")
    sale_order_date = fields.Datetime(string="Fecha de orden")
    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom', string="Unidad de Medida")
    currency_id = fields.Many2one("res.currency", string="Moneda")
    currency_id2 = fields.Many2one("res.currency", string="Moneda secundaria")
    unit_price = fields.Monetary(string="Precio", currency_field='currency_id')
    price_unit_rate = fields.Monetary(string='Precio al cambio', currency_field='currency_id2')
    total_price = fields.Monetary(string="Total", currency_field='currency_id')
    total_price_rate = fields.Monetary(string='Total al cambio', currency_field='currency_id2')
    price_subtotal = fields.Monetary(string="Subtotal", currency_field='currency_id')
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    invoice_number_next = fields.Char(string='Nro de factura')
    invoice_number_control = fields.Char(string='Nro de control')
    team_name = fields.Char(string="Equipo de Venta")          # desde el pedido
    amount_residual = fields.Monetary(string="Monto residual", currency_field='currency_id')
    amount_total = fields.Monetary(string="Total factura", currency_field='currency_id')
    invoice_date = fields.Date(string="Fecha de factura")
    invoice_state = fields.Char(string="Estado")

    def _select(self):
        return """
            row_number() over()                                                      AS id,
            aml.name                                                                 AS name,
            aml.quantity                                                             AS product_uom_qty,
            aml.price_unit                                                           AS unit_price,
            aml.price_unit_rate                                                      AS price_unit_rate,
            aml.price_subtotal                                                       AS total_price,
            aml.price_subtotal_rate                                                  AS total_price_rate,
            aml.price_subtotal                                                       AS price_subtotal,
            aml.product_uom_id                                                       AS product_uom,
            aml.product_id                                                           AS product_id,
            am.partner_id                                                            AS partner_id,
            aml.currency_id                                                          AS currency_id,
            aml.currency_id2                                                         AS currency_id2,
            am.invoice_user_id                                                       AS user_id,
            so.date_order                                                            AS sale_order_date,
            am.company_id                                                            AS company_id,
            COALESCE(
    team_factura.name->>'es_VE',
    team.name->>'es_VE',
    team_factura.name->>'en_US',
    team.name->>'en_US',
    ''
) AS team_name,
            am.name                                                                  AS invoice_number_next,
            am.ref                                                                   AS invoice_number_control,
            am.amount_residual                                                       AS amount_residual,
            am.amount_total                                                          AS amount_total,
            am.invoice_date                                                          AS invoice_date,
            am.state                                                                 AS invoice_state
        """

    def _from(self):
        return """
            account_move_line AS aml
                INNER JOIN account_move AS am
                    ON aml.move_id = am.id
                LEFT JOIN sale_order_line_invoice_rel AS rel
                    ON aml.id = rel.invoice_line_id
                LEFT JOIN sale_order_line AS sol
                    ON rel.order_line_id = sol.id
                LEFT JOIN sale_order AS so
                    ON sol.order_id = so.id
                LEFT JOIN crm_team AS team
                    ON so.team_id = team.id
                LEFT JOIN crm_team AS team_factura
                    ON am.team_id = team_factura.id
                
        """

    def _where(self):
        return """
            am.move_type IN ('out_invoice', 'out_refund')
            AND aml.display_type = 'product'
            AND aml.product_id IS NOT NULL
            AND am.name NOT LIKE 'RFVSIM%'
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS
                SELECT {self._select()}
                FROM {self._from()}
                WHERE {self._where()}
        """)