from urllib.parse import quote
from odoo import models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_sendwsfactura(self):
        invoice_message = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("oo_whatsapp_web.invoice_message", "")
        )
        if not invoice_message:
            raise ValidationError(
                "No se ha configurado un mensaje para facturas en WhatsApp. "
                "Configure el mensaje en Ajustes > Técnico > Configuración > WhatsApp."
            )

        for rec in self:
            if not rec.partner_id.mobile:
                raise ValidationError("El cliente no tiene número de celular.")

            # Limpiar número de teléfono
            num_cel = rec.partner_id.mobile.replace("+", "").replace("-", "").replace(" ", "")
            if len(num_cel) not in (12, 13):
                raise ValidationError(
                    f"Número de teléfono mal formateado: {rec.partner_id.mobile}"
                )

            # ---- Usar amount_residual (saldo pendiente) ----
            if rec.currency_id:
                amount_formatted = rec.currency_id.format(rec.amount_residual)
            else:
                amount_formatted = f"{rec.amount_residual:,.2f}"

            if rec.amount_residual == 0:
                amount_formatted = "Pagado"

            # ---- Número de factura (invoice_number_next) ----
            factura_numero = rec.invoice_number_next or rec.name  # fallback a name si no tiene

            # Reemplazar placeholders
            message = invoice_message.replace("#CLIENTE", rec.partner_id.display_name)
            message = message.replace("#MONTO", amount_formatted)
            message = message.replace("#FACTURA", factura_numero)
            message = message.replace("#NUMERO", num_cel)

            message_encoded = quote(message)

            # ---- RETORNAR ACCIÓN URL ESTÁNDAR (SIN JS) ----
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',  # Abre en nueva pestaña
                'url': f"https://wa.me/{num_cel}?text={message_encoded}",
            }