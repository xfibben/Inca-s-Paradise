from odoo import api, fields, models


class IncasCotizacion(models.Model):
    _name = "incas.cotizacion"
    _description = "Cotización"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Código", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente principal", required=True, tracking=True)
    fecha_cotizacion = fields.Date(string="Fecha de cotización", default=fields.Date.context_today, required=True, tracking=True)
    fecha_viaje = fields.Date(string="Fecha de viaje", tracking=True)
    idioma = fields.Selection(
        [
            ("es", "Español"),
            ("en", "Inglés"),
            ("pt", "Portugués"),
            ("fr", "Francés"),
            ("it", "Italiano"),
        ],
        string="Idioma",
        required=True,
        default="es",
        tracking=True,
    )
    canal_venta = fields.Selection(
        [
            ("web", "Web"),
            ("whatsapp", "WhatsApp"),
            ("correo", "Correo"),
            ("agencia", "Agencia"),
            ("oficina", "Oficina"),
            ("otro", "Otro"),
        ],
        string="Canal",
        required=True,
        default="web",
        tracking=True,
    )
    tipo_servicio = fields.Selection(
        [
            ("tour", "Tour"),
            ("transporte", "Transporte"),
        ],
        string="Tour o transporte",
        required=True,
        tracking=True,
    )
    tipo_tour = fields.Selection(
        [
            ("tour", "Tour"),
            ("small_trip", "Small Trip"),
            ("package", "Package"),
        ],
        string="Tipo de tour",
        tracking=True,
    )
    estilo_transporte_id = fields.Many2one("incas.estilo.transporte", string="Estilo de transporte", tracking=True)
    servicio_id = fields.Many2one(
        "incas.servicio.catalogo",
        string="Servicio",
        domain="[('tipo_servicio', '=', tipo_servicio), '|', ('tipo_tour', '=', False), ('tipo_tour', '=', tipo_tour), '|', ('estilo_transporte_id', '=', False), ('estilo_transporte_id', '=', estilo_transporte_id)]",
        tracking=True,
    )
    servicio_nombre = fields.Char(string="Nombre del servicio", required=True, tracking=True)
    precio_adulto = fields.Float(string="Precio adulto", tracking=True)
    precio_nino = fields.Float(string="Precio niño", tracking=True)
    descuento = fields.Float(string="Descuento", tracking=True)
    cantidad_adultos = fields.Integer(string="Cantidad adultos", default=1, required=True, tracking=True)
    cantidad_ninos = fields.Integer(string="Cantidad niños", default=0, required=True, tracking=True)
    cantidad_pasajeros = fields.Integer(string="Cantidad de pasajeros", compute="_compute_cantidad_pasajeros", store=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="PEN",
        tracking=True,
    )
    monto_total = fields.Float(string="Monto total", compute="_compute_monto_total", store=True, tracking=True)
    state = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("enviada", "Enviada"),
            ("aprobada", "Aprobada"),
            ("rechazada", "Rechazada"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado",
        required=True,
        default="borrador",
        tracking=True,
    )
    observaciones = fields.Text(string="Observaciones")
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    reserva_ids = fields.One2many("incas.reserva", "cotizacion_id", string="Reservas")
    reserva_count = fields.Integer(string="Cantidad de reservas", compute="_compute_reserva_count")

    @api.depends("reserva_ids")
    def _compute_reserva_count(self):
        for record in self:
            record.reserva_count = len(record.reserva_ids)

    @api.depends("cantidad_adultos", "cantidad_ninos")
    def _compute_cantidad_pasajeros(self):
        for record in self:
            record.cantidad_pasajeros = (record.cantidad_adultos or 0) + (record.cantidad_ninos or 0)

    @api.depends("cantidad_adultos", "cantidad_ninos", "precio_adulto", "precio_nino", "descuento")
    def _compute_monto_total(self):
        for record in self:
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.monto_total = subtotal - descuento_monto

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.cotizacion") or "Nuevo"
        return super().create(vals_list)

    @api.onchange("tipo_servicio")
    def _onchange_tipo_servicio(self):
        for record in self:
            record.servicio_id = False
            record.servicio_nombre = False
            record.precio_adulto = 0
            record.precio_nino = 0
            record.descuento = 0
            if record.tipo_servicio == "tour":
                record.estilo_transporte_id = False
                if not record.tipo_tour:
                    record.tipo_tour = "tour"
            elif record.tipo_servicio == "transporte":
                record.tipo_tour = False
                record.estilo_transporte_id = False

    @api.onchange("tipo_tour", "estilo_transporte_id")
    def _onchange_tipo_detalle_servicio(self):
        for record in self:
            record.servicio_id = False
            record.servicio_nombre = False
            record.precio_adulto = 0
            record.precio_nino = 0
            record.descuento = 0

    @api.onchange("servicio_id")
    def _onchange_servicio_id(self):
        for record in self:
            if not record.servicio_id:
                continue
            record.tipo_servicio = record.servicio_id.tipo_servicio
            record.tipo_tour = record.servicio_id.tipo_tour
            record.estilo_transporte_id = record.servicio_id.estilo_transporte_id
            record.servicio_nombre = record.servicio_id.name
            record.precio_adulto = record.servicio_id.precio_adulto
            record.precio_nino = record.servicio_id.precio_nino
            record.descuento = record.servicio_id.descuento

    def action_marcar_enviada(self):
        self.write({"state": "enviada"})

    def action_marcar_aprobada(self):
        self.write({"state": "aprobada"})

    def action_marcar_rechazada(self):
        self.write({"state": "rechazada"})

    def action_cancelar(self):
        self.write({"state": "cancelada"})
