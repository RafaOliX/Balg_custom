from odoo import api, models, _
from odoo.exceptions import ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.constrains('employee_id', 'date_from', 'date_to', 'state')
    def _check_duplicate_payslip(self):
        for record in self:
            # Ignoramos los recibos cancelados
            if record.state == 'cancel':
                continue

            # Buscamos otros recibos para el mismo empleado que se solapen en fechas
            domain = [
                ('id', '!=', record.id),  # Excluimos el recibo actual
                ('employee_id', '=', record.employee_id.id),
                ('state', '!=', 'cancel'), # Ignoramos los cancelados
                ('date_from', '<=', record.date_to),
                ('date_to', '>=', record.date_from),
            ]
            duplicate = self.search(domain, limit=1)
            if duplicate:
                raise ValidationError(
                    _("¡Error! Ya existe una nómina para el empleado %s en el período del %s al %s. "
                      "No se puede crear otra nómina en el mismo rango de fechas.")
                    % (record.employee_id.name, record.date_from, record.date_to)
                )