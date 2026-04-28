import json

from odoo import fields, models


class IncasCatalogoVehiculo(models.Model):
    _name = "incas.catalogo.vehiculo"
    _description = "Catálogo local de vehículos"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    strapi_id = fields.Integer(string="ID Strapi", required=True, index=True)
    strapi_document_id = fields.Char(string="Document ID Strapi")
    descripcion = fields.Text(string="Descripción")
    imagen_data = fields.Text(string="Imagen")
    nro_asientos = fields.Integer(string="Nro. asientos")
    features_data = fields.Text(string="Features")
    active = fields.Boolean(default=True)

    _incas_catalogo_vehiculo_strapi_unique = models.Constraint(
        "UNIQUE(strapi_id)",
        "El vehículo ya existe en el catálogo.",
    )

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)
