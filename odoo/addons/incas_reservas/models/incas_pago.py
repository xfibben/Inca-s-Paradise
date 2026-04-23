from odoo import api, fields, models


class IncasPago(models.Model):
    _name = "incas.pago"
    _description = "Pago"
    _order = "create_date desc"

    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade")
    proveedor = fields.Selection(
        [("efectivo", "Efectivo"), ("izipay", "IziPay"), ("paypal", "PayPal")],
        string="Proveedor",
        required=True,
    )
    metodo = fields.Selection(
        [("efectivo", "Efectivo"), ("tarjeta", "Tarjeta"), ("yape_qr", "Yape QR"), ("paypal", "PayPal")],
        string="Método",
        required=True,
    )
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="PEN",
    )
    monto = fields.Float(string="Monto", required=True)
    moneda_reserva = fields.Selection(related="reserva_id.moneda", string="Moneda reserva", store=True)
    monto_reserva = fields.Float(string="Monto aplicado a reserva", compute="_compute_monto_reserva", store=True)
    estado = fields.Selection(
        [("pendiente", "Pendiente"), ("pagado", "Pagado"), ("fallido", "Fallido"), ("reembolsado", "Reembolsado")],
        string="Estado",
        required=True,
        default="pendiente",
    )
    transaccion_id = fields.Char(string="Transacción ID")
    orden_id = fields.Char(string="Orden ID")
    codigo_respuesta = fields.Char(string="Código de respuesta")
    mensaje_respuesta = fields.Char(string="Mensaje de respuesta")
    qr_url = fields.Text(string="QR URL")
    qr_expiracion = fields.Datetime(string="QR expiración")
    fecha_pago = fields.Datetime(string="Fecha de pago")
    ip_cliente = fields.Char(string="IP cliente")

    @api.onchange("proveedor")
    def _onchange_proveedor(self):
        for record in self:
            if record.proveedor == "efectivo":
                record.metodo = "efectivo"
            elif record.proveedor == "paypal":
                record.metodo = "paypal"
                record.moneda = "USD"
            elif record.proveedor == "izipay" and record.metodo == "paypal":
                record.metodo = False

    @api.onchange("metodo")
    def _onchange_metodo(self):
        for record in self:
            if record.metodo == "efectivo":
                record.proveedor = "efectivo"
            elif record.metodo == "paypal":
                record.proveedor = "paypal"
                record.moneda = "USD"
            elif record.metodo in ("tarjeta", "yape_qr"):
                record.proveedor = "izipay"

    def _convertir_a_usd(self, monto, moneda, rates):
        if moneda == "PEN":
            return monto / rates["PEN"] if rates["PEN"] else 0
        if moneda == "EUR":
            return monto / rates["EUR"] if rates["EUR"] else 0
        return monto

    def _convertir_desde_usd(self, monto_usd, moneda, rates):
        if moneda == "PEN":
            return monto_usd * rates["PEN"]
        if moneda == "EUR":
            return monto_usd * rates["EUR"]
        return monto_usd

    @api.depends("monto", "moneda", "reserva_id.moneda")
    def _compute_monto_reserva(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            monto_usd = record._convertir_a_usd(record.monto or 0, record.moneda, rates)
            record.monto_reserva = record._convertir_desde_usd(monto_usd, record.reserva_id.moneda, rates)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("estado") == "pagado" and not vals.get("fecha_pago"):
                vals["fecha_pago"] = fields.Datetime.now()
        pagos = super().create(vals_list)
        pagos.mapped("reserva_id")._actualizar_pendientes()
        for reserva in pagos.mapped("reserva_id"):
            try:
                reserva._sincronizar_con_sheets()
            except Exception:
                pass
        return pagos

    def write(self, vals):
        if vals.get("estado") == "pagado" and not vals.get("fecha_pago"):
            vals["fecha_pago"] = fields.Datetime.now()
        result = super().write(vals)
        self.mapped("reserva_id")._actualizar_pendientes()
        for reserva in self.mapped("reserva_id"):
            try:
                reserva._sincronizar_con_sheets()
            except Exception:
                pass
        return result
