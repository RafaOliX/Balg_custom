import base64
import io
from datetime import datetime, time, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import re
import pytz

class AttendanceImportWizard(models.TransientModel):
    _name = 'attendance.import.wizard'
    _description = 'Asistente de Importación de Marcajes'

    file_1 = fields.Binary(string='Archivo Excel 1', required=True)
    file_1_name = fields.Char()
    file_2 = fields.Binary(string='Archivo Excel 2')
    file_2_name = fields.Char()
    anio = fields.Integer(string='Año', default=lambda self: fields.Date.today().year)
    mes = fields.Integer(string='Mes', default=lambda self: fields.Date.today().month)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    def action_import(self):
        self.ensure_one()
        
        company_env = self.env['hr.work.entry'].with_company(self.company_id)
        employee_env = self.env['hr.employee'].with_company(self.company_id)

        tz = pytz.timezone('America/Caracas')
        fecha_inicio_local = datetime(self.anio, self.mes, 1, 0, 0, 0)
        if self.mes == 12:
            fecha_fin_local = datetime(self.anio + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            fecha_fin_local = datetime(self.anio, self.mes + 1, 1, 0, 0, 0) - timedelta(seconds=1)

        start_utc = tz.localize(fecha_inicio_local).astimezone(pytz.utc).replace(tzinfo=None)
        end_utc = tz.localize(fecha_fin_local).astimezone(pytz.utc).replace(tzinfo=None)

        # 1. Limpiar entradas de la compañía seleccionada
        entradas_a_borrar = company_env.search([
            ('date_start', '>=', start_utc),
            ('date_start', '<=', end_utc),
            ('company_id', '=', self.company_id.id),
        ])
        
        if entradas_a_borrar:
            try:
                entradas_a_borrar.sudo().unlink()
            except Exception as e:
                raise UserError(_(f"No se pudieron borrar las entradas existentes. Detalle: {e}"))

        archivos = [self.file_1, self.file_2]
        total_creados = 0
        errores = []

        tipo_asistencia = self.env.ref('hr_work_entry.work_entry_type_attendance')

        for archivo_b64 in archivos:
            if not archivo_b64:
                continue
            
            file_data = base64.b64decode(archivo_b64)
            df = pd.read_excel(io.BytesIO(file_data), header=None, skiprows=6)

            for index, row in df.iterrows():
                emp_id_cell = row[0]
                if pd.isna(emp_id_cell):
                    continue
                
                try:
                    emp_id_str = str(int(emp_id_cell))
                except:
                    emp_id_str = str(emp_id_cell).strip()

                employee = employee_env.search([('registration_number', '=', emp_id_str)], limit=1)
                
                if not employee:
                    errores.append(f"ID: {emp_id_str}")
                    continue

                fecha_inicio_date = fecha_inicio_local.date()
                fecha_fin_date = fecha_fin_local.date()
                
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('date_start', '<=', fecha_fin_date),
                    '|', ('date_end', '=', False), ('date_end', '>=', fecha_inicio_date)
                ], limit=1)

                if not contract:
                    errores.append(f"Sin contrato: {employee.name}")
                    continue

                for dia in range(1, 32):
                    col_idx = dia + 2
                    if col_idx >= len(row):
                        break

                    cell_value = row[col_idx]
                    
                    if pd.notna(cell_value) and str(cell_value).strip() != "":
                        try:
                            fecha_base = datetime(self.anio, self.mes, dia).date()
                        except ValueError:
                            continue

                        texto_celda = str(cell_value).strip()
                        horas_encontradas = re.findall(r'\b([0-2]?[0-9]:[0-5][0-9])\b', texto_celda)
                        
                        hora_entrada = time(8, 0)
                        hora_salida = time(16, 0)

                        if len(horas_encontradas) >= 1:
                            h_ent, m_ent = map(int, horas_encontradas[0].split(':'))
                            hora_entrada = time(h_ent, m_ent)
                            if len(horas_encontradas) == 1:
                                dt_entrada = datetime.combine(fecha_base, hora_entrada)
                                dt_salida = dt_entrada + timedelta(hours=8)
                                hora_salida = dt_salida.time()

                        if len(horas_encontradas) >= 2:
                            h_sal, m_sal = map(int, horas_encontradas[-1].split(':'))
                            hora_salida = time(h_sal, m_sal)

                        local_start = tz.localize(datetime.combine(fecha_base, hora_entrada))
                        local_stop = tz.localize(datetime.combine(fecha_base, hora_salida))

                        if local_stop <= local_start:
                            local_stop += timedelta(days=1)

                        date_start = local_start.astimezone(pytz.utc).replace(tzinfo=None)
                        date_stop = local_stop.astimezone(pytz.utc).replace(tzinfo=None)

                        duration = (date_stop - date_start).total_seconds() / 3600.0

                        try:
                            with self.env.cr.savepoint():
                                company_env.create({
                                    'name': f'Asistencia {fecha_base}',
                                    'employee_id': employee.id,
                                    'contract_id': contract.id,
                                    'department_id': employee.department_id.id,
                                    'date_start': date_start,
                                    'date_stop': date_stop,
                                    'work_entry_type_id': tipo_asistencia.id,
                                    'duration': duration,
                                    'company_id': self.company_id.id,
                                })
                                total_creados += 1
                        except Exception as e:
                            errores.append(f"Error BD {employee.name}: {str(e)}")

        # --- NOTIFICACIÓN FINAL (SIN GUARDAR EN ir.logging) ---
        if errores:
            # Mostramos una advertencia amarilla con los primeros 5 errores
            errores_msg = "\n".join(errores[:5])
            if len(errores) > 5:
                errores_msg += f"\n... y {len(errores) - 5} más."
                
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Importación Finalizada con Advertencias',
                    'message': f'Se guardaron {total_creados} asistencias.\n\nObservaciones:\n{errores_msg}',
                    'type': 'warning',
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        # Si todo salió perfecto, notificación verde
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Éxito!',
                'message': f'Se importaron correctamente {total_creados} asistencias.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }