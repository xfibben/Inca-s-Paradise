from odoo import api, fields, models


class IncasTourNoIncluido(models.Model):
    _name = "incas.tour.no.incluido"
    _description = "Item no incluido de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    tour_id = fields.Many2one("incas.tour", string="Tour", required=True, ondelete="cascade")
    titulo = fields.Html(string="Título")
    titulo_en = fields.Html(string="Título en inglés")
    titulo_pt = fields.Html(string="Título en portugués")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("titulo") and not vals.get("titulo_en"):
                vals["titulo_en"] = vals["titulo"]
            if vals.get("titulo") and not vals.get("titulo_pt"):
                vals["titulo_pt"] = vals["titulo"]
        return super().create(vals_list)

    def write(self, vals):
        valores = dict(vals)
        if "titulo" in valores:
            if "titulo_en" not in valores and any(not record.titulo_en for record in self):
                valores["titulo_en"] = valores["titulo"]
            if "titulo_pt" not in valores and any(not record.titulo_pt for record in self):
                valores["titulo_pt"] = valores["titulo"]
        return super().write(valores)
