from odoo import api, fields, models


class IncasEstiloTour(models.Model):
    _name = "incas.estilo.tour"
    _description = "Estilo de tour"
    _order = "nombre, id"

    nombre = fields.Char(string="Nombre", required=True)
    nombre_en = fields.Char(string="Nombre en inglés")
    nombre_pt = fields.Char(string="Nombre en portugués")
    slug = fields.Char(string="Slug", required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("incas_estilo_tour_slug_unique", "unique(slug)", "El slug del estilo ya existe."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("nombre") and not vals.get("nombre_en"):
                vals["nombre_en"] = vals["nombre"]
            if vals.get("nombre") and not vals.get("nombre_pt"):
                vals["nombre_pt"] = vals["nombre"]
        return super().create(vals_list)

    def write(self, vals):
        valores = dict(vals)
        if "nombre" in valores:
            if "nombre_en" not in valores and any(not record.nombre_en for record in self):
                valores["nombre_en"] = valores["nombre"]
            if "nombre_pt" not in valores and any(not record.nombre_pt for record in self):
                valores["nombre_pt"] = valores["nombre"]
        return super().write(valores)

    @api.onchange("nombre")
    def _onchange_copiar_nombre(self):
        for record in self:
            if record.nombre and not record.nombre_en:
                record.nombre_en = record.nombre
            if record.nombre and not record.nombre_pt:
                record.nombre_pt = record.nombre
