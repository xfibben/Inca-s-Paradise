from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasPostventaCaso(models.Model):
    _name = "incas.postventa.caso"
    _description = "Caso post viaje"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_apertura desc, id desc"

    name = fields.Char(string="Codigo", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva vinculada", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    servicio_nombre = fields.Char(string="Servicio / tour", tracking=True)
    fecha_inicio = fields.Date(string="Fecha de salida", tracking=True)
    fecha_fin = fields.Date(string="Fecha de retorno", tracking=True)
    fecha_viaje = fields.Date(string="Fecha de viaje", tracking=True)
    canal_venta = fields.Selection(
        [
            ("web", "Web"),
            ("whatsapp", "WhatsApp"),
            ("correo", "Correo"),
            ("agencia", "Agencia"),
            ("oficina", "Oficina"),
            ("referido", "Referido"),
            ("otro", "Otro"),
        ],
        string="Canal de venta",
        default="web",
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("encuesta_enviada", "Encuesta enviada"),
            ("encuesta_respondida", "Encuesta respondida"),
            ("en_revision", "En revision"),
            ("cerrado", "Cerrado"),
        ],
        string="Estado postventa",
        default="pendiente",
        required=True,
        tracking=True,
    )
    fecha_apertura = fields.Datetime(string="Fecha de apertura", default=fields.Datetime.now, required=True, tracking=True)
    fecha_cierre = fields.Datetime(string="Fecha de cierre", readonly=True, tracking=True)
    observaciones = fields.Text(string="Observaciones")
    encuesta_ids = fields.One2many("incas.postventa.encuesta", "caso_id", string="Encuestas")
    reclamo_ids = fields.One2many("incas.postventa.reclamo", "caso_id", string="Reclamos")
    accion_ids = fields.One2many("incas.postventa.accion", "caso_id", string="Acciones correctivas")
    encuesta_count = fields.Integer(string="Nro. encuestas", compute="_compute_counts")
    reclamo_count = fields.Integer(string="Nro. reclamos", compute="_compute_counts")
    accion_count = fields.Integer(string="Acciones", compute="_compute_counts")
    active = fields.Boolean(default=True)

    @api.depends("encuesta_ids", "reclamo_ids", "accion_ids")
    def _compute_counts(self):
        for record in self:
            record.encuesta_count = len(record.encuesta_ids)
            record.reclamo_count = len(record.reclamo_ids)
            record.accion_count = len(record.accion_ids)

    def _values_from_reserva(self, reserva):
        return {
            "partner_id": reserva.partner_id.id,
            "servicio_nombre": reserva.servicio_nombre,
            "fecha_inicio": reserva.fecha_inicio,
            "fecha_fin": reserva.fecha_fin,
            "fecha_viaje": reserva.fecha_viaje,
            "canal_venta": reserva.canal_venta or "web",
            "responsable_id": reserva.responsable_id.id or self.env.user.id,
        }

    @api.onchange("reserva_id")
    def _onchange_reserva_id(self):
        for record in self:
            if record.reserva_id:
                for field_name, value in record._values_from_reserva(record.reserva_id).items():
                    record[field_name] = value

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.postventa.caso") or "Nuevo"
            reserva_id = vals.get("reserva_id")
            if reserva_id:
                if self.search_count([("reserva_id", "=", reserva_id)]):
                    raise ValidationError("Ya existe un caso postventa para esta reserva.")
                reserva = self.env["incas.reserva"].browse(reserva_id)
                if reserva.exists():
                    for field_name, value in self._values_from_reserva(reserva).items():
                        vals.setdefault(field_name, value)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("estado") == "cerrado" and not vals.get("fecha_cierre"):
            vals["fecha_cierre"] = fields.Datetime.now()
        if vals.get("estado") != "cerrado":
            vals["fecha_cierre"] = False
        return super().write(vals)

    def action_enviar_encuesta(self):
        for record in self:
            encuesta = record.encuesta_ids[:1]
            if not encuesta:
                encuesta = self.env["incas.postventa.encuesta"].create({"caso_id": record.id})
            encuesta.action_enviar()
            record.estado = "encuesta_enviada"
        return True

    def action_crear_reclamo(self):
        self.ensure_one()
        reclamo = self.env["incas.postventa.reclamo"].create({"caso_id": self.id})
        self.estado = "en_revision"
        return {
            "type": "ir.actions.act_window",
            "name": "Reclamo",
            "res_model": "incas.postventa.reclamo",
            "view_mode": "form",
            "res_id": reclamo.id,
        }

    def action_cerrar(self):
        self.write({"estado": "cerrado"})

    def action_ver_encuestas(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Encuestas",
            "res_model": "incas.postventa.encuesta",
            "view_mode": "list,form",
            "domain": [("caso_id", "=", self.id)],
            "context": {"default_caso_id": self.id},
        }

    def action_ver_reclamos(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reclamos",
            "res_model": "incas.postventa.reclamo",
            "view_mode": "list,form",
            "domain": [("caso_id", "=", self.id)],
            "context": {"default_caso_id": self.id},
        }

    def action_ver_acciones(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Acciones correctivas",
            "res_model": "incas.postventa.accion",
            "view_mode": "list,form",
            "domain": [("caso_id", "=", self.id)],
            "context": {"default_caso_id": self.id},
        }
