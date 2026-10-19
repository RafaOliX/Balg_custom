from urllib.parse import quote

from odoo import models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_send_whatsapp(self):
        """Open WhatsApp Web with a greeting message for this contact."""
        for rec in self:
            if not rec.mobile:
                raise ValidationError("El contacto no tiene número de celular.")

            # Limpiar número de teléfono
            num_cel = rec.mobile.replace("+", "").replace("-", "").replace(" ", "")
            if len(num_cel) not in (12, 13):
                raise ValidationError(
                    f"Número de teléfono mal formateado: {rec.mobile}"
                )

            # Mensaje simple de saludo
            message = f"Buen día, {rec.display_name}"
            message_encoded = quote(message)

            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": f"https://wa.me/{num_cel}?text={message_encoded}",
            }
