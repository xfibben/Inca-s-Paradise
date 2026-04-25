from odoo import api, fields, models
from odoo.exceptions import UserError


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
            ("paquete", "Paquete"),
        ],
        string="Tour o transporte",
        required=True,
        default="paquete",
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
    paquete_linea_ids = fields.One2many("incas.cotizacion.paquete.linea", "cotizacion_id", string="Líneas del paquete")
    paquete_tour_ids = fields.Many2many(
        "incas.servicio.catalogo",
        "incas_cotizacion_paquete_tour_rel",
        "cotizacion_id",
        "servicio_id",
        string="Tours del paquete",
        domain="[('tipo_servicio', '=', 'tour')]",
    )
    paquete_transporte_ids = fields.Many2many(
        "incas.servicio.catalogo",
        "incas_cotizacion_paquete_transporte_rel",
        "cotizacion_id",
        "servicio_id",
        string="Transportes del paquete",
        domain="[('tipo_servicio', '=', 'transporte')]",
    )
    servicio_nombre = fields.Char(string="Nombre del servicio", compute="_compute_resumen_servicio", store=True, tracking=True)
    precio_adulto_usd = fields.Float(string="Precio adulto base USD", compute="_compute_resumen_servicio", store=True)
    precio_nino_usd = fields.Float(string="Precio niño base USD", compute="_compute_resumen_servicio", store=True)
    precio_adulto = fields.Float(string="Precio adulto", compute="_compute_resumen_servicio", store=True, tracking=True)
    precio_nino = fields.Float(string="Precio niño", compute="_compute_resumen_servicio", store=True, tracking=True)
    descuento = fields.Float(string="Descuento", compute="_compute_resumen_servicio", store=True, tracking=True)
    cantidad_adultos = fields.Integer(string="Cantidad adultos", default=1, required=True, tracking=True)
    cantidad_ninos = fields.Integer(string="Cantidad niños", default=0, required=True, tracking=True)
    cantidad_pasajeros = fields.Integer(string="Cantidad de pasajeros", compute="_compute_cantidad_pasajeros", store=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="USD",
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
    paquete_item_count = fields.Integer(string="Cantidad de items del paquete", compute="_compute_paquete_item_count")
    tiene_detalle_paquete = fields.Boolean(string="Tiene detalle de paquete", compute="_compute_paquete_item_count")

    def _get_resumen_servicio(self):
        self.ensure_one()
        if not self.paquete_linea_ids:
            return {
                "tipo_servicio": "paquete",
                "tipo_tour": False,
                "estilo_transporte_id": self.env["incas.estilo.transporte"],
                "servicio_id": self.env["incas.servicio.catalogo"],
                "servicio_nombre": False,
                "precio_adulto_usd": 0,
                "precio_nino_usd": 0,
                "precio_adulto": 0,
                "precio_nino": 0,
                "descuento": 0,
            }
        precio_adulto_usd = sum(self.paquete_linea_ids.mapped("precio_adulto_neto_usd"))
        precio_nino_usd = sum(self.paquete_linea_ids.mapped("precio_nino_neto_usd"))
        precio_adulto = sum(self.paquete_linea_ids.mapped("precio_adulto_neto"))
        precio_nino = sum(self.paquete_linea_ids.mapped("precio_nino_neto"))
        if len(self.paquete_linea_ids) == 1:
            linea = self.paquete_linea_ids[0]
            return {
                "tipo_servicio": linea.tipo_servicio,
                "tipo_tour": linea.tipo_tour,
                "estilo_transporte_id": linea.estilo_transporte_id,
                "servicio_id": linea.servicio_id,
                "servicio_nombre": self.servicio_nombre or linea.nombre,
                "precio_adulto_usd": precio_adulto_usd,
                "precio_nino_usd": precio_nino_usd,
                "precio_adulto": precio_adulto,
                "precio_nino": precio_nino,
                "descuento": linea.descuento,
            }
        return {
            "tipo_servicio": "paquete",
            "tipo_tour": False,
            "estilo_transporte_id": self.env["incas.estilo.transporte"],
            "servicio_id": self.env["incas.servicio.catalogo"],
            "servicio_nombre": self.servicio_nombre or "Paquete personalizado",
            "precio_adulto_usd": precio_adulto_usd,
            "precio_nino_usd": precio_nino_usd,
            "precio_adulto": precio_adulto,
            "precio_nino": precio_nino,
            "descuento": 0,
        }

    @api.depends("reserva_ids")
    def _compute_reserva_count(self):
        for record in self:
            record.reserva_count = len(record.reserva_ids)

    @api.depends("paquete_linea_ids")
    def _compute_paquete_item_count(self):
        for record in self:
            total = len(record.paquete_linea_ids)
            record.paquete_item_count = total
            record.tiene_detalle_paquete = total > 0

    @api.depends(
        "moneda",
        "paquete_linea_ids",
        "paquete_linea_ids.nombre",
        "paquete_linea_ids.tipo_servicio",
        "paquete_linea_ids.tipo_tour",
        "paquete_linea_ids.estilo_transporte_id",
        "paquete_linea_ids.servicio_id",
        "paquete_linea_ids.descuento",
        "paquete_linea_ids.precio_adulto_neto_usd",
        "paquete_linea_ids.precio_nino_neto_usd",
    )
    def _compute_resumen_servicio(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if not record.paquete_linea_ids:
                record.tipo_servicio = "paquete"
                record.tipo_tour = False
                record.estilo_transporte_id = False
                record.servicio_id = False
                record.servicio_nombre = False
                record.precio_adulto_usd = 0
                record.precio_nino_usd = 0
                record.precio_adulto = 0
                record.precio_nino = 0
                record.descuento = 0
                continue
            precio_adulto_usd = sum(record.paquete_linea_ids.mapped("precio_adulto_neto_usd"))
            precio_nino_usd = sum(record.paquete_linea_ids.mapped("precio_nino_neto_usd"))
            if len(record.paquete_linea_ids) == 1:
                linea = record.paquete_linea_ids[0]
                record.tipo_servicio = linea.tipo_servicio
                record.tipo_tour = linea.tipo_tour
                record.estilo_transporte_id = linea.estilo_transporte_id
                record.servicio_id = linea.servicio_id
                record.servicio_nombre = linea.nombre
                record.descuento = linea.descuento
            else:
                record.tipo_servicio = "paquete"
                record.tipo_tour = False
                record.estilo_transporte_id = False
                record.servicio_id = False
                record.servicio_nombre = "Paquete personalizado"
                record.descuento = 0
            record.precio_adulto_usd = precio_adulto_usd
            record.precio_nino_usd = precio_nino_usd
            record.precio_adulto = record._convertir_desde_usd(precio_adulto_usd, record.moneda, rates)
            record.precio_nino = record._convertir_desde_usd(precio_nino_usd, record.moneda, rates)

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

    def _convertir_desde_usd(self, monto_usd, moneda, rates):
        if moneda == "PEN":
            return monto_usd * rates["PEN"]
        if moneda == "EUR":
            return monto_usd * rates["EUR"]
        return monto_usd

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.cotizacion") or "Nuevo"
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if "moneda" in vals:
            for linea in self.mapped("paquete_linea_ids"):
                linea._actualizar_precios_desde_usd(vals["moneda"])
        return result

    @api.onchange("moneda")
    def _onchange_moneda(self):
        for record in self:
            record.paquete_linea_ids._actualizar_precios_desde_usd(record.moneda)

    def action_marcar_enviada(self):
        self.write({"state": "enviada"})

    def action_marcar_aprobada(self):
        self.write({"state": "aprobada"})

    def action_marcar_rechazada(self):
        self.write({"state": "rechazada"})

    def action_cancelar(self):
        self.write({"state": "cancelada"})

    def action_print_pdf(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/cotizacion/{self.id}/pdf",
            "target": "self",
        }

    def action_print_package_pdf(self):
        self.ensure_one()
        if not self.paquete_linea_ids:
            raise UserError("Selecciona al menos un tour o un transporte en la pestaña Paquete.")
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/cotizacion/{self.id}/detalle-paquete-pdf",
            "target": "self",
        }
