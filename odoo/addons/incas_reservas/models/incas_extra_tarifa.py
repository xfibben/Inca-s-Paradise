from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasExtraTarifa(models.Model):
    _name = "incas.extra.tarifa"
    _description = "Tarifa de extra"
    _order = "extra_id, fecha_desde desc, name"

    name = fields.Char(string="Nombre", required=True)
    extra_id = fields.Many2one("incas.extra", string="Extra", required=True, ondelete="cascade")
    fecha_desde = fields.Date(string="Fecha desde", required=True)
    fecha_hasta = fields.Date(string="Fecha hasta", required=True)
    unidad = fields.Selection(
        [
            ("unidad", "Unidad"),
            ("persona", "Persona"),
            ("tramo", "Tramo"),
            ("dia", "Día"),
        ],
        string="Unidad de cobro",
        required=True,
        default="unidad",
    )
    precio_unitario_usd = fields.Float(string="Precio unitario base", required=True, default=0)
    descuento = fields.Float(string="Descuento", default=0)
    active = fields.Boolean(default=True)

    _incas_extra_tarifa_unique = models.Constraint(
        "UNIQUE(extra_id, fecha_desde, fecha_hasta, unidad)",
        "Ya existe una tarifa con la misma vigencia y unidad para este extra.",
    )

    @api.constrains("fecha_desde", "fecha_hasta")
    def _check_fechas(self):
        for record in self:
            if record.fecha_desde and record.fecha_hasta and record.fecha_desde > record.fecha_hasta:
                raise ValidationError("La fecha desde no puede ser mayor que la fecha hasta.")

    @api.constrains("precio_unitario_usd", "descuento")
    def _check_valores(self):
        for record in self:
            if record.precio_unitario_usd < 0:
                raise ValidationError("El precio no puede ser negativo.")
            if record.descuento < 0 or record.descuento > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100.")

    # Convierte desde la moneda base del extra hacia USD.
    def _convertir_base_a_usd(self, monto_base):
        self.ensure_one()
        moneda_base = self.extra_id.moneda_base or "USD"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        if moneda_base == "PEN" and rates["PEN"]:
            return (monto_base or 0) / rates["PEN"]
        if moneda_base == "EUR" and rates["EUR"]:
            return (monto_base or 0) / rates["EUR"]
        return monto_base or 0

    def obtener_precio_unitario_neto_usd(self):
        self.ensure_one()
        precio_unitario_usd = self._convertir_base_a_usd(self.precio_unitario_usd or 0)
        return precio_unitario_usd * (1 - ((self.descuento or 0) / 100))
