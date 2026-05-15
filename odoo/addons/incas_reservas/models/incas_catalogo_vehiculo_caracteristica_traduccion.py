from odoo import api, fields, models


class IncasCatalogoVehiculoCaracteristicaTraduccion(models.Model):
    _name = "incas.catalogo.vehiculo.caracteristica.traduccion"
    _description = "Traducción de característica de vehículo"
    _order = "idioma_id, id"

    caracteristica_id = fields.Many2one(
        "incas.catalogo.vehiculo.caracteristica",
        string="Característica",
        required=True,
        ondelete="cascade",
    )
    idioma_id = fields.Many2one(
        "incas.idioma",
        string="Idioma",
        required=True,
        ondelete="restrict",
    )
    titulo = fields.Char(string="Título")
    descripcion = fields.Html(string="Descripción")

    _sql_constraints = [
        (
            "incas_catalogo_vehiculo_car_traduccion_unique",
            "unique(caracteristica_id, idioma_id)",
            "Ya existe una traducción para este idioma en la característica.",
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
        self.env["incas.catalogo.vehiculo.caracteristica"]._migrar_columnas_legadas_jsonb()
        for record in self:
            if not record.idioma_id.por_defecto:
                continue
            record.caracteristica_id.with_context(skip_sync_traducciones=True).write(
                {
                    "titulo": record.titulo,
                    "descripcion": record.descripcion,
                }
            )
