from odoo import api, fields, models


class IncasTourHorario(models.Model):
    _name = "incas.tour.horario"
    _description = "Horario de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    tour_id = fields.Many2one("incas.tour", string="Tour", required=True, ondelete="cascade")
    horario_inicial = fields.Char(string="Horario inicial")
    horario_final = fields.Char(string="Horario final")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped("tour_id")._sincronizar_servicio_operativo()
        return records

    def write(self, vals):
        result = super().write(vals)
        self.mapped("tour_id")._sincronizar_servicio_operativo()
        return result

    def unlink(self):
        tours = self.mapped("tour_id")
        result = super().unlink()
        tours._sincronizar_servicio_operativo()
        return result
