from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasIdioma(models.Model):
    _name = "incas.idioma"
    _description = "Idioma"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    nombre = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código", required=True)
    activo = fields.Boolean(string="Activo", default=True)
    por_defecto = fields.Boolean(string="Por defecto", default=False)

    _sql_constraints = [
        ("incas_idioma_codigo_unique", "unique(codigo)", "El código del idioma ya existe."),
    ]

    def name_get(self):
        return [(record.id, record.nombre) for record in self]

    @api.constrains("por_defecto", "activo")
    def _check_por_defecto(self):
        for record in self:
            if record.por_defecto and not record.activo:
                raise ValidationError("El idioma por defecto debe estar activo.")
        idiomas_defecto = self.search([("por_defecto", "=", True)])
        if len(idiomas_defecto) > 1:
            raise ValidationError("Solo puede existir un idioma por defecto.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("por_defecto"):
                self.search([("por_defecto", "=", True)]).write({"por_defecto": False})
        self._asegurar_columnas_multilenguaje()
        records = super().create(vals_list)
        records._sincronizar_base_desde_traducciones_defecto()
        records._sincronizar_traducciones_relacionadas()
        return records

    def write(self, vals):
        if vals.get("por_defecto"):
            self.search([("por_defecto", "=", True), ("id", "not in", self.ids)]).write({"por_defecto": False})
        self._asegurar_columnas_multilenguaje()
        result = super().write(vals)
        if "por_defecto" in vals or "activo" in vals:
            self._sincronizar_base_desde_traducciones_defecto()
        self._sincronizar_traducciones_relacionadas()
        return result

    def _asegurar_columnas_multilenguaje(self):
        self.env["incas.catalogo.vehiculo"]._migrar_columnas_legadas_jsonb()
        self.env["incas.catalogo.vehiculo.caracteristica"]._migrar_columnas_legadas_jsonb()

    def _sincronizar_traducciones_relacionadas(self):
        self.env["incas.catalogo.vehiculo"].search([])._asegurar_traducciones_idiomas()
        self.env["incas.catalogo.vehiculo.caracteristica"].search([])._asegurar_traducciones_idiomas()

    def _sincronizar_base_desde_traducciones_defecto(self):
        idiomas_defecto = self.filtered(lambda item: item.por_defecto and item.activo)
        if not idiomas_defecto:
            return
        traducciones_vehiculo = self.env["incas.catalogo.vehiculo.traduccion"].search(
            [("idioma_id", "in", idiomas_defecto.ids)]
        )
        traducciones_caracteristica = self.env["incas.catalogo.vehiculo.caracteristica.traduccion"].search(
            [("idioma_id", "in", idiomas_defecto.ids)]
        )
        traducciones_vehiculo._sincronizar_hacia_base()
        traducciones_caracteristica._sincronizar_hacia_base()
