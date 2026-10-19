# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteDiarioCobranza(models.Model):
    _name = 'balg_reportes_gerencia.reporte_diario_cobranza'
    _description = 'Reporte de Cobranza'
    _auto = False

    id = fields.Integer(string="ID", readonly=True)
    x_nombre_diario = fields.Char(string="Producto", readonly=True)
    x_consecutivo_pago = fields.Char(string="Referencia", readonly=True)
    x_fecha = fields.Char(string="Ubicación", readonly=True)
    x_total_monto_pago = fields.Char(string="Tono", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW balg_reportes_gerencia_reporte_diario_cobranza AS (
                SELECT
                        ROW_NUMBER() OVER () AS id,
    aj.name AS x_nombre_diario,am.name AS x_consecutivo_pago,
    am.date x_fecha,
    SUM(ap.amount) AS x_total_monto_pago
FROM account_payment ap
INNER JOIN account_move am ON am.id = ap.move_id
INNER JOIN account_journal aj ON aj.id = am.journal_id
WHERE am.state = 'posted'
  AND am.company_id = 2  
  AND payment_type = 'inbound'
GROUP BY  aj.name,aj.id,x_consecutivo_pago,am.date
            )
        """)