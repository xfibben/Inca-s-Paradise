from odoo import fields, models


class IncasHotelCategoria(models.Model):
    _name = "incas.hotel.categoria"
    _description = "Categoría de hotel"
    _order = "sequence, name, id"

    name = fields.Char(string="Nombre", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    active = fields.Boolean(default=True)

    def init(self):
        self.env.cr.execute("SELECT to_regclass('incas_hotel_categoria')")
        if not self.env.cr.fetchone()[0]:
            return
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
