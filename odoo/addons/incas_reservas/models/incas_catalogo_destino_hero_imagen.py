from odoo import fields, models


class IncasCatalogoDestinoHeroImagen(models.Model):
    _name = "incas.catalogo.destino.hero.imagen"
    _description = "Imagen hero de destino"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    destino_id = fields.Many2one(
        "incas.catalogo.destino",
        string="Destino",
        required=True,
        ondelete="cascade",
    )
    imagen = fields.Image(string="Imagen", required=True)
