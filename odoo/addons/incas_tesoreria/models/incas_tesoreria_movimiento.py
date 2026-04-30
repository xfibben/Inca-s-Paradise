from odoo import fields, models


class IncasTesoreriaMovimiento(models.Model):
    _name = "incas.tesoreria.movimiento"
    _description = "Movimiento de tesoreria"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default="Nuevo", tracking=True)
    fecha = fields.Date(string="Fecha", required=True, default=fields.Date.context_today, tracking=True)
    tipo = fields.Selection(
        [("ingreso", "Ingreso"), ("egreso", "Egreso")],
        string="Tipo",
        required=True,
        default="ingreso",
        tracking=True,
    )
    categoria = fields.Selection(
        [
            ("reserva", "Reserva"),
            ("proveedor", "Proveedor"),
            ("operacion", "Operación"),
            ("administrativo", "Administrativo"),
            ("otro", "Otro"),
        ],
        string="Categoría",
        required=True,
        default="otro",
        tracking=True,
    )
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", ondelete="set null", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente/Proveedor", ondelete="set null", tracking=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="PEN",
        tracking=True,
    )
    monto = fields.Float(string="Monto", required=True, tracking=True)
    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("confirmado", "Confirmado"),
            ("anulado", "Anulado"),
        ],
        string="Estado",
        required=True,
        default="borrador",
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", required=True, default=lambda self: self.env.user, tracking=True)
    descripcion = fields.Text(string="Descripción")
    active = fields.Boolean(default=True)

    def action_confirmar(self):
        for record in self.filtered(lambda r: r.estado == "borrador"):
            record.estado = "confirmado"

    def action_anular(self):
        for record in self.filtered(lambda r: r.estado != "anulado"):
            record.estado = "anulado"
