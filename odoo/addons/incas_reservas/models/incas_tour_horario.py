from odoo import fields, models


class IncasTourHorario(models.Model):
    _name = "incas.tour.horario"
    _description = "Horario de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    tour_id = fields.Many2one("incas.tour", string="Tour", required=True, ondelete="cascade")
    horario_inicial = fields.Char(string="Horario inicial")
    horario_final = fields.Char(string="Horario final")
