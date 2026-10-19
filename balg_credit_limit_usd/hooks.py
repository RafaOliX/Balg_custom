import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'res_partner'
          AND column_name IN ('credit_limit_usd', 'use_credit_limit_balg')
    """)
    cols = {r[0] for r in cr.fetchall()}
    if 'credit_limit_usd' not in cols:
        return

    cr.execute("""
        SELECT id, credit_limit_usd, use_credit_limit_balg
        FROM res_partner
        WHERE credit_limit_usd IS NOT NULL AND credit_limit_usd <> 0
    """)
    rows = cr.fetchall()
    if not rows:
        return

    companies = env['res.company'].search([])
    CreditLimit = env['res.partner.credit_limit']
    usd = env.ref('base.USD', raise_if_not_found=False)

    for partner_id, limit, use_limit in rows:
        for company in companies:
            exists = CreditLimit.search([
                ('partner_id', '=', partner_id),
                ('company_id', '=', company.id),
            ], limit=1)
            if not exists:
                CreditLimit.create({
                    'partner_id': partner_id,
                    'company_id': company.id,
                    'use_credit_limit': bool(use_limit),
                    'credit_limit_currency_id': usd.id if usd else False,
                    'credit_limit_usd': limit,
                })

    _logger.info("Migrados %s partners a res.partner.credit_limit", len(rows))