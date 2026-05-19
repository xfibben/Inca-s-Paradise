from odoo import fields, models


class IncasHistorialTour(models.Model):
    _name = "incas.historial.tour"
    _description = "Historial de tours"
    _order = "id desc"

    nombre_tour = fields.Char(string="Nombre de tour", required=True)
    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        related="create_uid",
        store=True,
        readonly=True,
    )
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
