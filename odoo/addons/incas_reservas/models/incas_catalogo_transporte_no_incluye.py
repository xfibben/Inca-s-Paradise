from odoo import api, fields, models


class IncasCatalogoTransporteNoIncluye(models.Model):
    _name = "incas.catalogo.transporte.no.incluye"
    _description = "No incluye de transporte"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    transporte_id = fields.Many2one(
        "incas.catalogo.transporte",
        string="Transporte",
        required=True,
        ondelete="cascade",
    )
    texto = fields.Char(string="Texto", required=True, default="Nuevo item")
    texto_en = fields.Char(string="Texto en inglés")
    texto_pt = fields.Char(string="Texto en portugués")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

    def _autocompletar_traducciones_en_vals(self, vals):
        texto = vals.get("texto")
        if texto and not vals.get("texto_en"):
            vals["texto_en"] = texto
        if texto and not vals.get("texto_pt"):
            vals["texto_pt"] = texto

    def _completar_traducciones_vacias(self):
        for record in self:
            valores = {}
            if record.texto and not record.texto_en:
                valores["texto_en"] = record.texto
            if record.texto and not record.texto_pt:
                valores["texto_pt"] = record.texto
            if valores:
                record.with_context(skip_autocompletar_traducciones=True).write(valores)

    @api.onchange("texto")
    def _onchange_autocompletar_traducciones(self):
        for record in self:
            if record.texto and not record.texto_en:
                record.texto_en = record.texto
            if record.texto and not record.texto_pt:
                record.texto_pt = record.texto
