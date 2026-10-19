# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "WhatsApp Web",
    "summary": """
        Send WhatsApp Web messages from Sales Orders, Invoices, Purchase Orders, and Contacts""",
    "author": "Be OnlyOne",
    "maintainers": ["onlyone-soft"],
    "website": "https://onlyone.odoo.com/",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "version": "18.0.3.3.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "depends": ["base", "sale", "account", "purchase"],
    "data": [
        "data/ir_config_parameter_data.xml",
        # "views/res_config_settings_views.xml",
        "views/buttons_sale_order_views.xml",
        "views/buttons_account_move_views.xml",
        "views/buttons_purchase_order_views.xml",
        "views/buttons_res_partner_views.xml",
    ],
}
