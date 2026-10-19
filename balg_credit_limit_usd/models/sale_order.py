from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        self._check_credit_limit()
        return super().action_confirm()

    def _check_credit_limit(self):
        for order in self:
            partner = order.partner_id
            company = order.company_id or self.env.company

            if not partner._has_credit_limit(company.id):
                continue

            rec = partner._get_credit_limit_record(company.id)
            credit_currency = rec.credit_limit_currency_id or company.credit_limit_currency_id
            credit_limit = rec.credit_limit_usd

            # Solo validamos órdenes en la moneda del límite (USD)
            if order.currency_id != credit_currency:
                continue

            total_due = partner._get_credit_total_usd(credit_currency, company_id=company.id)
            order_amount = order.amount_total
            total_with_order = total_due + order_amount

            if float_compare(total_with_order, credit_limit,
                             precision_rounding=credit_currency.rounding) > 0:
                fmt = lambda v: credit_currency.format(v)
                raise ValidationError(_(
                    "El cliente %(partner)s ha excedido su límite de crédito de %(limit)s.\n"
                    "Deuda actual: %(due)s\n"
                    "Esta orden: %(order)s\n"
                    "Total: %(total)s",
                    partner=partner.name,
                    limit=fmt(credit_limit),
                    due=fmt(total_due),
                    order=fmt(order_amount),
                    total=fmt(total_with_order),
                ))
        return True