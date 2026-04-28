from odoo import api, fields, models


class IncasPostventaAccion(models.Model):
    _name = "incas.postventa.accion"
    _description = "Accion correctiva postventa"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_compromiso asc, id desc"

    name = fields.Char(string="Codigo", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    caso_id = fields.Many2one("incas.postventa.caso", string="Caso post viaje", tracking=True)
    encuesta_id = fields.Many2one("incas.postventa.encuesta", string="Encuesta", tracking=True)
    reclamo_id = fields.Many2one("incas.postventa.reclamo", string="Reclamo", tracking=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    tipo = fields.Selection(
        [
            ("disculpa", "Disculpa"),
            ("devolucion", "Devolucion"),
            ("descuento", "Descuento"),
            ("reprogramacion", "Reprogramacion"),
            ("compensacion", "Compensacion"),
            ("llamada", "Llamada"),
            ("capacitacion", "Capacitacion interna"),
        ],
        string="Tipo de accion",
        default="llamada",
        required=True,
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    fecha_compromiso = fields.Date(string="Fecha compromiso", tracking=True)
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("ejecucion", "En ejecucion"),
            ("cumplida", "Cumplida"),
            ("cerrada", "Cerrada"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
        tracking=True,
    )
    resultado = fields.Selection(
        [
            ("solucionado", "Solucionado"),
            ("parcial", "Parcialmente solucionado"),
            ("no_procede", "No procede"),
        ],
        string="Resultado",
        tracking=True,
    )
    descripcion = fields.Text(string="Descripcion")
    evidencia = fields.Text(string="Evidencia")
    active = fields.Boolean(default=True)

    def _values_from_relations(self, vals):
        caso = self.env["incas.postventa.caso"].browse(vals.get("caso_id")) if vals.get("caso_id") else False
        encuesta = self.env["incas.postventa.encuesta"].browse(vals.get("encuesta_id")) if vals.get("encuesta_id") else False
        reclamo = self.env["incas.postventa.reclamo"].browse(vals.get("reclamo_id")) if vals.get("reclamo_id") else False
        source = reclamo if reclamo and reclamo.exists() else encuesta if encuesta and encuesta.exists() else caso if caso and caso.exists() else False
        if not source:
            return {}
        values = {
            "partner_id": source.partner_id.id,
            "reserva_id": source.reserva_id.id,
        }
        if getattr(source, "caso_id", False):
            values["caso_id"] = source.caso_id.id
        return values

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.postventa.accion") or "Nuevo"
            for field_name, value in self._values_from_relations(vals).items():
                vals.setdefault(field_name, value)
        return super().create(vals_list)

    def action_ejecutar(self):
        self.write({"estado": "ejecucion"})

    def action_cumplir(self):
        self.write({"estado": "cumplida"})

    def action_cerrar(self):
        self.write({"estado": "cerrada"})

    def action_cancelar(self):
        self.write({"estado": "cancelada"})
