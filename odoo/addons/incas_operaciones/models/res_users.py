import json

from odoo import api, models, modules


class ResUsers(models.Model):
    _inherit = "res.users"

    _REVISOR_TAREAS_EMAIL = "incasparadise@gmail.com"

    @api.model
    def _get_activity_groups(self):
        activity_groups = super()._get_activity_groups()
        usuario = self.env.user
        if usuario.login != self._REVISOR_TAREAS_EMAIL and usuario.email != self._REVISOR_TAREAS_EMAIL:
            return activity_groups

        activity_groups = [
            group
            for group in activity_groups
            if group.get("model") not in {"project.task", "mail.activity"}
        ]

        tareas_por_revisar = self.env["mail.activity"].with_context(active_test=False).search(
            [
                "&",
                "&",
                ("estado_ejecucion", "=", "finalizada"),
                "|",
                ("revision_tarea", "=", False),
                ("revision_tarea", "=", "por_revisar"),
                ("es_revision_tarea", "=", False),
            ],
            order="fecha_hora_fin desc, id desc",
        )
        if not tareas_por_revisar:
            return activity_groups

        activity_groups.insert(
            0,
            {
                "id": self.env["ir.model"]._get("mail.activity").id,
                "name": "Tareas por revisar",
                "model": "mail.activity",
                "type": "activity",
                "icon": modules.module.get_module_icon("mail"),
                "domain": json.dumps([["id", "in", tareas_por_revisar.ids]]),
                "activity_ids": tareas_por_revisar.ids,
                "total_count": len(tareas_por_revisar),
                "today_count": len(tareas_por_revisar),
                "overdue_count": 0,
                "planned_count": 0,
                "view_type": "list",
            },
        )
        return activity_groups
