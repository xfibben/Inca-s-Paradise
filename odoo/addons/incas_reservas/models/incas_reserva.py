from odoo import api, fields, models


class IncasReserva(models.Model):
    _name = "incas.reserva"
    _description = "Reserva"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Código", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    cotizacion_id = fields.Many2one("incas.cotizacion", string="Cotización", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente principal", required=True, tracking=True)
    fecha_reserva = fields.Date(string="Fecha de reserva", default=fields.Date.context_today, required=True, tracking=True)
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
    monto_pagado = fields.Float(string="Monto pagado", tracking=True)
    saldo_pendiente = fields.Float(string="Saldo pendiente", compute="_compute_saldo_pendiente", store=True)
    estado_reserva = fields.Selection(
        [
            ("reservado", "Reservado"),
            ("por_coordinar", "Por coordinar"),
            ("falta_pago", "Falta pago"),
            ("pagado", "Pagado"),
            ("completado", "Completado"),
            ("finalizado", "Finalizado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado de reserva",
        required=True,
        default="reservado",
        tracking=True,
    )
    estado_pago = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("parcial", "Parcial"),
            ("pagado", "Pagado"),
            ("reembolsado", "Reembolsado"),
        ],
        string="Estado de pago",
        required=True,
        default="pendiente",
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    observaciones = fields.Text(string="Observaciones")
    pasajero_ids = fields.One2many("incas.pasajero", "reserva_id", string="Pasajeros")
    active = fields.Boolean(default=True)

    @api.depends("cantidad_adultos", "cantidad_ninos", "pasajero_ids")
    def _compute_cantidad_pasajeros(self):
        for record in self:
            if record.pasajero_ids:
                record.cantidad_pasajeros = len(record.pasajero_ids)
            else:
                record.cantidad_pasajeros = (record.cantidad_adultos or 0) + (record.cantidad_ninos or 0) or record.cotizacion_id.cantidad_pasajeros or 1

    @api.depends("cantidad_adultos", "cantidad_ninos", "precio_adulto", "precio_nino", "descuento")
    def _compute_monto_total(self):
        for record in self:
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.monto_total = subtotal - descuento_monto

    @api.depends("monto_total", "monto_pagado")
    def _compute_saldo_pendiente(self):
        for record in self:
            record.saldo_pendiente = record.monto_total - record.monto_pagado

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

    @api.onchange("cotizacion_id")
    def _onchange_cotizacion_id(self):
        for record in self:
            cotizacion = record.cotizacion_id
            if not cotizacion:
                continue
            record.partner_id = cotizacion.partner_id
            record.fecha_viaje = cotizacion.fecha_viaje
            record.idioma = cotizacion.idioma
            record.canal_venta = cotizacion.canal_venta
            record.tipo_servicio = cotizacion.tipo_servicio
            record.tipo_tour = cotizacion.tipo_tour
            record.estilo_transporte_id = cotizacion.estilo_transporte_id
            record.servicio_id = cotizacion.servicio_id
            record.servicio_nombre = cotizacion.servicio_nombre
            record.precio_adulto = cotizacion.precio_adulto
            record.precio_nino = cotizacion.precio_nino
            record.descuento = cotizacion.descuento
            record.cantidad_adultos = cotizacion.cantidad_adultos
            record.cantidad_ninos = cotizacion.cantidad_ninos
            record.moneda = cotizacion.moneda
            record.monto_total = cotizacion.monto_total
            record.responsable_id = cotizacion.responsable_id
            record.observaciones = cotizacion.observaciones

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.reserva") or "Nuevo"
        return super().create(vals_list)
