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
        if reserva_id:
            email_from = message_dict.get("email_from")
            user_id = self._mail_find_user_for_gateway(email_from).id or self.env.uid
            route = self._routing_check_route(
                message,
                message_dict,
                ("incas.reserva", reserva_id, custom_values, user_id, None),
                raise_exception=False,
            )
            if route:
                return [route]
        return super().message_route(
            message,
            message_dict,
            model=model,
            thread_id=thread_id,
            custom_values=custom_values,
        )

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
