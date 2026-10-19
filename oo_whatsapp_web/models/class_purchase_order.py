from urllib.parse import quote

from odoo import models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_sendwscompra(self):
        purchase_message = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("oo_whatsapp_web.purchase_message", "")
        )
        if not purchase_message:
            raise ValidationError(
                "No se ha configurado un mensaje para compras en WhatsApp. "
                "Configure el mensaje en Ajustes > Técnico > Configuración > WhatsApp."
            )

        for rec in self:
            if not rec.partner_id.mobile:
                raise ValidationError("El proveedor no tiene número de celular.")

            # Limpiar número de teléfono
            num_cel = rec.partner_id.mobile.replace("+", "").replace("-", "").replace(" ", "")
            if len(num_cel) not in (12, 13):
                raise ValidationError(
                    f"Número de teléfono mal formateado: {rec.partner_id.mobile}"
                )

            # Reemplazar placeholders
            message = purchase_message.replace("#PROVEEDOR", rec.partner_id.display_name)
            message = message.replace("#NUMERO", num_cel)
            # Codificar URL
            message_encoded = quote(message)

            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": f"https://wa.me/{num_cel}?text={message_encoded}",
            }