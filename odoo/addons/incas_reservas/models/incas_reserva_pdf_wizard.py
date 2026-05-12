from odoo import fields, models


class IncasReservaPdfWizard(models.TransientModel):
    _name = "incas.reserva.pdf.wizard"
    _description = "Wizard para exportar voucher de reserva"

    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True)
    idioma = fields.Selection(
        [
            ("es", "Español"),
            ("en", "Inglés"),
            ("pt", "Portugués"),
        ],
        string="Idioma",
        required=True,
        default="es",
    )

    def action_exportar_pdf(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/reserva/{self.reserva_id.id}/pdf?idioma={self.idioma}",
            "target": "self",
        }
