{
    'name': 'Balgres Web',
    'version': '16.0.1.0.0',
    'category': 'Website/Website',
    'depends': ['website'],
    'data': [
        'views/navbar_templates.xml',
        'views/templates.xml',
        'views/footer_navbar_templates.xml',
        'views/contact_templates.xml',
        'views/footer_info_templates.xml',
        'views/balgres_products_page.xml',
        'views/balgres_product_detail.xml',

        # Desde el shell de Odoo o psql: psql -d ceramicasbalgres-qa-dev-38074992 -c "DELETE FROM balgres_product;"
        'data/sync_products.xml',
        'data/balgres_product_acl.xml',
    ],
    'assets': {
        'web.assets_frontend': [

            
            # Main
            'balgres_web/static/src/scss/main.scss',
            # Abstracts
            'balgres_web/static/src/scss/abstracts/_variables.scss',
            'balgres_web/static/src/scss/abstracts/_fonts.scss',
            
            # Base
            'balgres_web/static/src/scss/base/_base.scss',
            'balgres_web/static/src/scss/base/_components-ui.scss',
            
            # Componentes
            'balgres_web/static/src/scss/components/_navbar.scss',
            'balgres_web/static/src/scss/components/_hero.scss',
            'balgres_web/static/src/scss/components/_about.scss',
            'balgres_web/static/src/scss/components/_distributors.scss',
            'balgres_web/static/src/scss/components/_why.scss',
            'balgres_web/static/src/scss/components/_testimonials.scss',
            'balgres_web/static/src/scss/components/_contact.scss',
            'balgres_web/static/src/scss/components/_products.scss',
            


            # JS
            'balgres_web/static/src/js/products.js',
            'balgres_web/static/src/js/navbar.js',
        ],
    },
    'installable': True,
    'application': False,
}