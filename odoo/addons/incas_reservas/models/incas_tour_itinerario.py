from odoo import api, fields, models


class IncasTourItinerario(models.Model):
    _name = "incas.tour.itinerario"
    _description = "Item de itinerario de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    tour_id = fields.Many2one("incas.tour", string="Tour", required=True, ondelete="cascade")
    titulo = fields.Html(string="Titulo")
    titulo_en = fields.Html(string="Titulo en ingles")
    titulo_pt = fields.Html(string="Titulo en portugues")
    descripcion = fields.Html(string="Descripcion")
    descripcion_en = fields.Html(string="Descripcion en ingles")
    descripcion_pt = fields.Html(string="Descripcion en portugues")
    imagen_ids = fields.One2many(
        "incas.tour.itinerario.imagen",
        "itinerario_id",
        string="Imagenes",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            for campo in ("titulo", "descripcion"):
                if vals.get(campo) and not vals.get(f"{campo}_en"):
                    vals[f"{campo}_en"] = vals[campo]
                if vals.get(campo) and not vals.get(f"{campo}_pt"):
                    vals[f"{campo}_pt"] = vals[campo]
        records = super().create(vals_list)
        records.mapped("tour_id")._sincronizar_servicio_operativo()
        return records

    def write(self, vals):
        valores = dict(vals)
        for campo in ("titulo", "descripcion"):
            if campo in valores:
                if f"{campo}_en" not in valores and any(not record[f"{campo}_en"] for record in self):
                    valores[f"{campo}_en"] = valores[campo]
                if f"{campo}_pt" not in valores and any(not record[f"{campo}_pt"] for record in self):
                    valores[f"{campo}_pt"] = valores[campo]
        result = super().write(valores)
        self.mapped("tour_id")._sincronizar_servicio_operativo()
        return result

    def unlink(self):
        tours = self.mapped("tour_id")
        result = super().unlink()
        tours._sincronizar_servicio_operativo()
        return result
