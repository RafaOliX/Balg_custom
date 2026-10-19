from odoo import models, fields, api


class ResPartnerCreditLimit(models.Model):
    _name = 'res.partner.credit_limit'
    _description = 'Límite de Crédito por Compañía (USD)'
    _rec_name = 'partner_id'
    _inherit = ['mail.thread']

    partner_id = fields.Many2one(
        'res.partner', string='Cliente',
        required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        required=True, index=True,
        default=lambda self: self.env.company,
    )
    use_credit_limit = fields.Boolean(
        string='Usar Límite de Crédito', default=True, tracking=True,
    )

    # Moneda fija del límite: USD
    credit_limit_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False),
        required=True,
        readonly=True,
    )

    credit_limit_usd = fields.Monetary(
        string='Límite de Crédito (USD)',
        currency_field='credit_limit_currency_id',
        default=0.0,
        tracking=True,
    )

    # Deuda solo con facturas pendientes (en USD, sin conversión)
    total_receivable_usd = fields.Monetary(
        string='Por Cobrar (USD)',
        compute='_compute_totals',
        currency_field='credit_limit_currency_id',
    )
    # Deuda incluyendo órdenes confirmadas sin facturar (en USD, sin conversión)
    total_credit_usd = fields.Monetary(
        string='Deuda Total (USD)',
        compute='_compute_totals',
        currency_field='credit_limit_currency_id',
    )

    _sql_constraints = [
        ('unique_partner_company', 'unique(partner_id, company_id)',
         'Ya existe un límite de crédito para este cliente en esta compañía.'),
    ]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id and not self.credit_limit_usd:
            self.credit_limit_usd = self.company_id.account_default_credit_limit_usd

    @api.depends('partner_id', 'company_id', 'credit_limit_currency_id')
    def _compute_totals(self):
        for rec in self:
            if not rec.partner_id or not rec.company_id or not rec.credit_limit_currency_id:
                rec.total_receivable_usd = 0.0
                rec.total_credit_usd = 0.0
                continue
            rec.total_receivable_usd = rec.partner_id._get_invoice_total_usd(
                rec.credit_limit_currency_id, company_id=rec.company_id.id,
            )
            rec.total_credit_usd = rec.partner_id._get_credit_total_usd(
                rec.credit_limit_currency_id, company_id=rec.company_id.id,
            )