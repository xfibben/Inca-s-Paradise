import json

from odoo import fields, models


class IncasCatalogoVehiculo(models.Model):
    _name = "incas.catalogo.vehiculo"
    _description = "Catálogo local de vehículos"
    _order = "nombre"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre", required=True)
    descripcion = fields.Text(string="Descripción")
    imagen = fields.Text(string="Imagen")
    numero_asientos = fields.Integer(string="Número de asientos")
    caracteristica_ids = fields.One2many(
        "incas.catalogo.vehiculo.caracteristica",
        "vehiculo_id",
        string="Características",
    )
    tarifa_transporte_ids = fields.One2many(
        "incas.catalogo.transporte.tarifa",
        "vehiculo_id",
        string="Tarifas de transporte",
    )
    active = fields.Boolean(string="Activo", default=True)

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)
