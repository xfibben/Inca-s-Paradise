from odoo import api, fields, models


class IncasAgendaEvento(models.Model):
    _name = "incas.agenda.evento"
    _description = "Evento de agenda operativa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_inicio asc, id desc"

    name = fields.Char(string="Título", required=True, tracking=True)
    tipo_evento = fields.Selection(
        [
            ("reserva", "Reserva"),
            ("reunion", "Reunión"),
            ("evento", "Evento"),
            ("bloqueo", "Bloqueo"),
        ],
        string="Tipo",
        required=True,
        default="evento",
        tracking=True,
    )
    fecha_inicio = fields.Datetime(string="Inicio", required=True, tracking=True)
    fecha_fin = fields.Datetime(string="Fin", tracking=True)
    all_day = fields.Boolean(string="Todo el día")
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", ondelete="set null", index=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", tracking=True)
    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("confirmado", "Confirmado"),
            ("en_progreso", "En progreso"),
            ("completado", "Completado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        required=True,
        default="pendiente",
        tracking=True,
    )
    notas = fields.Text(string="Notas")
    color = fields.Integer(string="Color")
    active = fields.Boolean(default=True)

    @api.model
    def action_sincronizar_reservas_calendario(self):
        reservas = self.env["incas.reserva"].sudo().search([])
        reservas._sincronizar_evento_operativo()
        return True
