from odoo import api, models


class IncasPago(models.Model):
    _inherit = "incas.pago"

    @api.model_create_multi
    def create(self, vals_list):
        pagos = super().create(vals_list)
        pagos.mapped("reserva_id")._sincronizar_lineas_operacion()
        return pagos

    def write(self, vals):
        result = super().write(vals)
        self.mapped("reserva_id")._sincronizar_lineas_operacion()
        return result
