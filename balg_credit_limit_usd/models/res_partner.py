from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit_ids = fields.One2many(
        'res.partner.credit_limit', 'partner_id',
        string='Límites de Crédito (USD)',
    )

    # ------------------------------------------------------------------
    # Utilidades de acceso al límite
    # ------------------------------------------------------------------
    def _get_credit_limit_record(self, company_id=None):
        self.ensure_one()
        if not company_id:
            company_id = self.env.company.id
        return self.env['res.partner.credit_limit'].search([
            ('partner_id', '=', self.id),
            ('company_id', '=', company_id),
        ], limit=1)

    def _has_credit_limit(self, company_id=None):
        self.ensure_one()
        rec = self._get_credit_limit_record(company_id)
        return bool(rec and rec.use_credit_limit and rec.credit_limit_usd > 0)

    # ------------------------------------------------------------------
    # Cálculo de la deuda (SIN conversión)
    # ------------------------------------------------------------------
    def _get_invoice_total_usd(self, target_currency, company_id=None):
        """Saldo pendiente del cliente en cuentas por cobrar (facturas,
        rectificativas y pagos no aplicados) en la moneda objetivo.
        Sin conversión: solo líneas cuya moneda sea `target_currency`.
        """
        self.ensure_one()
        if not target_currency:
            return 0.0
        if not company_id:
            company_id = self.env.company.id
    
        lines = self.env['account.move.line'].search([
            ('partner_id', '=', self.id),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            ('company_id', '=', company_id),
            ('currency_id', '=', target_currency.id),   # 👈 solo USD
        ])
        # ⚠️ amount_residual_currency está en la moneda de la línea (USD);
        #    amount_residual estaría en moneda de compañía (Bs) → NO usar.
        return sum(lines.mapped('amount_residual_currency'))
    
    
    def _get_credit_total_usd(self, target_currency, company_id=None):
        """Deuda total: saldo por cobrar (líneas contables) + órdenes sin facturar.
        Sin conversión."""
        self.ensure_one()
        if not target_currency:
            return 0.0
        if not company_id:
            company_id = self.env.company.id
    
        total_due = self._get_invoice_total_usd(target_currency, company_id=company_id)
    
        orders = self.env['sale.order'].search([
            ('partner_id', '=', self.id),
            ('state', 'in', ['sale', 'done']),
            ('invoice_status', 'in', ['to invoice', 'no']),
            ('company_id', '=', company_id),
            ('currency_id', '=', target_currency.id),
        ])
        for order in orders:
            total_due += order.amount_total
    
        return total_due