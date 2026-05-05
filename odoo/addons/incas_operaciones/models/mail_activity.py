from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    _REVISOR_TAREAS_EMAIL = "incasparadise@gmail.com"

    def _auto_init(self):
        res = super()._auto_init()
        self.env.cr.execute(
            """
            ALTER TABLE mail_activity
            ADD COLUMN IF NOT EXISTS es_revision_tarea boolean DEFAULT FALSE
            """
        )
        self.env.cr.execute(
            """
            ALTER TABLE mail_activity
            ADD COLUMN IF NOT EXISTS tarea_origen_id integer
            """
        )
        self.env.cr.execute(
            """
            UPDATE mail_activity
               SET es_revision_tarea = FALSE
             WHERE es_revision_tarea IS NULL
            """
        )
        self.env.cr.execute(
            """
            UPDATE mail_activity
               SET active = FALSE
             WHERE es_revision_tarea = TRUE
               AND active = TRUE
            """
        )
        self.env.cr.execute(
            """
            UPDATE mail_activity
               SET revision_tarea = 'por_revisar'
             WHERE revision_tarea IS NULL
            """
        )
        return res

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
    revision_tarea = fields.Selection(
        [
            ("por_revisar", "Falta revisar"),
            ("aprobado", "Aprobado"),
            ("observado", "Observado"),
        ],
        string="Estado de revisión",
        default="por_revisar",
        copy=False,
    )
    observacion_tarea = fields.Text(string="Comentario", copy=False)
    es_revision_tarea = fields.Boolean(string="Es revisión de tarea", default=False, copy=False)
    tarea_origen_id = fields.Many2one("mail.activity", string="Tarea revisada", copy=False, readonly=True)

    def _obtener_usuario_revisor_tarea(self):
        return self.env["res.users"].sudo().search(
            [
                "|",
                ("login", "=", self._REVISOR_TAREAS_EMAIL),
                ("email", "=", self._REVISOR_TAREAS_EMAIL),
            ],
            limit=1,
        )

    def _crear_actividad_revision_tarea(self):
        usuario_revisor = self._obtener_usuario_revisor_tarea()
        if not usuario_revisor:
            return
        tipo_actividad = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        modelo_partner = self.env.ref("base.model_res_partner", raise_if_not_found=False)
        if not tipo_actividad:
            return
        if not modelo_partner or not usuario_revisor.partner_id:
            return
        actividades_revision = self.env["mail.activity"].sudo()
        for activity in self.filtered(lambda item: item.id and not item.es_revision_tarea):
            existente = actividades_revision.search(
                [
                    ("user_id", "=", usuario_revisor.id),
                    ("es_revision_tarea", "=", True),
                    ("tarea_origen_id", "=", activity.id),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if existente:
                continue
            actividades_revision.create(
                {
                    "res_model_id": modelo_partner.id,
                    "res_id": usuario_revisor.partner_id.id,
                    "activity_type_id": tipo_actividad.id,
                    "user_id": usuario_revisor.id,
                    "summary": "Revisar tarea finalizada",
                    "note": (
                        f"Tarea finalizada por {activity.user_id.name or 'Sin asignar'}"
                        f"<br/>Actividad: {activity.summary or activity.activity_type_id.name or 'Sin asunto'}"
                        f"<br/>Registro origen: {activity.res_name or 'Sin registro'}"
                    ),
                    "date_deadline": fields.Date.context_today(activity),
                    "es_revision_tarea": True,
                    "tarea_origen_id": activity.id,
                }
            )

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
                    "revision_tarea": "por_revisar",
                    "fecha_hora_inicio": inicio,
                    "fecha_hora_fin": ahora,
                    "duracion_minutos": int(duracion_segundos // 60),
                    "duracion_horas": round(duracion_segundos / 3600, 2),
                }
            )

    def action_concluir_actividad(self):
        self._registrar_cierre_actividad()
        return super().action_done()

    def action_aprobar_tarea(self):
        self.write({"revision_tarea": "aprobado"})
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_desaprobar_tarea(self):
        self.write({"revision_tarea": "por_revisar"})
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_observar_tarea(self):
        self.write(
            {
                "revision_tarea": "observado",
                "estado_ejecucion": "pendiente",
                "active": True,
                "fecha_hora_inicio": False,
                "fecha_hora_fin": False,
                "duracion_minutos": 0,
                "duracion_horas": 0,
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_feedback(self, feedback=False, attachment_ids=None):
        self._registrar_cierre_actividad()
        return super().action_feedback(feedback=feedback, attachment_ids=attachment_ids)

    def action_abrir_tarea_origen(self):
        self.ensure_one()
        tarea_origen = self.tarea_origen_id
        if not tarea_origen:
            return {"type": "ir.actions.client", "tag": "reload"}
        return {
            "type": "ir.actions.act_window",
            "name": "Tarea revisada",
            "res_model": "mail.activity",
            "res_id": tarea_origen.id,
            "view_mode": "form",
            "target": "new",
        }
