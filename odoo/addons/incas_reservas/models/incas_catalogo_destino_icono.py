from odoo import fields, models


class IncasCatalogoDestinoIcono(models.Model):
    _name = "incas.catalogo.destino.icono"
    _description = "Icono de destino"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    destino_id = fields.Many2one(
        "incas.catalogo.destino",
        string="Destino",
        required=True,
        ondelete="cascade",
    )
    titulo = fields.Html(string="Título")
    titulo_en = fields.Html(string="Título en inglés")
    titulo_pt = fields.Html(string="Título en portugués")
    imagen = fields.Image(string="Imagen")
