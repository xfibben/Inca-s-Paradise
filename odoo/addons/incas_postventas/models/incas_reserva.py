from odoo import fields, models


class IncasReserva(models.Model):
    _inherit = "incas.reserva"

    postventa_caso_ids = fields.One2many("incas.postventa.caso", "reserva_id", string="Casos postventa")
    postventa_caso_count = fields.Integer(string="Postventa", compute="_compute_postventa_caso_count")

    def _compute_postventa_caso_count(self):
        for record in self:
            record.postventa_caso_count = len(record.postventa_caso_ids)

    def _crear_caso_postventa_si_corresponde(self):
        caso_model = self.env["incas.postventa.caso"]
        for reserva in self.filtered(lambda item: item.estado_reserva == "finalizado"):
            if not reserva.postventa_caso_ids:
                caso_model.create({"reserva_id": reserva.id})

    def write(self, vals):
        result = super().write(vals)
        if vals.get("estado_reserva") == "finalizado":
            self._crear_caso_postventa_si_corresponde()
        return result

    def action_crear_caso_postventa(self):
        self.ensure_one()
        if not self.postventa_caso_ids:
            self.env["incas.postventa.caso"].create({"reserva_id": self.id})
        caso = self.postventa_caso_ids[:1]
        return {
            "type": "ir.actions.act_window",
            "name": "Caso post viaje",
            "res_model": "incas.postventa.caso",
            "view_mode": "form",
            "res_id": caso.id,
            "context": {"default_reserva_id": self.id},
        }
