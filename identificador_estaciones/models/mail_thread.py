from odoo import models, api, fields
from odoo.http import request
from markupsafe import Markup

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        # Intentamos capturar la estación de la cookie
        try:
            estacion = request.httprequest.cookies.get('odoo_estacion_id') if request else False
        except Exception:
            estacion = False

        if estacion:
            for vals in vals_list:
                # Obtenemos el cuerpo actual del mensaje
                body = vals.get('body', '')
                # Si el mensaje ya trae algo o es un cambio de estado automático
                tag = f"<br/><span style='font-size: 10px; color: #999;'>💻 Estación: <b>{estacion}</b></span>"
                
                # Inyectamos la estación asegurando que sea HTML procesable
                vals['body'] = Markup(body or '') + Markup(tag)

        return super(MailMessage, self).create(vals_list)