from odoo import api, fields, models


class IncasBoleta(models.Model):
    _name = "incas.boleta"
    _description = "Boleta"
    _order = "periodo_anio desc, periodo_mes desc, id desc"

    numero = fields.Char(string="Número", required=True, copy=False, default="Nuevo")
    trabajador_id = fields.Many2one("res.users", string="Trabajador", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="trabajador_id.company_id", string="Compañía", store=True)
    currency_id = fields.Many2one(related="trabajador_id.currency_id", string="Moneda", store=True)
    periodo_anio = fields.Integer(string="Año", required=True, default=lambda self: fields.Date.today().year)
    periodo_mes = fields.Selection(
        [
            ("01", "Enero"),
            ("02", "Febrero"),
            ("03", "Marzo"),
            ("04", "Abril"),
            ("05", "Mayo"),
            ("06", "Junio"),
            ("07", "Julio"),
            ("08", "Agosto"),
            ("09", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes",
        required=True,
        default=lambda self: fields.Date.today().strftime("%m"),
    )
    fecha_emision = fields.Date(string="Fecha de emisión", required=True, default=fields.Date.context_today)
    fecha_pago = fields.Date(string="Fecha de pago")
    sueldo_base = fields.Monetary(string="Sueldo base", currency_field="currency_id")
    asignacion_familiar = fields.Monetary(string="Asignación familiar", currency_field="currency_id")
    bonos = fields.Monetary(string="Bonos", currency_field="currency_id")
    horas_extra = fields.Monetary(string="Horas extra", currency_field="currency_id")
    comisiones = fields.Monetary(string="Comisiones", currency_field="currency_id")
    otros_ingresos = fields.Monetary(string="Otros ingresos", currency_field="currency_id")
    total_ingresos = fields.Monetary(
        string="Total ingresos",
        currency_field="currency_id",
        compute="_compute_totales",
        store=True,
    )
    afp_onp = fields.Monetary(string="AFP / ONP", currency_field="currency_id")
    adelantos = fields.Monetary(string="Adelantos", currency_field="currency_id")
    prestamos = fields.Monetary(string="Préstamos", currency_field="currency_id")
    descuentos = fields.Monetary(string="Descuentos", currency_field="currency_id")
    otros_descuentos = fields.Monetary(string="Otros descuentos", currency_field="currency_id")
    total_descuentos = fields.Monetary(
        string="Total descuentos",
        currency_field="currency_id",
        compute="_compute_totales",
        store=True,
    )
    neto_pagar = fields.Monetary(
        string="Neto a pagar",
        currency_field="currency_id",
        compute="_compute_totales",
        store=True,
    )
    estado = fields.Selection(
        [("borrador", "Borrador"), ("confirmada", "Confirmada"), ("pagada", "Pagada"), ("anulada", "Anulada")],
        string="Estado",
        required=True,
        default="borrador",
    )
    observaciones = fields.Text(string="Observaciones")

    @api.depends(
        "sueldo_base",
        "asignacion_familiar",
        "bonos",
        "horas_extra",
        "comisiones",
        "otros_ingresos",
        "afp_onp",
        "adelantos",
        "prestamos",
        "descuentos",
        "otros_descuentos",
    )
    def _compute_totales(self):
        for record in self:
            record.total_ingresos = (
                (record.sueldo_base or 0.0)
                + (record.asignacion_familiar or 0.0)
                + (record.bonos or 0.0)
                + (record.horas_extra or 0.0)
                + (record.comisiones or 0.0)
                + (record.otros_ingresos or 0.0)
            )
            record.total_descuentos = (
                (record.afp_onp or 0.0)
                + (record.adelantos or 0.0)
                + (record.prestamos or 0.0)
                + (record.descuentos or 0.0)
                + (record.otros_descuentos or 0.0)
            )
            record.neto_pagar = record.total_ingresos - record.total_descuentos

    @api.onchange("trabajador_id")
    def _onchange_trabajador_id(self):
        for record in self:
            if record.trabajador_id:
                record.sueldo_base = record.trabajador_id.sueldo_base

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("numero", "Nuevo") == "Nuevo":
                vals["numero"] = sequence.next_by_code("incas.boleta") or "Nuevo"
            if vals.get("trabajador_id") and not vals.get("sueldo_base"):
                trabajador = self.env["res.users"].browse(vals["trabajador_id"])
                vals["sueldo_base"] = trabajador.sueldo_base
        return super().create(vals_list)

    def action_confirmar(self):
        self.write({"estado": "confirmada"})

    def action_marcar_pagada(self):
        self.write({"estado": "pagada", "fecha_pago": self.fecha_pago or fields.Date.context_today(self)})

    def action_borrador(self):
        self.write({"estado": "borrador"})

    def action_anular(self):
        self.write({"estado": "anulada"})

    def action_imprimir_boleta(self):
        self.ensure_one()
        return self.env.ref("incas_rrhh.action_report_incas_boleta").report_action(self)
