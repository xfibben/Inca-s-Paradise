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
    categoria = fields.Char(string="Categoría legacy")
    categoria_id = fields.Many2one("incas.hotel.categoria", string="Categoría", ondelete="restrict")
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
        self.env.cr.execute(
            """
            INSERT INTO incas_hotel_categoria (name, sequence, active, create_uid, create_date, write_uid, write_date)
            SELECT data.name, data.sequence, TRUE, 1, NOW(), 1, NOW()
            FROM (
                VALUES
                    ('1 estrella', 10),
                    ('2 estrellas', 20),
                    ('3 estrellas', 30),
                    ('4 estrellas', 40),
                    ('5 estrellas', 50),
                    ('Boutique', 60),
                    ('Luxury', 70)
            ) AS data(name, sequence)
            WHERE NOT EXISTS (
                SELECT 1
                FROM incas_hotel_categoria categoria
                WHERE categoria.name = data.name
            )
            """
        )
        for codigo, nombre in self._CATEGORIAS_LEGACY.items():
            self.env.cr.execute(
                """
                UPDATE incas_hotel hotel
                   SET categoria_id = categoria.id
                  FROM incas_hotel_categoria categoria
                 WHERE hotel.categoria = %s
                   AND categoria.name = %s
                   AND hotel.categoria_id IS NULL
                """,
                (codigo, nombre),
            )

    def create(self, vals_list):
        for vals in vals_list:
            categoria_id = vals.get("categoria_id")
            if "categoria_id" in vals and not categoria_id:
                vals["categoria"] = False
            elif categoria_id and not vals.get("categoria"):
                categoria = self.env["incas.hotel.categoria"].browse(categoria_id)
                vals["categoria"] = categoria.name
        return super().create(vals_list)

    def write(self, vals):
        if "categoria_id" in vals:
            if not vals.get("categoria_id"):
                vals = dict(vals, categoria=False)
            elif not vals.get("categoria"):
                categoria = self.env["incas.hotel.categoria"].browse(vals["categoria_id"])
                vals = dict(vals, categoria=categoria.name)
        return super().write(vals)
