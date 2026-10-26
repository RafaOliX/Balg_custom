import os
import mimetypes
from odoo import http
from odoo.http import request

BALGRES_IMG_BASE = '/home/odoo/data/balgres_web'


class BalgresController(http.Controller):

    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kw):
        return request.render('balgres_web.balgres_home')

    @http.route('/contacto', type='http', auth='public', website=True)
    def contact_page(self, **kw):
        return request.render('balgres_web.balgres_contact_page')

    @http.route('/productos', type='http', auth='public', website=True)
    def products_page(self, formato=None, **kw):
        BalgresProduct = request.env['balgres.product'].sudo()
        formatos = sorted({p.formato for p in BalgresProduct.search([])})
        if not formato and formatos:
            formato = formatos[0]
        return request.render('balgres_web.balgres_products_page', {
            'formatos': formatos,
            'formato_activo': formato,
        })

    @http.route('/balgres_web/get_products', type='json',
                auth='public', website=True)
    def get_products(self, formato=None, **kw):
        domain = [('active', '=', True)]
        if formato:
            domain.append(('formato', '=', formato))

        products = request.env['balgres.product'].sudo().search(domain)

        return [{
            'id': p.id,
            'nombre': p.name,
            'slug': p.slug,
            'formato': p.formato,
            'imagen': p.image_base_url,
            'hover': p.image_hover_url,
            'url': f'/productos/{p.slug}',
        } for p in products]

    @http.route('/productos/<string:slug>', type='http',
                auth='public', website=True)
    def product_detail(self, slug, **kw):
        product = request.env['balgres.product'].sudo().search(
            [('slug', '=', slug)], limit=1)
        if not product:
            return request.not_found()
        return request.render('balgres_web.balgres_product_detail', {
            'product': product,
        })

    @http.route('/proyectos', type='http', auth='public', website=True)
    def projects_page(self, **kw):
        return request.render('balgres_web.balgres_projects_page')

class BalgresImageController(http.Controller):

    @http.route('/balgres_imagen/<path:filepath>', type='http',
                auth='public', website=True)
    def serve_image(self, filepath, **kw):
        if '..' in filepath or filepath.startswith('/'):
            return request.not_found()

        full = os.path.realpath(os.path.join(BALGRES_IMG_BASE, filepath))
        base = os.path.realpath(BALGRES_IMG_BASE)

        if not full.startswith(base + os.sep) or not os.path.isfile(full):
            return request.not_found()

        mimetype = mimetypes.guess_type(full)[0] or 'application/octet-stream'

        with open(full, 'rb') as f:
            content = f.read()

        return request.make_response(
            content,
            headers=[
                ('Content-Type', mimetype),
                ('Content-Length', len(content)),
                ('Cache-Control', 'public, max-age=604800'),
            ],
        )