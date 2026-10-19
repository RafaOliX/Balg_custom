from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        self._check_credit_limit()
        return super().action_post()

    def _check_credit_limit(self):
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue

            partner = move.partner_id
            company = move.company_id or self.env.company

            if not partner._has_credit_limit(company.id):
                continue

            rec = partner._get_credit_limit_record(company.id)
            credit_currency = rec.credit_limit_currency_id or company.credit_limit_currency_id
            credit_limit = rec.credit_limit_usd

            # Solo validamos facturas en la moneda del límite (USD)
            if move.currency_id != credit_currency:
                continue

            total_due = partner._get_credit_total_usd(credit_currency, company_id=company.id)

            # Para rectificativas, restar el monto
            move_amount = move.amount_total
            if move.move_type == 'out_refund':
                move_amount = -move_amount

            total_with_move = total_due + move_amount

            _logger.info(
                "Validación crédito: partner=%s company_id=%s límite=%s %s "
                "deuda=%s factura=%s total=%s",
                partner.name, company.id, credit_limit, credit_currency.name,
                total_due, move_amount, total_with_move,
            )

            if float_compare(total_with_move, credit_limit,
                             precision_rounding=credit_currency.rounding) > 0:
                fmt = lambda v: credit_currency.format(v)
                raise ValidationError(_(
                    "El cliente %(partner)s ha excedido su límite de crédito de %(limit)s.\n"
                    "Deuda actual: %(due)s\n"
                    "Esta factura: %(move)s\n"
                    "Total: %(total)s",
                    partner=partner.name,
                    limit=fmt(credit_limit),
                    due=fmt(total_due),
                    move=fmt(move_amount),
                    total=fmt(total_with_move),
                ))
        return True