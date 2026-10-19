from odoo import models, api
from odoo.http import request
from markupsafe import Markup, escape
import logging

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        estacion = False
        try:
            if request and getattr(request, 'httprequest', None):
                estacion = request.httprequest.cookies.get('odoo_estacion_id')
        except Exception:
            estacion = False

        _logger.info("mail.message.create estacion=%s", estacion)

        if estacion:
            estacion = escape(estacion)
            for vals in vals_list:
                body = vals.get('body', '')
                tag = Markup(
                    "<br/><span style='font-size: 10px; color: #999;'>"
                    "🖥️Estación: <b>{}</b></span>"
                ).format(estacion)
                vals['body'] = Markup(body or '') + tag

        return super().create(vals_list)