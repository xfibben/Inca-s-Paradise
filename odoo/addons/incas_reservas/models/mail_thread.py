import re

from odoo import api, models
from odoo.tools.mail import email_split


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):
        recipients = message_dict.get("recipients") or message_dict.get("to") or ""
        emails = [email.lower().strip() for email in email_split(recipients)]
        reserva_id = self._extraer_reserva_id_desde_alias(emails)
        if not reserva_id:
            reserva_id = self._extraer_reserva_id_desde_asunto(message_dict.get("subject") or "")
        if reserva_id:
            email_from = message_dict.get("email_from")
            user_id = self._mail_find_user_for_gateway(email_from).id or self.env.uid
            return [("incas.reserva", reserva_id, custom_values, user_id, None)]
        try:
            return super().message_route(
                message,
                message_dict,
                model=model,
                thread_id=thread_id,
                custom_values=custom_values,
            )
        except ValueError:
            if self._correo_monitoreado_en_destinatarios(emails):
                return []
            raise

    @api.model
    def _extraer_reserva_id_desde_alias(self, emails):
        for email in emails:
            match = re.match(r"^[^@+]+\+reserva-(\d+)@", email)
            if not match:
                continue
            reserva_id = int(match.group(1))
            if self.env["incas.reserva"].sudo().browse(reserva_id).exists():
                return reserva_id
        return False

    @api.model
    def _extraer_reserva_id_desde_asunto(self, subject):
        match = re.search(r"(TICKET-\d{8}-\d+)", subject or "", flags=re.IGNORECASE)
        if not match:
            return False
        ticket = match.group(1).upper()
        reserva = self.env["incas.reserva"].sudo().search([("ticket", "=", ticket)], limit=1)
        return reserva.id or False

    @api.model
    def _correo_monitoreado_en_destinatarios(self, emails):
        default_from = (
            self.env["ir.config_parameter"].sudo().get_param("mail.default.from")
            or self.env.user.email
            or self.env.company.email
            or ""
        ).strip().lower()
        if not default_from:
            return False
        if any(email == default_from for email in emails):
            return True
        local = default_from.split("@", 1)[0]
        return any(email.startswith(f"{local}+") for email in emails)
