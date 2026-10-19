from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    credit_limit_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda para Límite de Crédito',
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False),
        required=True,
        help="Moneda en la que se expresan los límites de crédito de los clientes.",
    )

    account_default_credit_limit_usd = fields.Monetary(
        string='Límite de Crédito por Defecto (USD)',
        currency_field='credit_limit_currency_id',
        default=0.0,
        help="Valor por defecto del límite para nuevos clientes, en USD.",
    )

    # El campo estándar de Odoo no lo usamos; lo dejamos de solo lectura
    account_default_credit_limit = fields.Monetary(
        string='Límite de Crédito por Defecto (Estándar)',
        readonly=True,
        help="No usar; se usa el campo en USD.",
    )