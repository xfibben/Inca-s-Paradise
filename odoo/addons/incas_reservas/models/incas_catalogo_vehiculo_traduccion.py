from odoo import api, fields, models


class IncasCatalogoVehiculoTraduccion(models.Model):
    _name = "incas.catalogo.vehiculo.traduccion"
    _description = "Traducción de vehículo"
    _order = "idioma_id, id"

    vehiculo_id = fields.Many2one(
        "incas.catalogo.vehiculo",
        string="Vehículo",
        required=True,
        ondelete="cascade",
    )
    idioma_id = fields.Many2one(
        "incas.idioma",
        string="Idioma",
        required=True,
        ondelete="restrict",
    )
    nombre = fields.Char(string="Nombre")
    descripcion = fields.Html(string="Descripción")

    _sql_constraints = [
        (
            "incas_catalogo_vehiculo_traduccion_unique",
            "unique(vehiculo_id, idioma_id)",
            "Ya existe una traducción para este idioma en el vehículo.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sincronizar_hacia_base()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._sincronizar_hacia_base()
        return result

    def _sincronizar_hacia_base(self):
        self.env["incas.catalogo.vehiculo"]._migrar_columnas_legadas_jsonb()
        for record in self:
            if not record.idioma_id.por_defecto:
                continue
            record.vehiculo_id.with_context(skip_sync_traducciones=True).write(
                {
                    "nombre": record.nombre,
                    "descripcion": record.descripcion,
                }
            )
