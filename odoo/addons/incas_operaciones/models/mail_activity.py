from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    estado_ejecucion = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("en_progreso", "En progreso"),
            ("finalizada", "Finalizada"),
        ],
        string="Estado de ejecución",
        default="pendiente",
        copy=False,
    )
    fecha_hora_inicio = fields.Datetime(string="Inicio", copy=False, readonly=True)
    fecha_hora_fin = fields.Datetime(string="Fin", copy=False, readonly=True)
    duracion_minutos = fields.Integer(string="Duración en minutos", copy=False, readonly=True)
    duracion_horas = fields.Float(string="Duración en horas", digits=(16, 2), copy=False, readonly=True)

    def action_iniciar_actividad(self):
        ahora = fields.Datetime.now()
        actividades = self.filtered(lambda activity: activity.active and activity.estado_ejecucion == "pendiente")
        if actividades:
            actividades.write(
                {
                    "estado_ejecucion": "en_progreso",
                    "fecha_hora_inicio": ahora,
                    "fecha_hora_fin": False,
                    "duracion_minutos": 0,
                    "duracion_horas": 0,
                }
            )
        return {"type": "ir.actions.client", "tag": "reload"}

    def _registrar_cierre_actividad(self):
        ahora = fields.Datetime.now()
        for activity in self.filtered("active"):
            if activity.estado_ejecucion == "finalizada":
                continue
            inicio = activity.fecha_hora_inicio or ahora
            duracion_segundos = max((ahora - inicio).total_seconds(), 0)
            activity.write(
                {
                    "estado_ejecucion": "finalizada",
                    "fecha_hora_inicio": inicio,
                    "fecha_hora_fin": ahora,
                    "duracion_minutos": int(duracion_segundos // 60),
                    "duracion_horas": round(duracion_segundos / 3600, 2),
                }
            )

    def action_concluir_actividad(self):
        self._registrar_cierre_actividad()
        return super().action_done()

    def action_feedback(self, feedback=False, attachment_ids=None):
        self._registrar_cierre_actividad()
        return super().action_feedback(feedback=feedback, attachment_ids=attachment_ids)
