# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class ReporteCuentasPorClientes(models.Model):
    _name = 'balg_reportes_gerencia.reporte_cuentas_por_clientes'
    _description = 'Reporte de Cuentas por Clientes (Cobrar)'
    _auto = False
    _rec_name = 'x_cliente'

    id = fields.Integer(string="ID", readonly=True)
    x_company_id = fields.Integer(string="Compañía", readonly=True)
    x_cliente = fields.Char(string="Cliente", readonly=True)
    x_fecha_documento = fields.Date(string="Fecha Documento", readonly=True)
    x_saldo_usd = fields.Float(string="Saldo USD", readonly=True)
    x_codigo_cuenta = fields.Char(string="Código Cuenta", readonly=True)
    x_nombre_cuenta = fields.Char(string="Nombre Cuenta", readonly=True)
    x_tipo_cuenta = fields.Char(string="Tipo Cuenta", readonly=True)
    x_detalle = fields.Char(string="Detalle", readonly=True)
    x_No_Secuencia = fields.Char(string="No. Secuencia", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT 
                    aml.id AS id,
                    aml.company_id AS x_company_id,
                    rp.name AS x_cliente,
                    aml.date AS x_fecha_documento,
                    aml.amount_currency AS x_saldo_usd,
                    aa.code AS x_codigo_cuenta,
                    aa.name AS x_nombre_cuenta,
                    aa.account_type AS x_tipo_cuenta,
                    COALESCE(am.ref) AS x_detalle,
                    aml.move_name AS x_No_Secuencia
                FROM 
                    account_move_line aml
                JOIN 
                    res_partner rp ON aml.partner_id = rp.id
                JOIN 
                    account_move am ON aml.move_id = am.id
                JOIN 
                    account_account aa ON aml.account_id = aa.id
                WHERE 
                    am.state = 'posted' 
                    AND aa.account_type = 'asset_receivable'
                    AND aml.company_id = 2 
                    AND aml.amount_currency != 0
                ORDER BY 
                    rp.name ASC, 
                    aml.date ASC
            )
        """)