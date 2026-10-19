from odoo import fields, models, tools

class PurchasePriceHistoryBalg(models.Model):
    _name = 'purchase.price.history.balg'
    _description = 'Purchase Price History (Balg)'
    _auto = False

    name = fields.Char(string="Línea de orden de compra")
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    user_id = fields.Many2one("res.users", string="Vendedor")
    product_id = fields.Many2one("product.product", string="Producto")
    purchase_order_date = fields.Datetime(string="Fecha de la orden de compra")
    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom', string="Unidad de Medida")
    currency_id = fields.Many2one("res.currency", string="Moneda")
    currency_id2 = fields.Many2one("res.currency", string="Moneda secundaria")
    unit_price = fields.Monetary(string="Precio", currency_field='currency_id')
    price_average = fields.Monetary(string="P/P", currency_field='currency_id')
    price_unit_rate = fields.Monetary(string='Precio al cambio', currency_field='currency_id2')
    price_average_rate = fields.Monetary(string="P/P al cambio", currency_field='currency_id2')
    total_price = fields.Monetary(string="Total", currency_field='currency_id')
    total_price_rate = fields.Monetary(string='Total al cambio', currency_field='currency_id2')
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    invoice_number_next = fields.Char(string='Nro de factura')
    invoice_number_control = fields.Char(string='Nro de control')




    def _select(self):
        return """
            row_number() over()                                                  AS id,
            move_line.name                                                       AS name,
            move_line.quantity                                                   AS product_uom_qty,
            move_line.price_subtotal                                             AS price_subtotal,
            move_line.price_subtotal / NULLIF(move_line.quantity, 0)             AS price_unit_net,
            move_line.price_total                                                AS total_price,
            move_line.product_uom_id                                             AS product_uom,
            move_line.product_id                                                 AS product_id,
            move.partner_id                                                      AS partner_id,
            move_line.currency_id                                                AS currency_id,
            move_line.currency_id2                                               AS currency_id2,
            move_line.price_subtotal_rate                                        AS price_subtotal_rate,
            0 AS total_price_rate,
            
            move_line.price_unit                                                 AS unit_price,
            0 AS price_unit_rate,
            (move_line.price_subtotal / NULLIF(move_line.quantity, 0))           AS price_average,
            0 AS price_average_rate,

            move.invoice_user_id                                                 AS user_id,
            move.invoice_date                                                    AS purchase_order_date,
            move.company_id                                                      AS company_id,
            move.partner_shipping_id                                             AS team_id,
            move.name                                                            AS invoice_number_next,
            move.ref                                                             AS invoice_number_control,
            move.state                                                           AS invoice_state
        """

    def _from(self):
        return """
            purchase_order_line                                  AS purchase_line
                INNER JOIN purchase_order                        AS purchase_order
                    ON purchase_line.order_id = purchase_order.id
                INNER JOIN res_users                             AS res_user
                    ON purchase_order.user_id = res_user.id
                LEFT JOIN account_move_line                      AS move_line
                    ON purchase_line.id = move_line.purchase_line_id
                LEFT JOIN account_move                           AS move
                    ON move_line.move_id = move.id
        """

    def _where(self):
        return """
            purchase_line.state = 'purchase'
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} as
                SELECT {self._select()}
                    FROM {self._from()}
                WHERE {self._where()}
        """)