from odoo import fields, models


class IncasHistorialTour(models.Model):
    _name = "incas.historial.tour"
    _description = "Historial de tours"
    _order = "id desc"

    nombre_tour = fields.Char(string="Nombre de tour", required=True)
    enlace = fields.Char(string="Enlace")
    notas = fields.Text(string="Notas")
    estado = fields.Selection(
        selection=[
            ("modificado", "Modificado"),
            ("falta_modificar", "Falta modificar"),
        ],
        string="Estado",
        required=True,
        default="falta_modificar",
    )
