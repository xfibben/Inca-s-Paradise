from odoo import fields, models


class IncasCatalogoVehiculoCaracteristica(models.Model):
    _name = "incas.catalogo.vehiculo.caracteristica"
    _description = "Característica de vehículo"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    vehiculo_id = fields.Many2one(
        "incas.catalogo.vehiculo",
        string="Vehículo",
        required=True,
        ondelete="cascade",
    )
    titulo = fields.Char(string="Título", required=True)
    descripcion = fields.Text(string="Descripción")
