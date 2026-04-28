from odoo import api, fields, models


class IncasPostventaReclamo(models.Model):
    _name = "incas.postventa.reclamo"
    _description = "Reclamo postventa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_registro desc, id desc"

    name = fields.Char(string="Codigo de reclamo", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    caso_id = fields.Many2one("incas.postventa.caso", string="Caso post viaje", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva relacionada", tracking=True)
    tipo = fields.Selection(
        [
            ("queja", "Queja"),
            ("reclamo", "Reclamo"),
            ("sugerencia", "Sugerencia"),
            ("incidente", "Incidente post viaje"),
        ],
        string="Tipo",
        default="reclamo",
        required=True,
        tracking=True,
    )
    motivo = fields.Selection(
        [
            ("servicio", "Servicio"),
            ("guia", "Guia"),
            ("transporte", "Transporte"),
            ("hotel", "Hotel"),
            ("retraso", "Retraso"),
            ("cobro", "Cobro"),
            ("atencion", "Atencion"),
            ("otro", "Otro"),
        ],
        string="Motivo",
        default="servicio",
        required=True,
        tracking=True,
    )
    descripcion = fields.Text(string="Descripcion")
    fecha_registro = fields.Datetime(string="Fecha de registro", default=fields.Datetime.now, required=True, tracking=True)
    canal = fields.Selection(
        [
            ("web", "Web"),
            ("oficina", "Oficina"),
            ("whatsapp", "WhatsApp"),
            ("correo", "Correo"),
            ("llamada", "Llamada"),
            ("otro", "Otro"),
        ],
        string="Canal",
        default="whatsapp",
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    prioridad = fields.Selection(
        [
            ("baja", "Baja"),
            ("media", "Media"),
            ("alta", "Alta"),
            ("critica", "Critica"),
        ],
        string="Prioridad",
        default="media",
        required=True,
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("nuevo", "Nuevo"),
            ("evaluacion", "En evaluacion"),
            ("proceso", "En proceso"),
            ("resuelto", "Resuelto"),
            ("cerrado", "Cerrado"),
        ],
        string="Estado",
        default="nuevo",
        required=True,
        tracking=True,
    )
    fecha_limite = fields.Date(string="Fecha limite", tracking=True)
    fecha_cierre = fields.Datetime(string="Fecha de cierre", readonly=True, tracking=True)
    respuesta_dada = fields.Text(string="Respuesta dada")
    accion_ids = fields.One2many("incas.postventa.accion", "reclamo_id", string="Acciones correctivas")
    active = fields.Boolean(default=True)

    def _values_from_caso(self, caso):
        return {
            "reserva_id": caso.reserva_id.id,
            "partner_id": caso.partner_id.id,
            "responsable_id": caso.responsable_id.id or self.env.user.id,
        }

    @api.onchange("caso_id")
    def _onchange_caso_id(self):
        for record in self:
            if record.caso_id:
                for field_name, value in record._values_from_caso(record.caso_id).items():
                    record[field_name] = value

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.postventa.reclamo") or "Nuevo"
            caso_id = vals.get("caso_id")
            if caso_id:
                caso = self.env["incas.postventa.caso"].browse(caso_id)
                if caso.exists():
                    for field_name, value in self._values_from_caso(caso).items():
                        vals.setdefault(field_name, value)
                    caso.estado = "en_revision"
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("estado") in {"resuelto", "cerrado"} and not vals.get("fecha_cierre"):
            vals["fecha_cierre"] = fields.Datetime.now()
        if vals.get("estado") in {"nuevo", "evaluacion", "proceso"}:
            vals["fecha_cierre"] = False
        return super().write(vals)

    def action_evaluar(self):
        self.write({"estado": "evaluacion"})

    def action_procesar(self):
        self.write({"estado": "proceso"})

    def action_resolver(self):
        self.write({"estado": "resuelto"})

    def action_cerrar(self):
        self.write({"estado": "cerrado"})

    def action_crear_accion_correctiva(self):
        self.ensure_one()
        accion = self.env["incas.postventa.accion"].create(
            {
                "caso_id": self.caso_id.id,
                "reclamo_id": self.id,
                "reserva_id": self.reserva_id.id,
                "partner_id": self.partner_id.id,
                "tipo": "llamada" if self.prioridad != "critica" else "compensacion",
                "responsable_id": self.responsable_id.id or self.env.user.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Accion correctiva",
            "res_model": "incas.postventa.accion",
            "view_mode": "form",
            "res_id": accion.id,
        }
