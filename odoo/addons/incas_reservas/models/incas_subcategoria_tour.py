from odoo import fields, models


class IncasSubcategoriaTour(models.Model):
    _name = "incas.subcategoria.tour"
    _description = "Subcategoría de tour por destino"
    _order = "sequence, nombre, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    nombre = fields.Char(string="Nombre", required=True)
    destino_id = fields.Many2one(
        "incas.catalogo.destino",
        string="Destino",
        required=True,
        ondelete="cascade",
    )
    tour_ids = fields.Many2many(
        "incas.tour",
        "incas_subcategoria_tour_web_tour_rel",
        "subcategoria_id",
        "tour_id",
        string="Tours",
    )
    active = fields.Boolean(default=True)
