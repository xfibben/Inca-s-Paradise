from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasPostventaEncuesta(models.Model):
    _name = "incas.postventa.encuesta"
    _description = "Encuesta postventa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_envio desc, id desc"

    name = fields.Char(string="Codigo", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    caso_id = fields.Many2one("incas.postventa.caso", string="Caso post viaje", tracking=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    servicio_nombre = fields.Char(string="Servicio / tour", tracking=True)
    estado = fields.Selection(
        [
            ("no_enviada", "No enviada"),
            ("enviada", "Enviada"),
            ("respondida", "Respondida"),
            ("vencida", "Vencida"),
        ],
        string="Estado de encuesta",
        default="no_enviada",
        required=True,
        tracking=True,
    )
    fecha_envio = fields.Datetime(string="Fecha de envio", tracking=True)
    fecha_respuesta = fields.Datetime(string="Fecha de respuesta", tracking=True)
    fecha_recordatorio = fields.Datetime(string="Fecha de recordatorio", tracking=True)
    nps = fields.Integer(string="NPS / recomendacion")
    satisfaccion_general = fields.Integer(string="Satisfaccion general")
    puntualidad = fields.Integer(string="Puntualidad")
    atencion_guia = fields.Integer(string="Atencion del guia")
    transporte = fields.Integer(string="Transporte")
    comunicacion_previa = fields.Integer(string="Comunicacion previa")
    cumplimiento_itinerario = fields.Integer(string="Cumplimiento del itinerario")
    seguridad = fields.Integer(string="Seguridad")
    precio_calidad = fields.Integer(string="Relacion precio/calidad")
    comentario = fields.Text(string="Comentario libre")
    requiere_accion = fields.Boolean(string="Requiere accion", compute="_compute_requiere_accion", store=True)
    accion_ids = fields.One2many("incas.postventa.accion", "encuesta_id", string="Acciones correctivas")
    active = fields.Boolean(default=True)

    @api.depends("nps", "satisfaccion_general")
    def _compute_requiere_accion(self):
        for record in self:
            record.requiere_accion = bool((record.nps is not False and record.nps <= 6) or (record.satisfaccion_general and record.satisfaccion_general <= 2))

    @api.constrains("nps")
    def _check_nps(self):
        for record in self:
            if record.nps and (record.nps < 0 or record.nps > 10):
                raise ValidationError("El NPS debe estar entre 0 y 10.")

    @api.constrains(
        "satisfaccion_general",
        "puntualidad",
        "atencion_guia",
        "transporte",
        "comunicacion_previa",
        "cumplimiento_itinerario",
        "seguridad",
        "precio_calidad",
    )
    def _check_scores(self):
        fields_to_check = [
            "satisfaccion_general",
            "puntualidad",
            "atencion_guia",
            "transporte",
            "comunicacion_previa",
            "cumplimiento_itinerario",
            "seguridad",
            "precio_calidad",
        ]
        for record in self:
            for field_name in fields_to_check:
                value = record[field_name]
                if value and (value < 1 or value > 5):
                    raise ValidationError("Las calificaciones de satisfaccion deben estar entre 1 y 5.")

    def _values_from_caso(self, caso):
        return {
            "reserva_id": caso.reserva_id.id,
            "partner_id": caso.partner_id.id,
            "servicio_nombre": caso.servicio_nombre,
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
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.postventa.encuesta") or "Nuevo"
            caso_id = vals.get("caso_id")
            if caso_id:
                caso = self.env["incas.postventa.caso"].browse(caso_id)
                if caso.exists():
                    for field_name, value in self._values_from_caso(caso).items():
                        vals.setdefault(field_name, value)
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if vals.keys() & {
            "nps",
            "satisfaccion_general",
            "puntualidad",
            "atencion_guia",
            "transporte",
            "comunicacion_previa",
            "cumplimiento_itinerario",
            "seguridad",
            "precio_calidad",
            "comentario",
        }:
            for record in self:
                if record.estado != "respondida":
                    super(IncasPostventaEncuesta, record).write(
                        {
                            "estado": "respondida",
                            "fecha_respuesta": record.fecha_respuesta or fields.Datetime.now(),
                        }
                    )
                if record.caso_id and record.caso_id.estado != "en_revision":
                    record.caso_id.estado = "encuesta_respondida"
        return result

    def action_enviar(self):
        self.write({"estado": "enviada", "fecha_envio": fields.Datetime.now()})

    def action_recordatorio(self):
        self.write({"fecha_recordatorio": fields.Datetime.now()})

    def action_vencida(self):
        self.write({"estado": "vencida"})

    def action_crear_accion_correctiva(self):
        self.ensure_one()
        accion = self.env["incas.postventa.accion"].create(
            {
                "caso_id": self.caso_id.id,
                "encuesta_id": self.id,
                "reserva_id": self.reserva_id.id,
                "partner_id": self.partner_id.id,
                "tipo": "llamada",
                "responsable_id": self.caso_id.responsable_id.id or self.env.user.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Accion correctiva",
            "res_model": "incas.postventa.accion",
            "view_mode": "form",
            "res_id": accion.id,
        }
