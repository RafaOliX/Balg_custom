from odoo import fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

def _sort_lines(lines):
    """Ordena las líneas de un grupo: factura primero, resto por fecha real."""
    def key(l):
        try:
            d = datetime.strptime(l.get('date') or '', '%d/%m/%Y')
        except (ValueError, TypeError):
            d = datetime.min
        # 0 = factura primero, 1 = resto ordenado por fecha
        return (0 if l.get('is_invoice') else 1, d)
    return sorted(lines, key=key)

class AccountPayableReceivableWizardBalg(models.TransientModel):
    _name = 'account.payable.receivable.wizard.balg'
    _description = 'Account Payable Balg Receivable'
    emission_date = fields.Date(
        string='Fecha de Emisión',
        default=lambda self: fields.Date.context_today(self),
        required=True,
        help="Fecha con la que se emite el estado de cuenta (aparece en el encabezado)."
    )
    show_all_movements = fields.Boolean(
        string='Mostrar todos los movimientos',
        default=True,
        help='Si está marcado, muestra todos los movimientos del cliente sin importar el rango de fechas. Si está desmarcado, usa el rango de fechas seleccionado.'
    )
    only_pending = fields.Boolean(
        string='Mostrar solo facturas pendientes',
        default=True,
        help='Si está marcado, solo se muestran las facturas con saldo pendiente '
             '(no saldadas). Si se desmarca, se muestran también las saldadas.'
    )
    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date(string='Date To',
                          default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    account_type = fields.Selection(selection=[
        ('asset_receivable', 'Asset Receivable'), ('liability_payable', 'Liability Payable')], string='Account Type',
        default='asset_receivable')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    report_currency_id = fields.Many2one(
        'res.currency',
        string='Report Currency',
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False) or self.env.company.currency_id,
        required=True,
        help="Moneda en la que se convertirán los montos del reporte."
    )

    def action_send_whatsapp_estado(self):
        """Abre WhatsApp con el resumen del estado de cuenta del cliente."""
        partner = self.partner_id
        if not partner:
            raise ValidationError("Debe seleccionar un cliente.")
        if not partner.mobile:
            raise ValidationError("El cliente no tiene número de celular.")
        num_cel = partner.mobile.replace("+", "").replace("-", "").replace(" ", "")
        if len(num_cel) not in (12, 13):
            raise ValidationError(f"Número de teléfono mal formateado: {partner.mobile}")
        # Calcular total adeudado (restando rectificativas)
        total_adeudado = 0.0
        total_rectificativas_huerfanas = 0.0
        for move_id, counter_move in self._get_sql().items():
            # El crédito a favor NO es deuda: se muestra pero no suma al saldo
            if counter_move.get('tipo') == 'remanente':
                continue
            total_adeudado += counter_move.get('total', 0.0)
            for line in counter_move.get('lines', []):
                if line.get('tipo') == 'rectificativa_huerfana':
                    total_rectificativas_huerfanas += abs(line.get('amount', 0))
        total_adeudado -= total_rectificativas_huerfanas
        if self.report_currency_id:
            amount_formatted = self.report_currency_id.format(total_adeudado)
        else:
            amount_formatted = f"{total_adeudado:,.2f}"
        message = (f"Buen día, {partner.display_name}. "
                   f"Su saldo total adeudado es de {amount_formatted}.")
        from urllib.parse import quote
        message_encoded = quote(message)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f"https://wa.me/{num_cel}?text={message_encoded}",
        }

    def _get_report_name(self, file_extension='pdf'):
        partner_name = self.partner_id.name or 'Sin Cliente'
        import re
        clean_name = re.sub(r'[^\w\s\-]', '', partner_name).strip().replace(' ', '_')
        emission = self.emission_date.strftime('%d-%m-%Y') if self.emission_date else ''
        return f"Estado_de_Cuenta_{clean_name}_{emission}"

    def _get_data(self):
        
        """Obtiene todas las facturas del partner y sus movimientos asociados."""
        partner = self.partner_id
        company = self.company_id
        report_currency = self.report_currency_id
        is_receivable = (self.account_type == 'asset_receivable')
        invoice_types = ['out_invoice'] if is_receivable else ['in_invoice']
        refund_types  = ['out_refund']  if is_receivable else ['in_refund']
        payment_type  = 'inbound'       if is_receivable else 'outbound'
        account_type  = self.account_type


        _logger.info("=== _get_data START === partner=%s (%s) account_type=%s report_currency=%s show_all=%s only_pending=%s",
             partner.id, partner.name, self.account_type,
             report_currency.name, self.show_all_movements, self.only_pending)
        if self.show_all_movements:
            from_date = fields.Date.to_date('1900-01-01')
            to_date = fields.Date.to_date('2100-12-31')
            _logger.info("=== Mostrando TODOS los movimientos (sin filtro de fechas) ===")
        else:
            from_date = self.from_date
            to_date = self.to_date
            _logger.info("=== Usando rango de fechas: %s - %s ===", from_date, to_date)
    
        _logger.info("Partner ID: %s, Nombre: %s", partner.id if partner else None, partner.name if partner else "Ninguno")
    
        # ---- OBTENER FACTURAS (SOLO PUBLICADAS) ----
        domain = [
            ('partner_id', '=', partner.id),
            ('move_type', 'in', invoice_types),
            ('state', '=', 'posted'),
            ('company_id', '=', company.id),
        ]
        if not self.show_all_movements:
            domain.extend([('date', '>=', from_date), ('date', '<=', to_date)])
    
        invoices = self.env['account.move'].search(domain, order='date ASC')
        _logger.info("Facturas encontradas: %s", len(invoices))
        if not invoices:
            return {}
    
        grouped_data = {}
    
        # ---- PROCESAR FACTURAS ----
        for invoice in invoices:
            _logger.info("Procesando factura: %s (ID: %s)", invoice.name, invoice.id)
            invoice_id = invoice.id
    
            amount_total = invoice.amount_total
            if invoice.currency_id != report_currency:
                amount_total = invoice.currency_id._convert(
                    amount_total,
                    report_currency,
                    company,
                    invoice.date or fields.Date.today()
                )
    
            grouped_data[invoice_id] = {
                "move_name": invoice.name,
                "balance": abs(amount_total),
                "total": 0.0,
                "lines": [],
                "factura_agregada": False,
                "tipo": "factura",
            }
    
            # ---- LÍNEA DE FACTURA ----
            grouped_data[invoice_id]["lines"].append({
                "date": invoice.date.strftime('%d/%m/%Y') if invoice.date else '',
                "ref": "",
                "counter_move_ref": "",
                "line_name": invoice.name,
                "journal_code": invoice.journal_id.code,
                "amount": abs(amount_total),
                "currency_id": report_currency.id,
                "invoice_number_next": invoice.invoice_number_next,
                "invoice_number_control": invoice.invoice_number_control,
                "is_invoice": True,
                "is_payment": False,
                "tipo": "factura",
            })
            grouped_data[invoice_id]["factura_agregada"] = True
    
            # ---- PAGOS ----
            payments = self._get_invoice_payments(invoice)
            for payment in payments:
                date_val = payment.get('date')
                grouped_data[invoice_id]["lines"].append({
                    "date": date_val.strftime('%d/%m/%Y') if date_val else '',
                    "ref": payment.get('ref'),
                    "counter_move_ref": payment.get('document_name'),
                    "line_name": payment.get('name', 'Pago'),
                    "journal_code": payment.get('journal_code'),
                    "amount": -abs(payment.get('amount', 0)),
                    "currency_id": report_currency.id,
                    "invoice_number_next": "",
                    "invoice_number_control": "",
                    "is_payment": True,
                    "is_invoice": False,
                    "tipo": "pago",
                })
    
            # ---- NOTAS DÉBITO ----
            debit_notes = self._get_debit_notes(invoice, invoice_types)
            for debit_note in debit_notes:
                amount = debit_note.get('amount', 0)
                date_val = debit_note.get('date')
                grouped_data[invoice_id]["lines"].append({
                    "date": date_val.strftime('%d/%m/%Y') if date_val else '',
                    "ref": debit_note.get('ref'),
                    "counter_move_ref": debit_note.get('origin'),
                    "line_name": debit_note.get('name', 'Nota Débito'),
                    "journal_code": debit_note.get('journal_code'),
                    "amount": amount,
                    "currency_id": report_currency.id,
                    "invoice_number_next": "",
                    "invoice_number_control": "",
                    "is_payment": False,
                    "is_invoice": False,
                    "tipo": "nota_debito",
                    "document_id": debit_note.get('document_id'),
                })
    
            # Calcular total de la factura
            grouped_data[invoice_id]["total"] = sum(line['amount'] for line in grouped_data[invoice_id]["lines"])
            # Ordenar líneas
            grouped_data[invoice_id]["lines"] = _sort_lines(grouped_data[invoice_id]["lines"])
    
        # ---- ASOCIACIÓN MANUAL DE RECTIFICATIVAS POR REFERENCIA DE FACTURA ----
        # Buscar TODAS las rectificativas PUBLICADAS del partner
        refund_domain = [
            ('partner_id', '=', partner.id),
            ('state', '=', 'posted'),
            ('company_id', '=', company.id),
            '|',
            ('move_type', 'in', refund_types),
            '&',
            ('move_type', 'in', invoice_types),
            ('amount_total', '<', 0),
        ]
        if not self.show_all_movements:
            refund_domain.append(('date', '>=', from_date))
            refund_domain.append(('date', '<=', to_date))
    
        all_refunds = self.env['account.move'].search(refund_domain)
        _logger.info("Total rectificativas encontradas para asociación: %s", len(all_refunds))
    
        for invoice_id, group in grouped_data.items():
            invoice = self.env['account.move'].browse(invoice_id)
            if not invoice.exists():
                continue
            invoice_ref = invoice.invoice_number_next or invoice.name.split('/')[-1]
            _logger.info("Buscando rectificativas para factura %s con referencia %s", invoice.name, invoice_ref)
    
            for refund in all_refunds:
                if any(line.get('document_id') == refund.id for line in group['lines']):
                    continue
    
                # Verificar coincidencia en varios campos
                match = False
                # CAMPO PRINCIPAL: reason (donde está el número de factura original)
                if refund.reason and (invoice_ref in refund.reason or invoice.name in refund.reason):
                    match = True
                    _logger.info("Coincidencia por reason: %s", refund.reason)
                # En ref
                elif refund.ref and (invoice_ref in refund.ref or invoice.name in refund.ref):
                    match = True
                    _logger.info("Coincidencia por ref: %s", refund.ref)
                # En invoice_origin
                elif refund.invoice_origin and (invoice_ref in refund.invoice_origin or invoice.name in refund.invoice_origin):
                    match = True
                    _logger.info("Coincidencia por invoice_origin: %s", refund.invoice_origin)
    
                if match:
                    amount = refund.amount_total
                    if refund.currency_id != report_currency:
                        amount = refund.currency_id._convert(amount, report_currency, company, refund.date or fields.Date.today())
                    amount = -abs(amount)
                    # Guardar el reason como referencia para mostrarlo
                    referencia = refund.reason or refund.invoice_origin or refund.ref
                    group['lines'].append({
                        "date": refund.date.strftime('%d/%m/%Y') if refund.date else '',
                        "ref": refund.ref,
                        "counter_move_ref": referencia,
                        "line_name": refund.name,
                        "journal_code": refund.journal_id.code,
                        "amount": amount,
                        "currency_id": report_currency.id,
                        "invoice_number_next": "",
                        "invoice_number_control": "",
                        "is_payment": False,
                        "is_invoice": False,
                        "is_refund": True,
                        "tipo": "rectificativa",
                        "document_id": refund.id,
                    })
                    group['total'] = sum(line['amount'] for line in group['lines'])
                    grouped_data[invoice_id]["lines"] = _sort_lines(grouped_data[invoice_id]["lines"])
                    _logger.info("Rectificativa %s asociada a factura %s (referencia: %s)", refund.name, invoice.name, referencia)
    
        # ---- DOCUMENTOS HUÉRFANOS (rectificativas no asociadas) ----
        used_refund_ids = set()
        for group in grouped_data.values():
            for line in group.get('lines', []):
                if line.get('document_id') and line.get('tipo') in ('rectificativa', 'rectificativa_huerfana'):
                    used_refund_ids.add(line['document_id'])
    
        orphan_domain = [
            ('partner_id', '=', partner.id),
            ('state', '=', 'posted'),
            ('company_id', '=', company.id),
            '|',
            ('move_type', 'in', refund_types),
            '&',
            ('move_type', 'in', invoice_types),
            ('amount_total', '<', 0),
            ('id', 'not in', list(used_refund_ids)),
        ]
        if not self.show_all_movements:
            orphan_domain.append(('date', '>=', from_date))
            orphan_domain.append(('date', '<=', to_date))
    
        orphan_refunds = self.env['account.move'].search(orphan_domain)
        _logger.info("Rectificativas huérfanas encontradas: %s", len(orphan_refunds))
        for refund in orphan_refunds:
            fake_id = -refund.id
            grouped_data[fake_id] = {
                "move_name": refund.name,
                "balance": 0,
                "total": 0,
                "lines": [],
                "factura_agregada": False,
                "tipo": "rectificativa_huerfana",
            }
        
            amount = refund.amount_total
            if refund.currency_id != report_currency:
                amount = refund.currency_id._convert(amount, report_currency, company, refund.date or fields.Date.today())
            grouped_data[fake_id]["lines"].append({
                "date": refund.date.strftime('%d/%m/%Y') if refund.date else '',
                "ref": refund.ref,
                "counter_move_ref": refund.invoice_origin,
                "line_name": refund.name,
                "journal_code": refund.journal_id.code,
                "amount": -abs(amount),
                "currency_id": report_currency.id,
                "invoice_number_next": "",
                "invoice_number_control": "",
                "is_invoice": False,
                "is_payment": False,
                "is_refund": True,
                "tipo": "rectificativa_huerfana",
                "document_id": refund.id,
            })
            grouped_data[fake_id]["total"] = -abs(amount)
            grouped_data[fake_id]["balance"] = -abs(amount)
    
        _logger.info("Total de grupos: %s", len(grouped_data))
    
                # ---- PAGOS CON REMANENTE (CRÉDITO A FAVOR) ----
        if partner:
            # 1) todos los apuntes de pago (inbound) del partner, publicados, en la compañía
            payment_moves = self.env['account.move'].search([
                ('company_id', '=', company.id),
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('move_type', '=', 'entry'),  # los pagos son 'entry', no factura
            ])

            # 2) sus líneas contra la cuenta por cobrar que aún tengan saldo
            payment_lines = self.env['account.move.line'].search([
                ('move_id', 'in', payment_moves.ids),
                ('account_id.account_type', '=', account_type),
                ('amount_residual', '!=', 0),
                ('reconciled', '=', False),
            ])
            _logger.info("Crédito: %s líneas candidatas (account_type=%s)",
                         len(payment_lines), account_type)
            
            for aml in payment_lines:
                ap = self.env['account.payment'].search([
                    ('move_id', '=', aml.move_id.id),
                    ('payment_type', '=', payment_type),
                ], limit=1)
                if not ap:
                    continue
                ...

                amount = abs(aml.amount_residual_currency or aml.amount_residual)
                if aml.currency_id != report_currency:
                    amount = aml.currency_id._convert(
                        amount, report_currency, company,
                        aml.date or fields.Date.today()
                    )

                fake_id = -aml.move_id.id
                grouped_data[fake_id] = {
                    "move_name": aml.move_id.name,
                    "balance": 0,
                    "total": -amount,
                    "lines": [],
                    "factura_agregada": False,
                    "tipo": "remanente",
                }
                grouped_data[fake_id]["lines"].append({
                    "date": aml.date.strftime('%d/%m/%Y') if aml.date else '',
                    "ref": aml.move_id.ref,
                    "counter_move_ref": aml.move_id.name,
                    "line_name": "CRÉDITO A FAVOR (Remanente no aplicado)",
                    "journal_code": aml.journal_id.code,
                    "amount": -amount,
                    "currency_id": report_currency.id,
                    "invoice_number_next": "",
                    "invoice_number_control": "",
                    "is_payment": True,
                    "is_invoice": False,
                    "tipo": "remanente",
                })
                grouped_data[fake_id]["total"] = -amount
                    # ---- FILTRO: SOLO FACTURAS PENDIENTES ----
        if self.only_pending:
            grouped_data = {
                k: v for k, v in grouped_data.items()
                if abs(v.get('total', 0.0)) > 0.001
            }
            _logger.info("Filtro 'solo pendientes' aplicado. Grupos restantes: %s",
                         len(grouped_data))
            
        _logger.info("=== _get_data END === grupos=%s totales=%s",
             len(grouped_data),
             {k: round(v.get('total', 0.0), 2) for k, v in grouped_data.items()})
        return grouped_data


        
    def _get_invoice_payments(self, invoice):
        payments = []
        account_type = self.account_type
        _logger.info("=== _get_invoice_payments para factura %s (account_type=%s) ===",
                     invoice.name, account_type)
    
        invoice_line_ids = invoice.line_ids.ids
        if not invoice_line_ids:
            _logger.warning("Factura %s no tiene líneas.", invoice.name)
            return payments
    
        reconciles = self.env['account.partial.reconcile'].search([
            '|',
            ('debit_move_id', 'in', invoice_line_ids),
            ('credit_move_id', 'in', invoice_line_ids),
        ])
    
        for rec in reconciles:
            _logger.info("Parcial id=%s amount=%s debit_ccy=%s credit_ccy=%s | "
                         "debit_move=%s(%s) credit_move=%s(%s)",
                         rec.id, rec.amount,
                         rec.debit_amount_currency, rec.credit_amount_currency,
                         rec.debit_move_id.move_id.name, rec.debit_move_id.move_id.move_type,
                         rec.credit_move_id.move_id.name, rec.credit_move_id.move_id.move_type)
    
            if rec.debit_move_id.move_id == invoice:
                payment_line = rec.credit_move_id
                amount = abs(rec.credit_amount_currency or rec.amount)
            elif rec.credit_move_id.move_id == invoice:
                payment_line = rec.debit_move_id
                amount = abs(rec.debit_amount_currency or rec.amount)
            else:
                continue
    
            if not payment_line:
                continue
    
            # Verificar que el parcial toque la cuenta del modo
            if (rec.debit_move_id.account_id.account_type != account_type and
                    rec.credit_move_id.account_id.account_type != account_type):
                _logger.info("Parcial %s descartado: no toca %s", rec.id, account_type)
                continue
    
            payment = payment_line.move_id
            if payment.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                continue
    
            if payment_line.currency_id != self.report_currency_id:
                amount = payment_line.currency_id._convert(
                    amount,
                    self.report_currency_id,
                    invoice.company_id,
                    payment.date or fields.Date.today()
                )
    
            payments.append({
                'date': payment.date,
                'ref': payment.ref,
                'name': payment.name,
                'document_name': payment.name,
                'journal_code': payment.journal_id.code,
                'amount': amount,
                'currency_id': self.report_currency_id.id,
            })
            _logger.info("Pago %s aplicado a %s: %s", payment.name, invoice.name, amount)
    
        return payments

    def _get_debit_notes(self, invoice, invoice_types):
        debit_notes = []
        debit_moves = self.env['account.move'].search([
            ('partner_id', '=', invoice.partner_id.id),
            ('move_type', 'in', invoice_types),
            ('state', '=', 'posted'),
            ('invoice_origin', '=', invoice.name),
            ('company_id', '=', invoice.company_id.id),
            ('name', 'like', 'NDD%'),
        ])
        for debit in debit_moves:
            amount = debit.amount_total
            if debit.currency_id != invoice.currency_id:
                amount = debit.currency_id._convert(
                    amount,
                    invoice.currency_id,
                    invoice.company_id,
                    debit.date or fields.Date.today()
                )
            debit_notes.append({
                'date': debit.date,
                'ref': debit.ref,
                'name': debit.name,
                'origin': debit.invoice_origin,
                'journal_code': debit.journal_id.code,
                'amount': amount,
                'currency_id': invoice.currency_id.id,
                'document_id': debit.id,
            })
        return debit_notes

    

    def _get_sql(self):
        return self._get_data()

    def _execute_sql(self):
        return list(self._get_data().values())

    def print_report(self):
        return self.env.ref(
            'balg_account_report_payable_receivable.action_account_payable_receivable_report_balg'
        ).report_action(self)

    def xls_report(self):
        return self.env.ref(
            'balg_account_report_payable_receivable.action_account_payable_receivable_report_xlsx_balg').report_action(self)


class ReportPayableReceivableBalg(models.AbstractModel):
    _name = "report.balg_account_report_payable_receivable.p_c_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report AR-CV BALG"

    def generate_xlsx_report(self, workbook, data, docs):
        sheet = workbook.add_worksheet('Payable/Receivable BALG')
    
        # --- FORMATOS ---
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#E6E6E6',
            'border': 1, 'font_size': 10, 'text_wrap': True,
        })
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy', 'border': 1, 'font_size': 10,
        })
        money_format = workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'font_size': 10,
        })
        money_negative_format = workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'font_size': 10,
            'font_color': '#FF0000',
        })
        text_format = workbook.add_format({
            'border': 1, 'font_size': 10,
        })
        total_format = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#FFFFCC',
            'border': 1, 'font_size': 10,
        })
        company_name_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'left',
        })
        company_address_format = workbook.add_format({
            'font_size': 10, 'align': 'left',
        })
        client_label_format = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'left',
        })
        client_data_format = workbook.add_format({
            'font_size': 10, 'align': 'left',
        })
        adeudado_label_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'left',
            'bg_color': '#FFFF00',
        })
        adeudado_data_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'left',
            'bg_color': '#FFFF00',
            'num_format': '#,##0.00',
        })
        factura_format = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'font_size': 10,
        })
        # 👇 NUEVO FORMATO para TOTAL GENERAL (abajo)
        total_general_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#FFFF00',
            'border': 2,
            'num_format': '#,##0.00',
            'align': 'right',
        })
        total_general_label_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#FFFF00',
            'border': 2,
            'align': 'left',
        })
    
        # --- OBTENER DATOS ---
        o = docs[0] if docs else None
        if not o:
            return
        company = o.company_id
        partner = o.partner_id
    
        # --- INSERTAR LOGO ---
        row_start = 0
        try:
            import os
            module_path = os.path.dirname(os.path.abspath(__file__))
            module_root = os.path.dirname(module_path)
            logo_filename = f"ceramicas_balgres_{company.id}.png"
            logo_path = os.path.join(module_root, 'static', 'img', logo_filename)
            
            if os.path.exists(logo_path):
                sheet.insert_image('A1', logo_path, {'x_scale': 0.5, 'y_scale': 0.5})
                row_start = 5
                _logger.info("Logo insertado desde archivo físico: %s", logo_path)
            else:
                _logger.info("No existe logo físico para la empresa ID %s. Se genera reporte sin logo.", company.id)
                row_start = 0
        except Exception as e:
            _logger.warning("Error al insertar logo desde archivo: %s", e)
            row_start = 0
    
        # --- DATOS DE LA EMPRESA ---
        _logger.info("=== DATOS DE EMPRESA ===")
        _logger.info("row_start: %s", row_start)
        _logger.info("Nombre empresa: %s", company.name)
        _logger.info("Partner ID: %s", company.partner_id.id if company.partner_id else None)
        
        sheet.merge_range(row_start, 0, row_start, 2, company.name or 'Mi Empresa', company_name_format)
        
        if company.partner_id and company.partner_id.street:
            _logger.info("Dirección: %s", company.partner_id.street)
            sheet.merge_range(row_start + 1, 0, row_start + 1, 3, company.partner_id.street, company_address_format)
        else:
            _logger.warning("La empresa no tiene dirección registrada.")
        
        address_parts = []
        if company.partner_id and company.partner_id.city:
            address_parts.append(company.partner_id.city)
        if company.partner_id and company.partner_id.state_id:
            address_parts.append(company.partner_id.state_id.name)
        if company.partner_id and company.partner_id.country_id:
            address_parts.append(company.partner_id.country_id.name)
        if company.partner_id and company.partner_id.phone:
            address_parts.append('Tel: ' + company.partner_id.phone)
        address_line = ', '.join(address_parts)
        if address_line:
            _logger.info("Línea de dirección: %s", address_line)
            sheet.merge_range(row_start + 2, 0, row_start + 2, 3, address_line, company_address_format)
        else:
            _logger.warning("No se pudo construir la línea de dirección (faltan datos).")
    
                # --- DATOS DEL CLIENTE ---
        row_client = row_start + 4
        rif = partner.vat or ''
        import re
        rif_clean = re.sub(r'^[JVE]', '', rif) if rif else ''
    
        def write_client_line(label, value, row, col_label=0, col_data=1, label_format=None, data_format=None):
            if value:
                label_fmt = label_format if label_format else client_label_format
                data_fmt = data_format if data_format else client_data_format
                sheet.write(row, col_label, label, label_fmt)
                sheet.write(row, col_data, value, data_fmt)
                return row + 1
            return row
    
        row_client = write_client_line('Cliente:', partner.name or '', row_client)
        row_client = write_client_line('RIF:', rif_clean, row_client)
        row_client = write_client_line('Fecha de Emisión:', o.emission_date.strftime('%d/%m/%Y') if o.emission_date else '', row_client)
        if partner and partner.street:
            row_client = write_client_line('Dirección:', partner.street, row_client)
        if partner and partner.phone:
            row_client = write_client_line('Teléfono:', partner.phone, row_client)
        if partner and partner.mobile:
            row_client = write_client_line('Móvil:', partner.mobile, row_client)
        if partner and partner.email:
            row_client = write_client_line('Correo:', partner.email, row_client)

        # --- CÁLCULO DEL TOTAL ADEUDADO (restando solo huérfanas) ---
        total_adeudado = 0.0
        total_rectificativas_huerfanas = 0.0
        for move_id, counter_move in o._get_sql().items():
            if counter_move.get('tipo') == 'remanente':
                continue
            total_adeudado += counter_move.get('total', 0.0)
            for line in counter_move.get('lines', []):
                if line.get('tipo') == 'rectificativa_huerfana':
                    total_rectificativas_huerfanas += abs(line.get('amount', 0))
        total_adeudado -= total_rectificativas_huerfanas

        # --- SALDO EN EL ENCABEZADO (duplicado) ---
        sheet.write(row_client, 0, 'Saldo:', adeudado_label_format)
        sheet.write(row_client, 1, total_adeudado, adeudado_data_format)
        row_client += 1  # avanzar una fila

        # --- DEFINIR INICIO DE LA TABLA (después del saldo) ---
        table_start_row = row_client
    
        # --- TABLA DE DATOS ---
        row = table_start_row
        headers = ['Fecha', 'Nro. Ref', 'Descripción ', 'Monto']
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_format)
        row += 1
    
        max_widths = [len(h) for h in headers]
    
        # --- BUCLE DE DATOS ---
        for move_id, counter_move in o._get_sql().items():
            for line in counter_move['lines']:
                # Fecha
                date_val = line.get('date')
                if date_val:
                    sheet.write(row, 0, date_val, date_format)
                else:
                    sheet.write(row, 0, '', text_format)
                if max_widths[0] < 12:
                    max_widths[0] = 12
    
                # Nro. Ref
                ref_num = str(line.get('invoice_number_next', ''))
                sheet.write(row, 1, ref_num, text_format)
                max_widths[1] = max(max_widths[1], len(ref_num))
    
                # Concepto
                concepto = str(line.get('line_name', ''))
                if line.get('ref'):
                    concepto += ' (' + line.get('ref') + ')'
                sheet.write(row, 2, concepto, text_format)
                max_widths[2] = max(max_widths[2], len(concepto))
    
                # Monto
                amount = line.get('amount', 0)
                if amount < 0:
                    sheet.write(row, 3, amount, money_negative_format)
                else:
                    sheet.write(row, 3, amount, money_format)
                max_widths[3] = max(max_widths[3], len(f"{amount:.2f}"))
                row += 1
    
            # Total de la factura (o Saldo a favor/Saldada)
            if counter_move['total'] < 0:
                sheet.write(row, 0, 'Saldo a favor (Crédito)', total_format)
                sheet.write(row, 3, counter_move['total'], money_negative_format)
            elif counter_move['total'] == 0:
                sheet.write(row, 0, 'Saldada', total_format)
                sheet.write(row, 3, 0.0, money_format)
            else:
                sheet.write(row, 0, 'Total', total_format)
                sheet.write(row, 3, counter_move['total'], money_format)
                
            if max_widths[0] < 5:
                max_widths[0] = 5
            row += 2
    
        # 👇 TOTAL GENERAL AL FINAL DE LA TABLA
        if row > table_start_row + 1:
            sheet.write(row, 0, 'TOTAL GENERAL', total_general_label_format)
            sheet.write(row, 3, total_adeudado, total_general_format)
            row += 1
    
        # --- AUTO-AJUSTE DE ANCHOS ---
        for col, width in enumerate(max_widths):
            adjusted_width = min(width + 2, 50)
            sheet.set_column(col, col, adjusted_width)