from odoo import models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import requests
import urllib3
import pytz
import logging
from bs4 import BeautifulSoup

urllib3.disable_warnings()
_logger = logging.getLogger(__name__)


class ResCurrencyRateServer(models.Model):
    _inherit = 'res.currency.rate.server'

    # -------------------------------------------------------------------------
    # 1) Fix del scraping BCV (parsing del HTML)
    # -------------------------------------------------------------------------
    def _get_scraping_central_bank(self):
        """Override: parseo robusto del HTML del BCV."""
        url = "https://www.bcv.org.ve/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept-Language': 'es-VE,es;q=0.9,en;q=0.8',
        }
        try:
            req = requests.get(url, verify=False, timeout=30, headers=headers)
        except requests.exceptions.RequestException as e:
            raise ValidationError(_('No se pudo conectar al BCV: %s') % e)

        if req.status_code != 200:
            raise ValidationError(_('BCV respondió con status %s') % req.status_code)

        html = BeautifulSoup(req.text, "html.parser")

        usd = self.env.ref('base.USD')
        eur = self.env.ref('base.EUR')

        if self.name.id == usd.id:
            div_id = 'dolar'
        elif self.name.id == eur.id:
            div_id = 'euro'
        else:
            raise ValidationError(
                _("Solo se pueden consultar USD y EUR para este servicio")
            )

        div = html.find('div', {'id': div_id})
        if not div:
            raise ValidationError(
                _("BCV cambió su HTML: no encuentro div#%s") % div_id
            )
        strong = div.find('strong')
        if not strong:
            raise ValidationError(
                _("BCV cambió su HTML: no encuentro <strong> dentro de div#%s") % div_id
            )

        txt = strong.get_text(strip=True)  # "875,65050000"
        try:
            return float(txt.replace('.', '').replace(',', '.'))
        except ValueError:
            raise ValidationError(
                _("No se pudo parsear el valor del BCV: '%s'") % txt
            )

    # -------------------------------------------------------------------------
    # 2) Fix del fin de semana/feriado (reemplaza el `+=` roto del partner)
    # -------------------------------------------------------------------------
    def _get_currency_rate(self):
        """Override: reemplaza el `amount += inverse_rate` del partner.

        Reglas:
        - Día hábil normal: scrapea BCV, crea registro con tasa fresca.
        - Fin de semana o feriado: usa la última tasa conocida, crea registro.
        - BCV caído en día hábil: usa la última tasa conocida, crea registro.
        - SIEMPRE se crea un registro del día.
        """
        date_today = date.today()
        weekday = date_today.weekday()
        is_special = (
            weekday in [5, 6]
            or self._get_is_holiday(date_today, self.company_id)
        )

        # inverse_rate es company-dependent → forzar la compañía correcta
        last_known_rate = self.name.with_company(self.company_id).inverse_rate

        if is_special:
            amount = last_known_rate
            _logger.info(
                "Tasa %s / %s: fin de semana o feriado. "
                "Usando última tasa conocida: %s",
                self.name.name, self.company_id.name, amount
            )
        else:
            try:
                if self.server == 'bcv_scraping':
                    amount = self._get_scraping_central_bank()
                elif self.server == 'BCV':
                    amount = self._request_central_bank()
                elif self.server == 'dolar-today':
                    amount = self._request_dollar_today()
                elif self.server == 'enparale-lovzla':
                    amount = self._request_parallel_ve()
                else:
                    raise UserError(_('Selecciona un servicio de tasa de cambio'))
            except Exception as e:
                _logger.warning(
                    "Tasa %s / %s: fallo el scraping (%s). "
                    "Usando última tasa conocida.",
                    self.name.name, self.company_id.name, e
                )
                amount = 0

            if not amount:
                amount = last_known_rate

        # SIEMPRE se crea el registro del día
        value = self._prepare_currency_rate_value(amount)
        self.env['res.currency.rate'].sudo().create(value)
        self.update_product(amount)
        self.update_pricelist(amount)

    # -------------------------------------------------------------------------
    # 3) Cron idempotente (evita los "duplicate key" si ya existe tasa del día)
    # -------------------------------------------------------------------------
    def _cron_update_product(self):
        """Override: salta las compañías que ya tienen tasa de hoy."""
        tz_caracas = pytz.timezone("America/Caracas")
        today = datetime.now(tz_caracas).strftime('%Y-%m-%d')

        update = self.env['res.currency.rate.server'].search([])
        for item in update:
            try:
                existing = self.env['res.currency.rate'].search([
                    ('name', '=', today),
                    ('currency_id', '=', item.name.id),
                    ('company_id', '=', item.company_id.id),
                ], limit=1)

                if existing:
                    _logger.info(
                        "Tasa ya existe para %s / %s (fecha %s), saltando",
                        item.name.name, item.company_id.name, today
                    )
                    continue

                item.action_post()
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception(
                    "Fallo actualizando tasa para %s / compañía %s: %s",
                    item.name.name if item.name else '?',
                    item.company_id.name if item.company_id else '?',
                    e,
                )