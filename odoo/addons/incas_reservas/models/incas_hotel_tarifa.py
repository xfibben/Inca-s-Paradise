from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasHotelTarifa(models.Model):
    _name = "incas.hotel.tarifa"
    _description = "Tarifa de hotel"
    _order = "hotel_id, fecha_desde desc, name"

    name = fields.Char(string="Nombre", required=True)
    hotel_id = fields.Many2one("incas.hotel", string="Hotel", required=True, ondelete="cascade")
    fecha_desde = fields.Date(string="Fecha desde", required=True)
    fecha_hasta = fields.Date(string="Fecha hasta", required=True)
    tipo_habitacion = fields.Selection(
        [
            ("simple", "Simple"),
            ("doble", "Doble"),
            ("matrimonial", "Matrimonial"),
            ("triple", "Triple"),
            ("cuadruple", "Cuádruple"),
            ("suite", "Suite"),
            ("familiar", "Familiar"),
        ],
        string="Tipo de habitación",
        required=True,
    )
    regimen = fields.Selection(
        [
            ("solo_alojamiento", "Solo alojamiento"),
            ("desayuno", "Desayuno"),
            ("media_pension", "Media pensión"),
            ("pension_completa", "Pensión completa"),
            ("todo_incluido", "Todo incluido"),
        ],
        string="Régimen",
        required=True,
        default="desayuno",
    )
    acomodacion = fields.Selection(
        [
            ("simple", "Simple"),
            ("doble", "Doble"),
            ("triple", "Triple"),
            ("cuadruple", "Cuádruple"),
            ("matrimonial", "Matrimonial"),
        ],
        string="Acomodación",
        required=True,
        default="doble",
    )
    capacidad_adultos = fields.Integer(string="Capacidad adultos", default=2, required=True)
    capacidad_ninos = fields.Integer(string="Capacidad niños", default=0, required=True)
    min_noches = fields.Integer(string="Noches mínimas", default=1, required=True)
    precio_noche_usd = fields.Float(string="Precio por noche base", required=True, default=0)
    precio_nino_usd = fields.Float(string="Precio niño base", default=0)
    precio_adulto_extra_usd = fields.Float(string="Precio adulto extra base", default=0)
    precio_nino_extra_usd = fields.Float(string="Precio niño extra base", default=0)
    descuento = fields.Float(string="Descuento", default=0)
    incluye_impuestos = fields.Boolean(string="Incluye impuestos", default=True)
    active = fields.Boolean(default=True)

    _incas_hotel_tarifa_unique = models.Constraint(
        "UNIQUE(hotel_id, fecha_desde, fecha_hasta, tipo_habitacion, regimen, acomodacion)",
        "Ya existe una tarifa con la misma vigencia y configuración para este hotel.",
    )

    @api.constrains("fecha_desde", "fecha_hasta")
    def _check_fechas(self):
        for record in self:
            if record.fecha_desde and record.fecha_hasta and record.fecha_desde > record.fecha_hasta:
                raise ValidationError("La fecha desde no puede ser mayor que la fecha hasta.")

    @api.constrains(
        "capacidad_adultos",
        "capacidad_ninos",
        "min_noches",
        "precio_noche_usd",
        "precio_nino_usd",
        "precio_adulto_extra_usd",
        "precio_nino_extra_usd",
        "descuento",
    )
    def _check_valores(self):
        for record in self:
            if record.capacidad_adultos < 0 or record.capacidad_ninos < 0:
                raise ValidationError("La capacidad no puede ser negativa.")
            if record.min_noches < 1:
                raise ValidationError("Las noches mínimas deben ser al menos 1.")
            if (
                record.precio_noche_usd < 0
                or record.precio_nino_usd < 0
                or record.precio_adulto_extra_usd < 0
                or record.precio_nino_extra_usd < 0
            ):
                raise ValidationError("Los precios no pueden ser negativos.")
            if record.descuento < 0 or record.descuento > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100.")

    # Convierte desde la moneda base del hotel hacia USD para mantener la cotización interna consistente.
    def _convertir_base_a_usd(self, monto_base):
        self.ensure_one()
        moneda_base = self.hotel_id.moneda_base or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        if moneda_base == "PEN" and rates["PEN"]:
            return (monto_base or 0) / rates["PEN"]
        if moneda_base == "EUR" and rates["EUR"]:
            return (monto_base or 0) / rates["EUR"]
        return monto_base or 0

    # Devuelve la tarifa neta en USD para reutilizar el mismo criterio en cotización y reserva.
    def obtener_precio_noche_neto_usd(self):
        self.ensure_one()
        precio_noche_usd = self._convertir_base_a_usd(self.precio_noche_usd or 0)
        return precio_noche_usd * (1 - ((self.descuento or 0) / 100))
