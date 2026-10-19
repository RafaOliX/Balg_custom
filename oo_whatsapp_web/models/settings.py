from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_message = fields.Char(
        string="Mensaje de Venta",
        config_parameter="oo_whatsapp_web.sale_message",
    )
    invoice_message = fields.Char(
        string="Mensaje de Factura",
        config_parameter="oo_whatsapp_web.invoice_message",
    )
    purchase_message = fields.Char(
        string="Mensaje de Compra",
        config_parameter="oo_whatsapp_web.purchase_message",
    )
