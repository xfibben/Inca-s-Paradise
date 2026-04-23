from odoo import api, fields, models


class IncasPasajero(models.Model):
    _name = "incas.pasajero"
    _description = "Pasajero"
    _order = "apellidos, nombres"
    _rec_name = "name"

    name = fields.Char(string="Nombre completo", compute="_compute_name", store=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade")
    nombres = fields.Char(string="Nombres", required=True)
    apellidos = fields.Char(string="Apellidos", required=True)
    tipo_documento = fields.Selection(
        [
            ("dni", "DNI"),
            ("ce", "CE"),
            ("pasaporte", "Pasaporte"),
            ("otro", "Otro"),
        ],
        string="Tipo de documento",
    )
    numero_documento = fields.Char(string="Número de documento")
    nacionalidad = fields.Char(string="Nacionalidad")
    fecha_nacimiento = fields.Date(string="Fecha de nacimiento")
    email = fields.Char(string="Correo")
    telefono = fields.Char(string="Teléfono")
    observaciones = fields.Text(string="Observaciones")

    @api.depends("nombres", "apellidos")
    def _compute_name(self):
        for record in self:
            record.name = " ".join(part for part in [record.nombres, record.apellidos] if part)
