from odoo import fields, models


class IncasHotel(models.Model):
    _name = "incas.hotel"
    _description = "Hotel"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código")
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    categoria = fields.Selection(
        [
            ("1", "1 estrella"),
            ("2", "2 estrellas"),
            ("3", "3 estrellas"),
            ("4", "4 estrellas"),
            ("5", "5 estrellas"),
            ("boutique", "Boutique"),
            ("luxury", "Luxury"),
        ],
        string="Categoría",
    )
    pais_id = fields.Many2one("res.country", string="País")
    ciudad = fields.Char(string="Ciudad")
    direccion = fields.Char(string="Dirección")
    check_in_default = fields.Char(string="Check-in por defecto")
    check_out_default = fields.Char(string="Check-out por defecto")
    moneda_base = fields.Selection(
        [("USD", "USD"), ("PEN", "PEN"), ("EUR", "EUR")],
        string="Moneda base",
        required=True,
        default="USD",
    )
    politicas = fields.Text(string="Políticas")
    observaciones = fields.Text(string="Observaciones")
    tarifa_ids = fields.One2many("incas.hotel.tarifa", "hotel_id", string="Tarifas")
    tarifa_count = fields.Integer(string="Cantidad de tarifas", compute="_compute_tarifa_count")
    active = fields.Boolean(default=True)

    def _compute_tarifa_count(self):
        for record in self:
            record.tarifa_count = len(record.tarifa_ids)
