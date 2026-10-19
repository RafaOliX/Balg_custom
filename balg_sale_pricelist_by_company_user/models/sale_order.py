from odoo import api, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id', 'company_id')
    def _compute_pricelist_id(self):
        # IDs fijos (los obtuviste de tus URLs)
        TARGET_COMPANY_ID = 2      # Ceramicas Balgres
        FIXED_PRICELIST_ID = 2     # Tarifa Divisa

        for order in self:
            # Si la empresa del presupuesto es Ceramicas Balgres (ID 2)
            if order.company_id.id == TARGET_COMPANY_ID:
                # Forzar la tarifa con ID 2
                fixed_pricelist = self.env['product.pricelist'].browse(FIXED_PRICELIST_ID)
                if fixed_pricelist.exists():
                    order.pricelist_id = fixed_pricelist
                else:
                    # Si por alguna razón no existe la tarifa, usar comportamiento nativo
                    super(SaleOrder, order)._compute_pricelist_id()
            else:
                # Para cualquier otra empresa, comportamiento nativo (tarifa del cliente)
                super(SaleOrder, order)._compute_pricelist_id()