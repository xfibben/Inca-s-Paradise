import json

from odoo import fields, models


class IncasCatalogoVehiculo(models.Model):
    _name = "incas.catalogo.vehiculo"
    _description = "Catálogo local de vehículos"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    descripcion = fields.Text(string="Descripción")
    imagen_data = fields.Text(string="Imagen")
    nro_asientos = fields.Integer(string="Nro. asientos")
    features_data = fields.Text(string="Features")
    transporte_tarifa_ids = fields.One2many(
        "incas.catalogo.transporte.tarifa",
        "vehiculo_id",
        string="Tarifas de transporte",
    )
    active = fields.Boolean(default=True)

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)
