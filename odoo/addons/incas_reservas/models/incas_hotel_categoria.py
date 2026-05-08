from odoo import fields, models


class IncasHotelCategoria(models.Model):
    _name = "incas.hotel.categoria"
    _description = "Categoría de hotel"
    _order = "sequence, name, id"

    name = fields.Char(string="Nombre", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    active = fields.Boolean(default=True)
