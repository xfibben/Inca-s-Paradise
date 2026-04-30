from datetime import datetime, time, timedelta

from odoo import api, fields, models


class IncasReserva(models.Model):
    _inherit = "incas.reserva"

    agenda_evento_ids = fields.One2many("incas.agenda.evento", "reserva_id", string="Eventos operativos")

    def _fecha_inicio_agenda(self):
        self.ensure_one()
        fecha = self.fecha_inicio or self.fecha_viaje or fields.Date.context_today(self)
        return fields.Datetime.to_string(datetime.combine(fecha, time(hour=9, minute=0)))

    def _fecha_fin_agenda(self):
        self.ensure_one()
        fecha = self.fecha_fin or self.fecha_inicio or self.fecha_viaje or fields.Date.context_today(self)
        return fields.Datetime.to_string(datetime.combine(fecha, time(hour=11, minute=0)))

    def _nombre_evento_reserva(self):
        self.ensure_one()
        codigo = self.ticket or self.name or f"RES-{self.id}"
        servicio = self.servicio_nombre or "Servicio"
        return f"{codigo} - {servicio}"

    def _valores_evento_reserva(self):
        self.ensure_one()
        estado = "cancelado" if self.estado_reserva == "cancelado" else "confirmado"
        return {
            "name": self._nombre_evento_reserva(),
            "tipo_evento": "reserva",
            "fecha_inicio": self._fecha_inicio_agenda(),
            "fecha_fin": self._fecha_fin_agenda(),
            "all_day": True,
            "partner_id": self.partner_id.id,
            "responsable_id": (self.responsable_id or self.env.user).id,
            "estado": estado,
            "reserva_id": self.id,
            "notas": self.observaciones or False,
        }

    def _sincronizar_evento_operativo(self):
        evento_model = self.env["incas.agenda.evento"].sudo()
        for reserva in self:
            evento = evento_model.search([("reserva_id", "=", reserva.id), ("tipo_evento", "=", "reserva")], limit=1)
            valores = reserva._valores_evento_reserva()
            if evento:
                evento.write(valores)
            else:
                evento_model.create(valores)

    @api.model_create_multi
    def create(self, vals_list):
        reservas = super().create(vals_list)
        reservas._sincronizar_evento_operativo()
        return reservas

    def write(self, vals):
        result = super().write(vals)
        campos_sync = {
            "ticket",
            "name",
            "servicio_nombre",
            "fecha_inicio",
            "fecha_fin",
            "fecha_viaje",
            "estado_reserva",
            "partner_id",
            "responsable_id",
            "observaciones",
        }
        if campos_sync.intersection(vals.keys()):
            self._sincronizar_evento_operativo()
        return result
