from odoo import api, fields, models


class IncasSostenibilidadEtiqueta(models.Model):
    _name = "incas.sostenibilidad.etiqueta"
    _description = "Etiqueta de sostenibilidad"
    _order = "name, id"
    _rec_name = "name"

    name = fields.Char(string="Etiqueta", required=True, index=True)
    articulo_ids = fields.Many2many(
        "incas.sostenibilidad.articulo",
        "incas_sostenibilidad_articulo_etiqueta_rel",
        "etiqueta_id",
        "articulo_id",
        string="Articulos",
    )

    _sql_constraints = [
        ("incas_sostenibilidad_etiqueta_name_unique", "unique(name)", "La etiqueta ya existe."),
    ]

    @api.model
    def _normalizar_nombre(self, valor):
        if not isinstance(valor, str):
            return valor
        valor = " ".join(valor.split())
        return valor.upper() if valor else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" in vals:
                vals["name"] = self._normalizar_nombre(vals["name"])
        return super().create(vals_list)

    def write(self, vals):
        valores = dict(vals)
        if "name" in valores:
            valores["name"] = self._normalizar_nombre(valores["name"])
        return super().write(valores)
