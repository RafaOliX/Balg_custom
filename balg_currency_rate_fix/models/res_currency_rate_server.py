import logging
from datetime import datetime
import pytz
from odoo import api, models

_logger = logging.getLogger(__name__)


class ResCurrencyRateServer(models.Model):
    _inherit = 'res.currency.rate.server'

    @api.model
    def _cron_update_currency_rate(self):
        """Override: idempotente y aislado por compañía.

        El cron del partner:
            for currency in server_rate:
                currency._get_currency_rate()

        Problema: si el cron 22 (OCA) ya creó la tasa del día para esa
        moneda/empresa, el create() del partner choca con el constraint
        `res_currency_rate_unique_name_per_day` → UniqueViolation → el loop
        se rompe y las empresas restantes no se procesan.

        Fix:
        - Skip si ya existe tasa del día para esa moneda/empresa.
        - try/except por compañía para que una falla no tumbe las demás.
        - commit por compañía para que los éxitos parciales persistan.
        """
        tz_caracas = pytz.timezone("America/Caracas")
        today_str = datetime.now(tz_caracas).strftime('%Y-%m-%d')

        for server in self.search([]):
            existing = self.env['res.currency.rate'].search([
                ('name', '=', today_str),
                ('currency_id', '=', server.currency_server_id.id),
                ('company_id', '=', server.company_id.id),
            ], limit=1)

            if existing:
                _logger.info(
                    "Tasa ya existe: %s / %s / %s. Skip.",
                    today_str,
                    server.currency_server_id.name,
                    server.company_id.name,
                )
                continue

            try:
                server._get_currency_rate()
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception(
                    "Fallo tasa %s / %s: %s",
                    server.currency_server_id.name,
                    server.company_id.name,
                    e,
                )