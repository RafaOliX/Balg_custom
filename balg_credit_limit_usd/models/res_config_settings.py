from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    credit_limit_currency_id = fields.Many2one(
        related='company_id.credit_limit_currency_id',
        string='Moneda para Límite de Crédito',
        readonly=False,
    )
    account_default_credit_limit_usd = fields.Monetary(
        related='company_id.account_default_credit_limit_usd',
        string='Límite de Crédito por Defecto (USD)',
        currency_field='credit_limit_currency_id',
        readonly=False,
    )