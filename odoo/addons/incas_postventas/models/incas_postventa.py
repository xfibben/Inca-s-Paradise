from odoo import api, fields, models


class IncasPostventa(models.Model):
    _name = "incas.postventa"
    _description = "Postventa legado"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_apertura desc, id desc"

    name = fields.Char(string="Codigo", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    caso_id = fields.Many2one("incas.postventa.caso", string="Caso post viaje", readonly=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    servicio_nombre = fields.Char(string="Servicio", tracking=True)
    ticket_reserva = fields.Char(string="Ticket reserva", tracking=True)
    tipo = fields.Selection(
        [
            ("seguimiento", "Seguimiento"),
            ("reclamo", "Reclamo"),
            ("queja", "Queja"),
            ("reembolso", "Reembolso"),
            ("documento", "Documento"),
            ("mejora", "Mejora"),
            ("otro", "Otro"),
        ],
        string="Tipo",
        required=True,
        default="seguimiento",
        tracking=True,
    )
    prioridad = fields.Selection(
        [
            ("baja", "Baja"),
            ("media", "Media"),
            ("alta", "Alta"),
            ("urgente", "Urgente"),
        ],
        string="Prioridad",
        required=True,
        default="media",
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("nuevo", "Nuevo"),
            ("seguimiento", "En seguimiento"),
            ("resuelto", "Resuelto"),
            ("cerrado", "Cerrado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        required=True,
        default="nuevo",
        tracking=True,
    )
    fecha_apertura = fields.Datetime(string="Fecha de apertura", default=fields.Datetime.now, required=True, tracking=True)
    fecha_limite = fields.Date(string="Fecha limite", tracking=True)
    fecha_cierre = fields.Datetime(string="Fecha de cierre", readonly=True, tracking=True)
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    satisfaccion = fields.Selection(
        [
            ("muy_baja", "Muy baja"),
            ("baja", "Baja"),
            ("media", "Media"),
            ("alta", "Alta"),
            ("muy_alta", "Muy alta"),
        ],
        string="Satisfaccion",
        tracking=True,
    )
    descripcion = fields.Text(string="Descripcion")
    solucion = fields.Text(string="Solucion")
    active = fields.Boolean(default=True)

    @api.onchange("reserva_id")
    def _onchange_reserva_id(self):
        for record in self:
            if not record.reserva_id:
                continue
            record.partner_id = record.reserva_id.partner_id
            record.servicio_nombre = record.reserva_id.servicio_nombre
            record.ticket_reserva = record.reserva_id.ticket or record.reserva_id.name

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        caso_model = self.env["incas.postventa.caso"]
        for record in records:
            if record.name == "Nuevo":
                record.name = self.env["ir.sequence"].next_by_code("incas.postventa.caso") or "Nuevo"
            if record.reserva_id:
                caso = caso_model.search([("reserva_id", "=", record.reserva_id.id)], limit=1)
                if not caso:
                    caso = caso_model.create({"reserva_id": record.reserva_id.id, "observaciones": record.descripcion})
                record.caso_id = caso
        return records

    def action_abrir_caso_nuevo(self):
        self.ensure_one()
        caso = self.caso_id
        if not caso and self.reserva_id:
            caso = self.env["incas.postventa.caso"].create({"reserva_id": self.reserva_id.id})
        return {
            "type": "ir.actions.act_window",
            "name": "Caso post viaje",
            "res_model": "incas.postventa.caso",
            "view_mode": "form",
            "res_id": caso.id if caso else False,
        }
