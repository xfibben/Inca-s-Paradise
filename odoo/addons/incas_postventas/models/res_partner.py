from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    incas_documento = fields.Char(string="Documento / pasaporte")
    incas_idioma = fields.Selection(
        [
            ("es", "Espanol"),
            ("en", "Ingles"),
            ("fr", "Frances"),
            ("pt", "Portugues"),
            ("it", "Italiano"),
        ],
        string="Idioma preferido",
    )
    incas_cumpleanos = fields.Date(string="Cumpleanos")
    incas_preferencias = fields.Text(string="Preferencias")
    incas_restricciones = fields.Text(string="Restricciones")
    incas_satisfaccion_promedio = fields.Float(string="Satisfaccion promedio", compute="_compute_incas_postventa", store=True)
    incas_ultima_encuesta = fields.Datetime(string="Ultima encuesta", compute="_compute_incas_postventa", store=True)
    incas_reserva_count = fields.Integer(string="Reservas", compute="_compute_incas_counts")

    @api.depends("incas_postventa_encuesta_ids.satisfaccion_general", "incas_postventa_encuesta_ids.fecha_respuesta")
    def _compute_incas_postventa(self):
        encuesta_model = self.env["incas.postventa.encuesta"]
        for partner in self:
            encuestas = encuesta_model.search([("partner_id", "=", partner.id), ("estado", "=", "respondida")])
            valores = [encuesta.satisfaccion_general for encuesta in encuestas if encuesta.satisfaccion_general]
            partner.incas_satisfaccion_promedio = sum(valores) / len(valores) if valores else 0
            partner.incas_ultima_encuesta = max(encuestas.mapped("fecha_respuesta")) if encuestas else False

    def _compute_incas_counts(self):
        reserva_model = self.env["incas.reserva"]
        for partner in self:
            partner.incas_reserva_count = reserva_model.search_count([("partner_id", "=", partner.id)])

    incas_postventa_encuesta_ids = fields.One2many("incas.postventa.encuesta", "partner_id", string="Encuestas postventa")
