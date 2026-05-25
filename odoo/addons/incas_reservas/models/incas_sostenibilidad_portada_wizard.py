from odoo import fields, models


class IncasSostenibilidadPortadaWizard(models.TransientModel):
    _name = "incas.sostenibilidad.portada.wizard"
    _description = "Confirmacion de reemplazo en portada"

    articulo_id = fields.Many2one("incas.sostenibilidad.articulo", string="Articulo", required=True, readonly=True)
    articulo_antiguo_id = fields.Many2one("incas.sostenibilidad.articulo", string="Articulo a reemplazar", readonly=True)
    mensaje = fields.Text(string="Mensaje", readonly=True)

    def action_confirmar(self):
        self.ensure_one()
        self.articulo_id.with_context(sostenibilidad_confirmar_portada=True)._activar_en_portada()
        return {"type": "ir.actions.act_window_close"}
