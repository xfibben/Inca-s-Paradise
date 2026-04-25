import json

from odoo import fields, models


class IncasCatalogoTransporte(models.Model):
    _name = "incas.catalogo.transporte"
    _description = "Catálogo local de transportes"
    _inherits = {"incas.servicio.catalogo": "servicio_id"}
    _order = "name"

    servicio_id = fields.Many2one("incas.servicio.catalogo", string="Servicio base", required=True, ondelete="cascade")
    image_data = fields.Text(string="Imagen")
    wallpaper_data = fields.Text(string="Wallpaper")
    destino_origen_data = fields.Text(string="Destino origen")
    destino_llegada_data = fields.Text(string="Destino llegada")
    modelo_vehiculo = fields.Char(string="Modelo de vehículo")
    duracion_viaje = fields.Char(string="Duración del viaje")
    distancia = fields.Char(string="Distancia")
    descripcion_origen = fields.Text(string="Descripción origen")
    descripcion_llegada = fields.Text(string="Descripción llegada")
    descripcion = fields.Text(string="Descripción")
    included_title = fields.Char(string="Included title")
    included_items_data = fields.Text(string="Included items")
    excluded_title = fields.Char(string="Excluded title")
    excluded_items_data = fields.Text(string="Excluded items")
    tipos_transporte_data = fields.Text(string="Tipos de transporte")
    seo_title = fields.Char(string="SEO title")
    seo_description = fields.Text(string="SEO description")
    precios_data = fields.Text(string="Precios por vehículo")

    _sql_constraints = [
        ("incas_catalogo_transporte_servicio_unique", "unique(servicio_id)", "El transporte ya está vinculado a un servicio."),
    ]

    def action_sync_from_strapi(self):
        self.env["incas.servicio.catalogo"].sync_from_strapi()
        return True

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)
