from odoo import fields, models


class IncasHorarioOpcion(models.Model):
    _name = "incas.horario.opcion"
    _description = "Horario disponible por servicio"
    _order = "sequence, id"

    name = fields.Char(string="Horario", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    servicio_id = fields.Many2one(
        "incas.servicio.catalogo",
        string="Servicio",
        required=True,
        ondelete="cascade",
        index=True,
    )

    _incas_horario_opcion_unique = models.Constraint(
        "UNIQUE(servicio_id, name)",
        "El horario ya existe para este servicio.",
    )
