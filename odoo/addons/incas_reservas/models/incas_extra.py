from odoo import fields, models


class IncasExtra(models.Model):
    _name = "incas.extra"
    _description = "Extra"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código")
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    tipo_extra = fields.Selection(
        [
            ("alimento", "Alimento"),
            ("snack", "Snack"),
            ("equipaje", "Equipaje"),
            ("asistencia", "Asistencia"),
            ("otro", "Otro"),
        ],
        string="Tipo de extra",
        required=True,
        default="otro",
    )
    moneda_base = fields.Selection(
        [("USD", "USD"), ("PEN", "PEN"), ("EUR", "EUR")],
        string="Moneda base",
        required=True,
        default="USD",
    )
    descripcion = fields.Html(string="Descripción")
    observaciones = fields.Text(string="Observaciones")
    tarifa_ids = fields.One2many("incas.extra.tarifa", "extra_id", string="Tarifas")
    tarifa_count = fields.Integer(string="Cantidad de tarifas", compute="_compute_tarifa_count")
    active = fields.Boolean(default=True)

    def _compute_tarifa_count(self):
        for record in self:
            record.tarifa_count = len(record.tarifa_ids)
