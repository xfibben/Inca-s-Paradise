from odoo import api, fields, models


class IncasCotizacionExtraLinea(models.Model):
    _name = "incas.cotizacion.extra.linea"
    _description = "Línea de extra de cotización"
    _order = "sequence, id"

    cotizacion_id = fields.Many2one("incas.cotizacion", string="Cotización", required=True, ondelete="cascade")
    moneda = fields.Selection(related="cotizacion_id.moneda", string="Moneda", readonly=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    extra_id = fields.Many2one("incas.extra", string="Extra", required=True)
    extra_tarifa_id = fields.Many2one(
        "incas.extra.tarifa",
        string="Tarifa de extra",
        domain="[('extra_id', '=', extra_id)]",
    )
    extra_nombre = fields.Char(string="Extra", required=True)
    extra_unidad = fields.Selection(
        [("unidad", "Unidad"), ("persona", "Persona"), ("tramo", "Tramo"), ("dia", "Día")],
        string="Unidad",
    )
    cantidad_extra = fields.Integer(string="Cantidad", default=1, required=True)
    extra_precio_unitario_usd = fields.Float(string="Precio unitario base USD", default=0)
    extra_precio_unitario = fields.Float(string="Precio unitario", default=0)
    extra_descuento = fields.Float(string="Descuento", default=0)
    monto_extra_usd = fields.Float(string="Monto extra USD", compute="_compute_monto_extra", store=True)
    monto_extra = fields.Float(string="Monto extra", compute="_compute_monto_extra", store=True)

    @api.depends("cantidad_extra", "extra_precio_unitario_usd", "cotizacion_id.moneda")
    def _compute_monto_extra(self):
        for record in self:
            record.monto_extra_usd = (record.cantidad_extra or 0) * (record.extra_precio_unitario_usd or 0)
            record.monto_extra = record._convertir_desde_usd(record.monto_extra_usd)

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
            record.extra_precio_unitario = record._convertir_desde_usd(record.extra_precio_unitario_usd, moneda)

    def _aplicar_tarifa(self):
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
            record.extra_precio_unitario = record._convertir_desde_usd(record.extra_precio_unitario_usd)
            record.extra_descuento = record.extra_tarifa_id.descuento or 0

    @api.onchange("extra_id")
    def _onchange_extra_id(self):
        for record in self:
            if record.extra_tarifa_id and record.extra_tarifa_id.extra_id != record.extra_id:
                record.extra_tarifa_id = False
            record.extra_nombre = record.extra_id.name or False

    @api.onchange("extra_tarifa_id")
    def _onchange_extra_tarifa_id(self):
        self._aplicar_tarifa()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._completar_datos(vals)
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            values = dict(vals)
            record._completar_datos(values)
            super(IncasCotizacionExtraLinea, record).write(values)
        return True

    def _completar_datos(self, vals):
        extra_id = vals.get("extra_id")
        tarifa_id = vals.get("extra_tarifa_id")
        tarifa = self.env["incas.extra.tarifa"].browse(tarifa_id) if tarifa_id else self.env["incas.extra.tarifa"]
        extra = self.env["incas.extra"].browse(extra_id) if extra_id else tarifa.extra_id
        if tarifa and tarifa.exists():
            vals.setdefault("extra_id", tarifa.extra_id.id)
            vals["extra_nombre"] = tarifa.extra_id.name
            vals["extra_unidad"] = tarifa.unidad
            vals["extra_precio_unitario_usd"] = tarifa.obtener_precio_unitario_neto_usd()
            vals["extra_descuento"] = tarifa.descuento or 0
        elif extra and extra.exists():
            vals["extra_nombre"] = extra.name
        cotizacion = self.env["incas.cotizacion"].browse(vals.get("cotizacion_id")) if vals.get("cotizacion_id") else self.cotizacion_id
        moneda = (cotizacion.moneda if cotizacion else False) or "USD"
        vals["extra_precio_unitario"] = self._convertir_desde_usd(vals.get("extra_precio_unitario_usd") or 0, moneda)
        return vals
