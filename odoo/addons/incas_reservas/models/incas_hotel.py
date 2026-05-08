from odoo import fields, models


class IncasHotel(models.Model):
    _name = "incas.hotel"
    _description = "Hotel"
    _order = "name"

    _CATEGORIAS_LEGACY = {
        "1": "1 estrella",
        "2": "2 estrellas",
        "3": "3 estrellas",
        "4": "4 estrellas",
        "5": "5 estrellas",
        "boutique": "Boutique",
        "luxury": "Luxury",
    }

    name = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código")
    partner_id = fields.Many2one("res.partner", string="Proveedor")
    categoria = fields.Char(string="Categoría")
    categoria_id = fields.Many2one("incas.hotel.categoria", string="Categoría", compute="_compute_categoria_id", inverse="_inverse_categoria_id")
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

    def init(self):
        for codigo, nombre in self._CATEGORIAS_LEGACY.items():
            self.env.cr.execute(
                """
                UPDATE incas_hotel
                   SET categoria = %s
                 WHERE categoria = %s
                """,
                (nombre, codigo),
            )

    def _compute_categoria_id(self):
        categorias = self.env["incas.hotel.categoria"].search([])
        categorias_por_nombre = {categoria.name: categoria for categoria in categorias}
        for record in self:
            nombre = self._CATEGORIAS_LEGACY.get(record.categoria, record.categoria)
            record.categoria_id = categorias_por_nombre.get(nombre, self.env["incas.hotel.categoria"])

    def _inverse_categoria_id(self):
        for record in self:
            record.categoria = record.categoria_id.name or False

    def create(self, vals_list):
        for vals in vals_list:
            categoria_id = vals.get("categoria_id")
            if "categoria_id" in vals and not categoria_id:
                vals["categoria"] = False
            elif categoria_id and not vals.get("categoria"):
                categoria = self.env["incas.hotel.categoria"].browse(categoria_id)
                vals["categoria"] = categoria.name
            vals.pop("categoria_id", None)
        return super().create(vals_list)

    def write(self, vals):
        if "categoria_id" in vals:
            if not vals.get("categoria_id"):
                vals = dict(vals, categoria=False)
            elif not vals.get("categoria"):
                categoria = self.env["incas.hotel.categoria"].browse(vals["categoria_id"])
                vals = dict(vals, categoria=categoria.name)
            vals.pop("categoria_id", None)
        return super().write(vals)
