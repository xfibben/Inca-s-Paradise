from odoo import api, fields, models


class IncasCotizacionHotelLinea(models.Model):
    _name = "incas.cotizacion.hotel.linea"
    _description = "Línea de hotel de cotización"
    _order = "sequence, id"

    cotizacion_id = fields.Many2one("incas.cotizacion", string="Cotización", required=True, ondelete="cascade")
    moneda = fields.Selection(related="cotizacion_id.moneda", string="Moneda", readonly=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    hotel_id = fields.Many2one("incas.hotel", string="Hotel", required=True)
    hotel_tarifa_id = fields.Many2one(
        "incas.hotel.tarifa",
        string="Tarifa de hotel",
        domain="[('hotel_id', '=', hotel_id)]",
    )
    tipo_tarifario = fields.Selection(
        [("ip", "IP"), ("conf", "CONF FIT"), ("fit", "Rack")],
        string="Tarifario",
        default="ip",
        required=True,
    )
    fecha_check_in = fields.Date(string="Check-in")
    fecha_check_out = fields.Date(string="Check-out")
    cantidad_noches = fields.Integer(string="Noches", default=1, required=True)
    cantidad_habitaciones = fields.Integer(string="Habitaciones", default=1, required=True)
    hotel_nombre = fields.Char(string="Hotel", required=True)
    hotel_precio_ip = fields.Float(string="Precio IP", compute="_compute_precios_tarifario", store=False)
    hotel_precio_conf_fit = fields.Float(string="Precio CONF FIT", compute="_compute_precios_tarifario", store=False)
    hotel_precio_rack = fields.Float(string="Precio Rack", compute="_compute_precios_tarifario", store=False)
    hotel_precio_noche_usd = fields.Float(string="Precio noche base USD", default=0)
    hotel_precio_noche = fields.Float(string="Precio noche", default=0)
    hotel_descuento = fields.Float(string="Descuento", default=0)
    monto_hotel_usd = fields.Float(string="Monto hotel USD", compute="_compute_monto_hotel", store=True)
    monto_hotel = fields.Float(string="Monto hotel", compute="_compute_monto_hotel", store=True)

    @api.depends("hotel_tarifa_id", "tipo_tarifario", "moneda")
    def _compute_precios_tarifario(self):
        for record in self:
            if not record.hotel_tarifa_id:
                record.hotel_precio_ip = 0
                record.hotel_precio_conf_fit = 0
                record.hotel_precio_rack = 0
                continue
            record.hotel_precio_ip = record._convertir_desde_usd(record.hotel_tarifa_id.obtener_precio_noche_neto_usd("ip"))
            record.hotel_precio_conf_fit = record._convertir_desde_usd(record.hotel_tarifa_id.obtener_precio_noche_neto_usd("conf"))
            record.hotel_precio_rack = record._convertir_desde_usd(record.hotel_tarifa_id.obtener_precio_noche_neto_usd("fit"))

    @api.depends("cantidad_noches", "cantidad_habitaciones", "hotel_precio_noche_usd", "cotizacion_id.moneda")
    def _compute_monto_hotel(self):
        for record in self:
            record.monto_hotel_usd = (record.cantidad_habitaciones or 0) * (record.cantidad_noches or 0) * (record.hotel_precio_noche_usd or 0)
            record.monto_hotel = record._convertir_desde_usd(record.monto_hotel_usd)

    def _convertir_desde_usd(self, monto_usd, moneda=None):
        moneda = moneda or self.cotizacion_id.moneda or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        if moneda == "PEN":
            return (monto_usd or 0) * rates["PEN"]
        if moneda == "EUR":
            return (monto_usd or 0) * rates["EUR"]
        return monto_usd or 0

    def _actualizar_precio_desde_usd(self, moneda=None):
        for record in self:
            record.hotel_precio_noche = record._convertir_desde_usd(record.hotel_precio_noche_usd, moneda)

    def _aplicar_tarifa(self):
        for record in self:
            if not record.hotel_tarifa_id:
                record.hotel_nombre = record.hotel_id.name or False
                record.hotel_precio_noche_usd = 0
                record.hotel_precio_noche = 0
                record.hotel_descuento = 0
                continue
            record.hotel_id = record.hotel_tarifa_id.hotel_id
            record.hotel_nombre = record.hotel_tarifa_id.hotel_id.name
            record.hotel_precio_noche_usd = record.hotel_tarifa_id.obtener_precio_noche_neto_usd(record.tipo_tarifario)
            record.hotel_precio_noche = record._convertir_desde_usd(record.hotel_precio_noche_usd)
            record.hotel_descuento = record.hotel_tarifa_id.descuento or 0

    @api.onchange("hotel_id")
    def _onchange_hotel_id(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_tarifa_id.hotel_id != record.hotel_id:
                record.hotel_tarifa_id = False
            record.hotel_nombre = record.hotel_id.name or False

    @api.onchange("hotel_tarifa_id")
    def _onchange_hotel_tarifa_id(self):
        self._aplicar_tarifa()
        for record in self:
            if record.hotel_tarifa_id:
                record.fecha_check_in = record.fecha_check_in or record.cotizacion_id.fecha_viaje or record.hotel_tarifa_id.fecha_desde
                if not record.fecha_check_out and record.fecha_check_in and record.cantidad_noches:
                    record.fecha_check_out = fields.Date.add(record.fecha_check_in, days=record.cantidad_noches)

    @api.onchange("tipo_tarifario")
    def _onchange_tipo_tarifario(self):
        self._aplicar_tarifa()

    @api.onchange("cantidad_noches")
    def _onchange_cantidad_noches(self):
        for record in self:
            if record.fecha_check_in and record.cantidad_noches and record.cantidad_noches > 0:
                record.fecha_check_out = fields.Date.add(record.fecha_check_in, days=record.cantidad_noches)
            elif record.cantidad_noches is not None and record.cantidad_noches <= 0:
                record.cantidad_noches = 1

    @api.onchange("fecha_check_in", "fecha_check_out")
    def _onchange_fechas(self):
        for record in self:
            if record.fecha_check_in and record.fecha_check_out and record.fecha_check_out > record.fecha_check_in:
                record.cantidad_noches = (record.fecha_check_out - record.fecha_check_in).days

    @api.onchange("hotel_precio_ip")
    def _onchange_hotel_precio_ip(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_precio_ip:
                record.tipo_tarifario = "ip"

    @api.onchange("hotel_precio_conf_fit")
    def _onchange_hotel_precio_conf_fit(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_precio_conf_fit:
                record.tipo_tarifario = "conf"

    @api.onchange("hotel_precio_rack")
    def _onchange_hotel_precio_rack(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_precio_rack:
                record.tipo_tarifario = "fit"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._completar_datos(vals)
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            values = dict(vals)
            record._completar_datos(values)
            super(IncasCotizacionHotelLinea, record).write(values)
        return True

    def _completar_datos(self, vals):
        hotel_id = vals.get("hotel_id") or (self.hotel_id.id if len(self) == 1 else False)
        tarifa_id = vals.get("hotel_tarifa_id") or (self.hotel_tarifa_id.id if len(self) == 1 else False)
        tipo_tarifario = vals.get("tipo_tarifario") or (self.tipo_tarifario if len(self) == 1 else "ip") or "ip"
        tarifa = self.env["incas.hotel.tarifa"].browse(tarifa_id) if tarifa_id else self.env["incas.hotel.tarifa"]
        hotel = self.env["incas.hotel"].browse(hotel_id) if hotel_id else tarifa.hotel_id
        if tarifa and tarifa.exists():
            vals.setdefault("hotel_id", tarifa.hotel_id.id)
            vals["hotel_nombre"] = tarifa.hotel_id.name
            vals.setdefault("tipo_tarifario", tipo_tarifario)
            vals["hotel_precio_noche_usd"] = tarifa.obtener_precio_noche_neto_usd(tipo_tarifario)
            vals["hotel_descuento"] = tarifa.descuento or 0
            vals.setdefault("fecha_check_in", tarifa.fecha_desde)
            cantidad_noches = vals.get("cantidad_noches") or (self.cantidad_noches if len(self) == 1 else 1) or 1
            vals["cantidad_noches"] = cantidad_noches
            if vals.get("fecha_check_in"):
                fecha_check_in = fields.Date.to_date(vals["fecha_check_in"])
                vals.setdefault("fecha_check_out", fields.Date.add(fecha_check_in, days=cantidad_noches))
        elif hotel and hotel.exists():
            vals["hotel_nombre"] = hotel.name
        cotizacion = self.env["incas.cotizacion"].browse(vals.get("cotizacion_id")) if vals.get("cotizacion_id") else self.cotizacion_id
        moneda = (cotizacion.moneda if cotizacion else False) or "USD"
        vals["hotel_precio_noche"] = self._convertir_desde_usd(vals.get("hotel_precio_noche_usd") or 0, moneda)
        return vals
