from odoo import fields, models


class IncasEstiloTransporte(models.Model):
    _name = "incas.estilo.transporte"
    _description = "Estilo de transporte"
    _order = "nro_orden, name"

    name = fields.Char(string="Nombre", required=True)
    slug = fields.Char(string="Slug")
    descripcion = fields.Text(string="Descripción")
    image_data = fields.Text(string="Imagen")
    wallpaper_data = fields.Text(string="Wallpaper")
    nro_orden = fields.Integer(string="Nro. orden", default=0)
    active = fields.Boolean(default=True)
