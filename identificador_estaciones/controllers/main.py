from odoo import http
from odoo.http import request

class EstacionController(http.Controller):
    # Usamos auth="public" para que el portal de Balgres permita la entrada
    @http.route('/web/login_estacion', type='http', auth="public", website=True, sitemap=False, csrf=False)
    def login_con_estacion(self, id=None, **kw):
        # Definimos a dónde queremos ir (al login oficial)
        redirect_url = '/web/login'
        
        # Creamos la respuesta de redirección
        response = request.redirect(redirect_url)
        
        if id:
            # Seteamos la cookie por 30 días
            # Importante: Usamos samesite='Lax' para que no lo bloquee Chrome/Edge
            response.set_cookie('odoo_estacion_id', id, max_age=2592000, samesite='Lax')
            
        return response