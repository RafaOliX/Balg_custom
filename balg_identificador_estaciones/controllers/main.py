from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class EstacionController(http.Controller):

    @http.route(
        '/web/login_estacion',
        type='http',
        auth='public',
        website=False,
        sitemap=False,
        csrf=False,
    )
    def login_con_estacion(self, id=None, estacion=None, **kw):
        _logger.info("login_estacion llamado con id=%s estacion=%s", id, estacion)
        valor = estacion or id
        response = request.redirect('/web/login')
        if valor:
            response.set_cookie(
                'odoo_estacion_id',
                valor,
                max_age=2147483647,
                samesite='Lax',
                httponly=True,
            )
        return response