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
    hotel_linea_ids = fields.One2many("incas.cotizacion.hotel.linea", "cotizacion_id", string="Hoteles")
    extra_linea_ids = fields.One2many("incas.cotizacion.extra.linea", "cotizacion_id", string="Extras")
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
    hotel_id = fields.Many2one("incas.hotel", string="Hotel", tracking=True)
    hotel_tarifa_id = fields.Many2one(
        "incas.hotel.tarifa",
        string="Tarifa de hotel",
        domain="[('hotel_id', '=', hotel_id)]",
        tracking=True,
    )
    fecha_check_in = fields.Date(string="Check-in", tracking=True)
    fecha_check_out = fields.Date(string="Check-out", tracking=True)
    cantidad_noches = fields.Integer(string="Cantidad noches", compute="_compute_cantidad_noches", store=True)
    cantidad_habitaciones = fields.Integer(string="Cantidad habitaciones", default=1, required=True, tracking=True)
    hotel_nombre = fields.Char(string="Nombre del hotel", tracking=True)
    hotel_precio_noche_usd = fields.Float(string="Precio noche hotel base USD", tracking=True)
    hotel_precio_noche = fields.Float(string="Precio noche hotel", tracking=True)
    hotel_descuento = fields.Float(string="Descuento hotel", tracking=True)
    monto_hotel_usd = fields.Float(string="Monto hotel USD", compute="_compute_monto_hotel", store=True)
    monto_hotel = fields.Float(string="Monto hotel", compute="_compute_monto_hotel", store=True, tracking=True)
    extra_id = fields.Many2one("incas.extra", string="Extra", tracking=True)
    extra_tarifa_id = fields.Many2one(
        "incas.extra.tarifa",
        string="Tarifa de extra",
        domain="[('extra_id', '=', extra_id)]",
        tracking=True,
    )
    extra_nombre = fields.Char(string="Nombre del extra", tracking=True)
    extra_unidad = fields.Selection(
        [("unidad", "Unidad"), ("persona", "Persona"), ("tramo", "Tramo"), ("dia", "Día")],
        string="Unidad extra",
        tracking=True,
    )
    cantidad_extra = fields.Integer(string="Cantidad extra", default=1, required=True, tracking=True)
    extra_precio_unitario_usd = fields.Float(string="Precio unitario extra base USD", tracking=True)
    extra_precio_unitario = fields.Float(string="Precio unitario extra", tracking=True)
    extra_descuento = fields.Float(string="Descuento extra", tracking=True)
    monto_extra_usd = fields.Float(string="Monto extra USD", compute="_compute_monto_extra", store=True)
    monto_extra = fields.Float(string="Monto extra", compute="_compute_monto_extra", store=True, tracking=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="USD",
        tracking=True,
    )
    precio_grupal = fields.Float(string="Precio grupal", compute="_compute_precio_grupal", inverse="_inverse_precio_grupal", store=True, tracking=True)
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

    @api.depends("fecha_check_in", "fecha_check_out")
    def _compute_cantidad_noches(self):
        for record in self:
            if record.fecha_check_in and record.fecha_check_out and record.fecha_check_out > record.fecha_check_in:
                record.cantidad_noches = (record.fecha_check_out - record.fecha_check_in).days
            else:
                record.cantidad_noches = 0

    @api.depends("cantidad_noches", "cantidad_habitaciones", "hotel_precio_noche_usd", "hotel_linea_ids.monto_hotel_usd", "hotel_linea_ids.monto_hotel")
    def _compute_monto_hotel(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if record.hotel_linea_ids:
                record.monto_hotel_usd = sum(record.hotel_linea_ids.mapped("monto_hotel_usd"))
                record.monto_hotel = sum(record.hotel_linea_ids.mapped("monto_hotel"))
            else:
                record.monto_hotel_usd = (record.cantidad_habitaciones or 0) * (record.cantidad_noches or 0) * (record.hotel_precio_noche_usd or 0)
                record.monto_hotel = record._convertir_desde_usd(record.monto_hotel_usd, record.moneda, rates)

    @api.depends("cantidad_extra", "extra_precio_unitario_usd", "extra_linea_ids.monto_extra_usd", "extra_linea_ids.monto_extra")
    def _compute_monto_extra(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if record.extra_linea_ids:
                record.monto_extra_usd = sum(record.extra_linea_ids.mapped("monto_extra_usd"))
                record.monto_extra = sum(record.extra_linea_ids.mapped("monto_extra"))
            else:
                record.monto_extra_usd = (record.cantidad_extra or 0) * (record.extra_precio_unitario_usd or 0)
                record.monto_extra = record._convertir_desde_usd(record.monto_extra_usd, record.moneda, rates)

    @api.depends(
        "cantidad_adultos",
        "cantidad_ninos",
        "precio_adulto",
        "precio_nino",
        "descuento",
        "paquete_linea_ids.precio_adulto_neto",
        "paquete_linea_ids.precio_nino_neto",
    )
    def _compute_precio_grupal(self):
        for record in self:
            record.precio_grupal = record._obtener_precio_grupal_actual()

    @api.depends("cantidad_adultos", "cantidad_ninos", "precio_adulto", "precio_nino", "descuento", "monto_hotel", "monto_extra")
    def _compute_monto_total(self):
        for record in self:
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.monto_total = (subtotal - descuento_monto) + (record.monto_hotel or 0) + (record.monto_extra or 0)

    def _obtener_precio_grupal_actual(self):
        self.ensure_one()
        if self.paquete_linea_ids:
            return sum(
                ((self.cantidad_adultos or 0) * (linea.precio_adulto_neto or 0))
                + ((self.cantidad_ninos or 0) * (linea.precio_nino_neto or 0))
                for linea in self.paquete_linea_ids
            )
        subtotal = ((self.cantidad_adultos or 0) * (self.precio_adulto or 0)) + ((self.cantidad_ninos or 0) * (self.precio_nino or 0))
        descuento_monto = subtotal * ((self.descuento or 0) / 100)
        return subtotal - descuento_monto

    # Reparte el total objetivo entre las líneas para que el paquete cierre con el nuevo precio grupal.
    def _inverse_precio_grupal(self):
        for record in self:
            if not record.paquete_linea_ids:
                continue
            cantidad_adultos = record.cantidad_adultos or 0
            cantidad_ninos = record.cantidad_ninos or 0
            if cantidad_adultos <= 0 and cantidad_ninos <= 0:
                continue
            total_objetivo = max(record.precio_grupal or 0, 0)
            suma_factores = sum(1 - ((linea.descuento or 0) / 100) for linea in record.paquete_linea_ids)
            if suma_factores <= 0:
                continue
            divisor = suma_factores * (cantidad_adultos + cantidad_ninos)
            if cantidad_ninos <= 0:
                divisor = suma_factores * cantidad_adultos
            if divisor <= 0:
                continue
            precio_comun = total_objetivo / divisor
            for linea in record.paquete_linea_ids:
                linea.write(
                    {
                        "precio_adulto": precio_comun,
                        "precio_nino": precio_comun if cantidad_ninos > 0 else 0,
                    }
                )

    def _convertir_desde_usd(self, monto_usd, moneda, rates):
        if moneda == "PEN":
            return monto_usd * rates["PEN"]
        if moneda == "EUR":
            return monto_usd * rates["EUR"]
        return monto_usd

    # Carga la tarifa al encabezado para que el hotel tenga precio separado del servicio.
    def _aplicar_tarifa_hotel(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if not record.hotel_tarifa_id:
                record.hotel_nombre = record.hotel_id.name or False
                record.hotel_precio_noche_usd = 0
                record.hotel_precio_noche = 0
                record.hotel_descuento = 0
                continue
            record.hotel_id = record.hotel_tarifa_id.hotel_id
            record.hotel_nombre = record.hotel_tarifa_id.hotel_id.name
            record.hotel_precio_noche_usd = record.hotel_tarifa_id.obtener_precio_noche_neto_usd()
            record.hotel_precio_noche = record._convertir_desde_usd(record.hotel_precio_noche_usd, record.moneda, rates)
            record.hotel_descuento = record.hotel_tarifa_id.descuento or 0

    def _aplicar_tarifa_extra(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if not record.extra_tarifa_id:
                record.extra_nombre = record.extra_id.name or False
                record.extra_unidad = False
                record.extra_precio_unitario_usd = 0
                record.extra_precio_unitario = 0
                record.extra_descuento = 0
                continue
            record.extra_id = record.extra_tarifa_id.extra_id
            record.extra_nombre = record.extra_tarifa_id.extra_id.name
            record.extra_unidad = record.extra_tarifa_id.unidad
            record.extra_precio_unitario_usd = record.extra_tarifa_id.obtener_precio_unitario_neto_usd()
            record.extra_precio_unitario = record._convertir_desde_usd(record.extra_precio_unitario_usd, record.moneda, rates)
            record.extra_descuento = record.extra_tarifa_id.descuento or 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.cotizacion") or "Nuevo"
            self._completar_datos_hotel(vals)
            self._completar_datos_extra(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._completar_datos_hotel(vals)
        self._completar_datos_extra(vals)
        result = super().write(vals)
        if "moneda" in vals:
            for linea in self.mapped("paquete_linea_ids"):
                linea._actualizar_precios_desde_usd(vals["moneda"])
            self.mapped("hotel_linea_ids")._actualizar_precio_desde_usd(vals["moneda"])
            self.mapped("extra_linea_ids")._actualizar_precio_desde_usd(vals["moneda"])
        return result

    @api.onchange("moneda")
    def _onchange_moneda(self):
        for record in self:
            record.paquete_linea_ids._actualizar_precios_desde_usd(record.moneda)
            record.hotel_linea_ids._actualizar_precio_desde_usd(record.moneda)
            record.extra_linea_ids._actualizar_precio_desde_usd(record.moneda)
            record.hotel_precio_noche = record._convertir_desde_usd(
                record.hotel_precio_noche_usd or 0,
                record.moneda,
                self.env["incas.servicio.catalogo"]._get_currency_rates(),
            )
            record.extra_precio_unitario = record._convertir_desde_usd(
                record.extra_precio_unitario_usd or 0,
                record.moneda,
                self.env["incas.servicio.catalogo"]._get_currency_rates(),
            )

    @api.onchange("hotel_id")
    def _onchange_hotel_id(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_tarifa_id.hotel_id != record.hotel_id:
                record.hotel_tarifa_id = False
            record.hotel_nombre = record.hotel_id.name or False
            if not record.hotel_id:
                record.hotel_tarifa_id = False
                record.hotel_precio_noche_usd = 0
                record.hotel_precio_noche = 0
                record.hotel_descuento = 0

    @api.onchange("hotel_tarifa_id")
    def _onchange_hotel_tarifa_id(self):
        self._aplicar_tarifa_hotel()
        for record in self:
            if record.hotel_tarifa_id:
                record.fecha_check_in = record.fecha_check_in or record.fecha_viaje or record.hotel_tarifa_id.fecha_desde
                record.fecha_check_out = record.fecha_check_out or record.hotel_tarifa_id.fecha_hasta

    @api.onchange("extra_id")
    def _onchange_extra_id(self):
        for record in self:
            if record.extra_tarifa_id and record.extra_tarifa_id.extra_id != record.extra_id:
                record.extra_tarifa_id = False
            record.extra_nombre = record.extra_id.name or False
            if not record.extra_id:
                record.extra_tarifa_id = False
                record.extra_unidad = False
                record.extra_precio_unitario_usd = 0
                record.extra_precio_unitario = 0
                record.extra_descuento = 0

    @api.onchange("extra_tarifa_id")
    def _onchange_extra_tarifa_id(self):
        self._aplicar_tarifa_extra()

    def _completar_datos_hotel(self, vals):
        hotel_id = vals.get("hotel_id")
        hotel_tarifa_id = vals.get("hotel_tarifa_id")
        if not hotel_id and not hotel_tarifa_id:
            return vals
        tarifa = self.env["incas.hotel.tarifa"].browse(hotel_tarifa_id) if hotel_tarifa_id else self.env["incas.hotel.tarifa"]
        hotel = self.env["incas.hotel"].browse(hotel_id) if hotel_id else tarifa.hotel_id
        if tarifa and tarifa.exists():
            vals.setdefault("hotel_id", tarifa.hotel_id.id)
            vals["hotel_nombre"] = tarifa.hotel_id.name
            vals["hotel_precio_noche_usd"] = tarifa.obtener_precio_noche_neto_usd()
            vals["hotel_descuento"] = tarifa.descuento or 0
            vals.setdefault("fecha_check_in", vals.get("fecha_viaje") or tarifa.fecha_desde)
            vals.setdefault("fecha_check_out", tarifa.fecha_hasta)
        elif hotel and hotel.exists():
            vals["hotel_nombre"] = hotel.name
        moneda = vals.get("moneda") or (self.moneda if len(self) == 1 else "USD") or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vals["hotel_precio_noche"] = self._convertir_desde_usd(vals.get("hotel_precio_noche_usd") or 0, moneda, rates)
        return vals

    def _completar_datos_extra(self, vals):
        extra_id = vals.get("extra_id")
        extra_tarifa_id = vals.get("extra_tarifa_id")
        if not extra_id and not extra_tarifa_id:
            return vals
        tarifa = self.env["incas.extra.tarifa"].browse(extra_tarifa_id) if extra_tarifa_id else self.env["incas.extra.tarifa"]
        extra = self.env["incas.extra"].browse(extra_id) if extra_id else tarifa.extra_id
        if tarifa and tarifa.exists():
            vals.setdefault("extra_id", tarifa.extra_id.id)
            vals["extra_nombre"] = tarifa.extra_id.name
            vals["extra_unidad"] = tarifa.unidad
            vals["extra_precio_unitario_usd"] = tarifa.obtener_precio_unitario_neto_usd()
            vals["extra_descuento"] = tarifa.descuento or 0
        elif extra and extra.exists():
            vals["extra_nombre"] = extra.name
        moneda = vals.get("moneda") or (self.moneda if len(self) == 1 else "USD") or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vals["extra_precio_unitario"] = self._convertir_desde_usd(vals.get("extra_precio_unitario_usd") or 0, moneda, rates)
        return vals

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
