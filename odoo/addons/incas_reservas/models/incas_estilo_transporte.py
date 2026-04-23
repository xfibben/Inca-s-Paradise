from odoo import fields, models


class IncasEstiloTransporte(models.Model):
    _name = "incas.estilo.transporte"
    _description = "Estilo de transporte"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    strapi_id = fields.Integer(string="ID Strapi", required=True, index=True)
    slug = fields.Char(string="Slug")
    active = fields.Boolean(default=True)

    _incas_estilo_transporte_strapi_unique = models.Constraint(
        "UNIQUE(strapi_id)",
        "El estilo de transporte ya existe.",
    )
