from odoo import api, fields, models
from odoo.exceptions import UserError


class IncasReservaCambio(models.Model):
    _name = "incas.reserva.cambio"
    _description = "Solicitud de cambio de reserva"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Código", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade", tracking=True)
    partner_id = fields.Many2one(related="reserva_id.partner_id", string="Cliente", store=True, readonly=True)
    tipo_cambio = fields.Selection(
        [("reprogramacion", "Reprogramación"), ("cancelacion", "Cancelación")],
        string="Tipo de cambio",
        required=True,
        default="reprogramacion",
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("solicitado", "Solicitado"),
            ("aprobado", "Aprobado"),
            ("rechazado", "Rechazado"),
            ("aplicado", "Aplicado"),
        ],
        string="Estado",
        required=True,
        default="borrador",
        tracking=True,
    )
    motivo = fields.Text(string="Motivo", required=True, tracking=True)
    fecha_efectiva = fields.Date(string="Fecha efectiva", tracking=True)
    fecha_viaje_anterior = fields.Date(string="Fecha de viaje anterior", readonly=True)
    fecha_viaje_nueva = fields.Date(string="Fecha de viaje nueva")
    fecha_inicio_anterior = fields.Date(string="Fecha de inicio anterior", readonly=True)
    fecha_inicio_nueva = fields.Date(string="Fecha de inicio nueva")
    fecha_fin_anterior = fields.Date(string="Fecha de fin anterior", readonly=True)
    fecha_fin_nueva = fields.Date(string="Fecha de fin nueva")
    turno_anterior = fields.Char(string="Turno anterior", readonly=True)
    turno_nuevo = fields.Char(string="Turno nuevo")
    monto_total_anterior = fields.Float(string="Monto total anterior", readonly=True)
    monto_total_nuevo = fields.Float(string="Monto total nuevo", readonly=True)
    estado_reserva_anterior = fields.Selection(
        selection=[("reservado", "Reservado"), ("por_coordinar", "Por coordinar"), ("falta_pago", "Falta pago"), ("pagado", "Pagado"), ("completado", "Completado"), ("finalizado", "Finalizado"), ("cancelado", "Cancelado")],
        string="Estado anterior",
        readonly=True,
    )
    estado_reserva_nuevo = fields.Selection(
        selection=[("reservado", "Reservado"), ("por_coordinar", "Por coordinar"), ("falta_pago", "Falta pago"), ("pagado", "Pagado"), ("completado", "Completado"), ("finalizado", "Finalizado"), ("cancelado", "Cancelado")],
        string="Estado nuevo",
        readonly=True,
    )
    aprobado_por_id = fields.Many2one("res.users", string="Aprobado por", readonly=True)
    aplicado_por_id = fields.Many2one("res.users", string="Aplicado por", readonly=True)
    fecha_aprobacion = fields.Datetime(string="Fecha de aprobación", readonly=True)
    fecha_aplicacion = fields.Datetime(string="Fecha de aplicación", readonly=True)
    observaciones = fields.Text(string="Observaciones")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.reserva.cambio") or "Nuevo"
            reserva = self.env["incas.reserva"].browse(vals.get("reserva_id"))
            if reserva:
                vals.setdefault("fecha_viaje_anterior", reserva.fecha_viaje)
                vals.setdefault("fecha_inicio_anterior", reserva.fecha_inicio)
                vals.setdefault("fecha_fin_anterior", reserva.fecha_fin)
                vals.setdefault("turno_anterior", reserva.turno)
                vals.setdefault("monto_total_anterior", reserva.monto_total)
                vals.setdefault("estado_reserva_anterior", reserva.estado_reserva)
                if vals.get("tipo_cambio") == "cancelacion":
                    vals.setdefault("estado_reserva_nuevo", "cancelado")
        return super().create(vals_list)

    def action_enviar(self):
        for record in self:
            if record.estado != "borrador":
                continue
            if not record.motivo:
                raise UserError("Debes indicar el motivo para enviar la solicitud.")
            if record.tipo_cambio == "reprogramacion" and not (record.fecha_viaje_nueva or record.fecha_inicio_nueva):
                raise UserError("Debes indicar al menos una fecha nueva para reprogramar.")
            record.estado = "solicitado"

    def action_aprobar(self):
        for record in self:
            if record.estado != "solicitado":
                continue
            record.write(
                {
                    "estado": "aprobado",
                    "aprobado_por_id": self.env.user.id,
                    "fecha_aprobacion": fields.Datetime.now(),
                }
            )

    def action_rechazar(self):
        for record in self:
            if record.estado != "solicitado":
                continue
            record.estado = "rechazado"

    def action_aplicar(self):
        for record in self:
            if record.estado != "aprobado":
                raise UserError("Solo puedes aplicar solicitudes aprobadas.")
            reserva = record.reserva_id.sudo()
            valores = {}
            if record.tipo_cambio == "reprogramacion":
                if record.fecha_viaje_nueva:
                    valores["fecha_viaje"] = record.fecha_viaje_nueva
                if record.fecha_inicio_nueva:
                    valores["fecha_inicio"] = record.fecha_inicio_nueva
                if record.fecha_fin_nueva:
                    valores["fecha_fin"] = record.fecha_fin_nueva
                if record.turno_nuevo:
                    valores["turno"] = record.turno_nuevo
            else:
                valores["estado_reserva"] = "cancelado"
            if valores:
                reserva.write(valores)
            if hasattr(reserva, "_sincronizar_evento_operativo"):
                reserva._sincronizar_evento_operativo()
            record.write(
                {
                    "estado": "aplicado",
                    "aplicado_por_id": self.env.user.id,
                    "fecha_aplicacion": fields.Datetime.now(),
                    "monto_total_nuevo": reserva.monto_total,
                    "estado_reserva_nuevo": reserva.estado_reserva,
                }
            )

    def action_ir_reserva(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reserva",
            "res_model": "incas.reserva",
            "view_mode": "form",
            "res_id": self.reserva_id.id,
            "target": "current",
        }
