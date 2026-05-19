from odoo import api, fields, models
import json


class IncasReservaPaqueteLinea(models.Model):
    _name = "incas.reserva.paquete.linea"
    _description = "Línea de paquete de reserva"
    _order = "sequence, id"

    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade")
    moneda = fields.Selection(related="reserva_id.moneda", string="Moneda", readonly=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    fecha = fields.Date(string="Fecha")
    horario = fields.Text(string="Horario")
    horario_id = fields.Many2one("incas.horario.opcion", string="Horario", domain="[('servicio_id', '=', servicio_id)]")
    servicio_id = fields.Many2one("incas.servicio.catalogo", string="Servicio", required=True)
    vehiculo_id = fields.Many2one("incas.catalogo.vehiculo", string="Vehículo")
    vehiculo_disponible_ids = fields.Many2many("incas.catalogo.vehiculo", compute="_compute_vehiculo_disponible_ids")
    tipo_servicio = fields.Selection(
        [("tour", "Tour"), ("transporte", "Transporte")],
        string="Tipo",
        compute="_compute_snapshot_servicio",
        store=True,
    )
    tipo_tour = fields.Selection(
        [("tour", "Tour"), ("small_trip", "Small Trip"), ("package", "Package")],
        string="Tipo de tour",
        compute="_compute_snapshot_servicio",
        store=True,
    )
    estilo_transporte_id = fields.Many2one(
        "incas.estilo.transporte",
        string="Estilo de transporte",
        compute="_compute_snapshot_servicio",
        store=True,
    )
    nombre = fields.Char(string="Nombre", required=True)
    precio_adulto_usd = fields.Float(string="Precio adulto base USD", required=True, default=0)
    precio_nino_usd = fields.Float(string="Precio niño base USD", required=True, default=0)
    precio_adulto = fields.Float(string="Precio adulto", default=0)
    precio_nino = fields.Float(string="Precio niño", default=0)
    descuento = fields.Float(string="Descuento", required=True, default=0)
    precio_adulto_neto_usd = fields.Float(string="Precio adulto neto USD", compute="_compute_precios_netos", store=True)
    precio_nino_neto_usd = fields.Float(string="Precio niño neto USD", compute="_compute_precios_netos", store=True)
    precio_adulto_neto = fields.Float(string="Precio adulto neto", default=0)
    precio_nino_neto = fields.Float(string="Precio niño neto", default=0)
    slug = fields.Char(string="Slug")
    destino_slug = fields.Char(string="Destino slug")
    destinos_data = fields.Text(string="Destinos")
    estilos_data = fields.Text(string="Estilos")
    duration_days = fields.Integer(string="Duración en días")
    hero_title = fields.Char(string="Hero title")
    hero_description = fields.Text(string="Hero description")
    hero_slide_images_data = fields.Text(string="Hero slide images")
    highlights_title = fields.Char(string="Highlights title")
    highlights_question = fields.Char(string="Highlights question")
    highlights_lead = fields.Text(string="Highlights lead")
    highlights_items_data = fields.Text(string="Highlights items")
    featured_images_data = fields.Text(string="Featured images")
    itinerary_title = fields.Char(string="Itinerary title")
    itinerary_items_data = fields.Text(string="Itinerary items")
    schedule_title = fields.Char(string="Schedule title")
    schedule_items_data = fields.Text(string="Schedule items")
    included_title = fields.Char(string="Included title")
    included_items_data = fields.Text(string="Included items")
    excluded_title = fields.Char(string="Excluded title")
    excluded_items_data = fields.Text(string="Excluded items")
    faq_title = fields.Char(string="FAQ title")
    faq_items_data = fields.Text(string="FAQ items")
    image_data = fields.Image(string="Imagen")
    wallpaper_data = fields.Image(string="Imagen de fondo")
    destino_origen_data = fields.Text(string="Destino origen")
    destino_llegada_data = fields.Text(string="Destino llegada")
    modelo_vehiculo = fields.Char(string="Modelo de vehículo")
    duracion_viaje = fields.Char(string="Duración del viaje")
    distancia = fields.Char(string="Distancia")
    descripcion_origen = fields.Html(string="Descripción origen")
    descripcion_llegada = fields.Html(string="Descripción llegada")
    descripcion = fields.Html(string="Descripción")
    tipos_transporte_data = fields.Text(string="Tipos de transporte")
    precios_data = fields.Text(string="Precios por vehículo")

    def _horario_por_defecto(self, servicio):
        if not servicio:
            return self.env["incas.horario.opcion"]
        return self.env["incas.horario.opcion"].search([("servicio_id", "=", servicio.id)], order="sequence, id", limit=1)

    def _convertir_desde_usd(self, monto_usd, moneda=None):
        moneda = moneda or self.reserva_id.moneda or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        if moneda == "PEN":
            return (monto_usd or 0) * rates["PEN"]
        if moneda == "EUR":
            return (monto_usd or 0) * rates["EUR"]
        return monto_usd or 0

    def _convertir_a_usd(self, monto, moneda=None):
        moneda = moneda or self.reserva_id.moneda or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        if moneda == "PEN" and rates["PEN"]:
            return (monto or 0) / rates["PEN"]
        if moneda == "EUR" and rates["EUR"]:
            return (monto or 0) / rates["EUR"]
        return monto or 0

    def _actualizar_precios_desde_usd(self, moneda=None):
        for record in self:
            moneda_actual = moneda or record.reserva_id.moneda or "USD"
            record.precio_adulto = record._convertir_desde_usd(record.precio_adulto_usd, moneda_actual)
            record.precio_nino = record._convertir_desde_usd(record.precio_nino_usd, moneda_actual)
            record.precio_adulto_neto = record._convertir_desde_usd(record.precio_adulto_neto_usd, moneda_actual)
            record.precio_nino_neto = record._convertir_desde_usd(record.precio_nino_neto_usd, moneda_actual)

    def _actualizar_usd_desde_precios(self, moneda=None):
        for record in self:
            moneda_actual = moneda or record.reserva_id.moneda or "USD"
            record.precio_adulto_usd = record._convertir_a_usd(record.precio_adulto, moneda_actual)
            record.precio_nino_usd = record._convertir_a_usd(record.precio_nino, moneda_actual)
            factor = 1 - ((record.descuento or 0) / 100)
            record.precio_adulto_neto_usd = (record.precio_adulto_usd or 0) * factor
            record.precio_nino_neto_usd = (record.precio_nino_usd or 0) * factor
            record.precio_adulto_neto = record._convertir_desde_usd(record.precio_adulto_neto_usd, moneda_actual)
            record.precio_nino_neto = record._convertir_desde_usd(record.precio_nino_neto_usd, moneda_actual)

    def _preparar_vals_monetarios(self, vals):
        values = dict(vals)
        reserva = self.env["incas.reserva"].browse(values.get("reserva_id")) if values.get("reserva_id") else self.reserva_id
        moneda = reserva.moneda or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()

        def convertir_a_usd(monto):
            if moneda == "PEN" and rates["PEN"]:
                return (monto or 0) / rates["PEN"]
            if moneda == "EUR" and rates["EUR"]:
                return (monto or 0) / rates["EUR"]
            return monto or 0

        def convertir_desde_usd(monto_usd):
            if moneda == "PEN":
                return (monto_usd or 0) * rates["PEN"]
            if moneda == "EUR":
                return (monto_usd or 0) * rates["EUR"]
            return monto_usd or 0

        if "precio_adulto" in values:
            values["precio_adulto_usd"] = convertir_a_usd(values["precio_adulto"])
        if "precio_nino" in values:
            values["precio_nino_usd"] = convertir_a_usd(values["precio_nino"])

        precio_adulto_usd = values.get("precio_adulto_usd", self.precio_adulto_usd or 0)
        precio_nino_usd = values.get("precio_nino_usd", self.precio_nino_usd or 0)
        descuento = values.get("descuento", self.descuento or 0)
        factor = 1 - ((descuento or 0) / 100)

        values["precio_adulto"] = convertir_desde_usd(precio_adulto_usd)
        values["precio_nino"] = convertir_desde_usd(precio_nino_usd)
        values["precio_adulto_neto_usd"] = precio_adulto_usd * factor
        values["precio_nino_neto_usd"] = precio_nino_usd * factor
        values["precio_adulto_neto"] = convertir_desde_usd(values["precio_adulto_neto_usd"])
        values["precio_nino_neto"] = convertir_desde_usd(values["precio_nino_neto_usd"])
        return values

    def _obtener_snapshot_servicio(self, servicio):
        valores = {"slug": servicio.slug}
        if servicio.tipo_servicio == "tour":
            detalle = self.env["incas.tour"].search([("servicio_id", "=", servicio.id)], limit=1)
            if not detalle:
                return valores
            valores.update(detalle._valores_snapshot_operativo())
            return valores
        detalle = self.env["incas.catalogo.transporte"].search([("servicio_id", "=", servicio.id)], limit=1)
        if not detalle:
            return valores
        valores.update(
            {
                "image_data": detalle.image_data,
                "wallpaper_data": detalle.wallpaper_data,
                "destino_origen_data": detalle.destino_origen_data,
                "destino_llegada_data": detalle.destino_llegada_data,
                "modelo_vehiculo": detalle.modelo_vehiculo,
                "duracion_viaje": detalle.duracion_viaje,
                "distancia": detalle.distancia,
                "descripcion_origen": detalle.descripcion_origen,
                "descripcion_llegada": detalle.descripcion_llegada,
                "descripcion": detalle.descripcion,
                "included_title": False,
                "included_items_data": detalle.included_items_data,
                "excluded_title": False,
                "excluded_items_data": detalle.excluded_items_data,
                "tipos_transporte_data": detalle.tipos_transporte_data,
                "precios_data": detalle.precios_data,
            }
        )
        return valores

    def action_open_popup(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.nombre or "Detalle del servicio",
            "res_model": "incas.reserva.paquete.linea",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def _aplicar_tarifa_vehiculo(self):
        for record in self:
            if record.tipo_servicio != "transporte" or not record.servicio_id or not record.vehiculo_id:
                continue
            tarifa = record.servicio_id.obtener_tarifa_vehiculo_transporte(record.vehiculo_id)
            record.precio_adulto_usd = tarifa["precio_adulto"]
            record.precio_nino_usd = tarifa["precio_nino"]
            record.descuento = tarifa["descuento"]
            factor = 1 - ((record.descuento or 0) / 100)
            record.precio_adulto_neto_usd = (record.precio_adulto_usd or 0) * factor
            record.precio_nino_neto_usd = (record.precio_nino_usd or 0) * factor
            record._actualizar_precios_desde_usd()

    @api.depends("servicio_id", "tipo_servicio")
    def _compute_vehiculo_disponible_ids(self):
        for record in self:
            if record.servicio_id and record.tipo_servicio == "transporte":
                record.vehiculo_disponible_ids = record.servicio_id.obtener_vehiculos_transporte()
            else:
                record.vehiculo_disponible_ids = self.env["incas.catalogo.vehiculo"]

    @api.depends("servicio_id")
    def _compute_snapshot_servicio(self):
        for record in self:
            record.tipo_servicio = record.servicio_id.tipo_servicio
            record.tipo_tour = record.servicio_id.tipo_tour
            record.estilo_transporte_id = record.servicio_id.estilo_transporte_id

    @api.depends("precio_adulto_usd", "precio_nino_usd", "descuento")
    def _compute_precios_netos(self):
        for record in self:
            factor = 1 - ((record.descuento or 0) / 100)
            record.precio_adulto_neto_usd = (record.precio_adulto_usd or 0) * factor
            record.precio_nino_neto_usd = (record.precio_nino_usd or 0) * factor

    @api.onchange("servicio_id")
    def _onchange_servicio_id(self):
        for record in self:
            if not record.servicio_id:
                continue
            record.nombre = record.servicio_id.name
            for campo, valor in record._obtener_snapshot_servicio(record.servicio_id).items():
                record[campo] = valor
            record.horario_id = record._horario_por_defecto(record.servicio_id)
            record.horario = record.horario_id.name or False
            if record.servicio_id.tipo_servicio == "transporte":
                record.vehiculo_id = record.servicio_id.obtener_vehiculo_transporte()
                record._aplicar_tarifa_vehiculo()
            else:
                record.vehiculo_id = False
                record.precio_adulto_usd = record.servicio_id.precio_adulto
                record.precio_nino_usd = record.servicio_id.precio_nino
                record.descuento = record.servicio_id.descuento
                factor = 1 - ((record.descuento or 0) / 100)
                record.precio_adulto_neto_usd = (record.precio_adulto_usd or 0) * factor
                record.precio_nino_neto_usd = (record.precio_nino_usd or 0) * factor
                record._actualizar_precios_desde_usd()

    @api.onchange("vehiculo_id")
    def _onchange_vehiculo_id(self):
        self._aplicar_tarifa_vehiculo()

    @api.onchange("horario_id")
    def _onchange_horario_id(self):
        for record in self:
            record.horario = record.horario_id.name or False

    @api.onchange("precio_adulto", "precio_nino", "descuento")
    def _onchange_precios_visibles(self):
        self._actualizar_usd_desde_precios()

    @api.model_create_multi
    def create(self, vals_list):
        processed_vals_list = []
        for vals in vals_list:
            values = dict(vals)
            servicio_id = values.get("servicio_id")
            reserva = self.env["incas.reserva"].browse(values.get("reserva_id")) if values.get("reserva_id") else self.env["incas.reserva"]
            if not values.get("fecha") and reserva:
                values["fecha"] = reserva.fecha_viaje
            if not servicio_id:
                processed_vals_list.append(self._preparar_vals_monetarios(values))
                continue
            servicio = self.env["incas.servicio.catalogo"].browse(servicio_id)
            if servicio.exists():
                values.setdefault("nombre", servicio.name)
                horario = self._horario_por_defecto(servicio)
                if not values.get("horario_id") and horario:
                    values["horario_id"] = horario.id
                if values.get("horario_id"):
                    horario = self.env["incas.horario.opcion"].browse(values["horario_id"])
                    values["horario"] = horario.name or False
                if servicio.tipo_servicio == "transporte":
                    vehiculo = servicio.obtener_vehiculo_transporte(vehiculo_id=values.get("vehiculo_id"), usar_default=not values.get("vehiculo_id"))
                    if vehiculo and not values.get("vehiculo_id"):
                        values["vehiculo_id"] = vehiculo.id
                    tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo)
                    values.setdefault("precio_adulto_usd", tarifa["precio_adulto"])
                    values.setdefault("precio_nino_usd", tarifa["precio_nino"])
                    values.setdefault("descuento", tarifa["descuento"])
                else:
                    values.setdefault("precio_adulto_usd", servicio.precio_adulto)
                    values.setdefault("precio_nino_usd", servicio.precio_nino)
                    values.setdefault("descuento", servicio.descuento)
                for campo, valor in self._obtener_snapshot_servicio(servicio).items():
                    values.setdefault(campo, valor)
            processed_vals_list.append(self._preparar_vals_monetarios(values))
        lineas = super().create(processed_vals_list)
        lineas.mapped("reserva_id")._aplicar_resumen_paquete()
        return lineas

    def write(self, vals):
        for record in self:
            values = dict(vals)
            servicio_id = values.get("servicio_id")
            if not values.get("fecha") and record.reserva_id and not record.fecha:
                values["fecha"] = record.reserva_id.fecha_viaje
            if values.get("vehiculo_id") and not servicio_id and record.servicio_id.tipo_servicio == "transporte":
                vehiculo = record.servicio_id.obtener_vehiculo_transporte(vehiculo_id=values.get("vehiculo_id"))
                tarifa = record.servicio_id.obtener_tarifa_vehiculo_transporte(vehiculo)
                values.setdefault("precio_adulto_usd", tarifa["precio_adulto"])
                values.setdefault("precio_nino_usd", tarifa["precio_nino"])
                values.setdefault("descuento", tarifa["descuento"])
            if servicio_id:
                servicio = self.env["incas.servicio.catalogo"].browse(servicio_id)
                if servicio.exists():
                    values.setdefault("nombre", servicio.name)
                    horario = self._horario_por_defecto(servicio)
                    if not values.get("horario_id") and horario:
                        values["horario_id"] = horario.id
                    if values.get("horario_id"):
                        horario = self.env["incas.horario.opcion"].browse(values["horario_id"])
                        values["horario"] = horario.name or False
                    if servicio.tipo_servicio == "transporte":
                        vehiculo = servicio.obtener_vehiculo_transporte(
                            vehiculo_id=values.get("vehiculo_id"),
                            vehiculo_actual=record.vehiculo_id if record.servicio_id == servicio else False,
                            usar_default=not values.get("vehiculo_id") and record.servicio_id != servicio,
                        )
                        if vehiculo and not values.get("vehiculo_id"):
                            values["vehiculo_id"] = vehiculo.id
                        tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo)
                        values.setdefault("precio_adulto_usd", tarifa["precio_adulto"])
                        values.setdefault("precio_nino_usd", tarifa["precio_nino"])
                        values.setdefault("descuento", tarifa["descuento"])
                    else:
                        values.setdefault("precio_adulto_usd", servicio.precio_adulto)
                        values.setdefault("precio_nino_usd", servicio.precio_nino)
                        values.setdefault("descuento", servicio.descuento)
                    for campo, valor in record._obtener_snapshot_servicio(servicio).items():
                        values.setdefault(campo, valor)
            elif values.get("horario_id"):
                horario = self.env["incas.horario.opcion"].browse(values["horario_id"])
                values["horario"] = horario.name or False
            super(IncasReservaPaqueteLinea, record).write(record._preparar_vals_monetarios(values))
        self.mapped("reserva_id")._aplicar_resumen_paquete()
        return True

    def unlink(self):
        reservas = self.mapped("reserva_id")
        result = super().unlink()
        reservas._aplicar_resumen_paquete()
        return result
