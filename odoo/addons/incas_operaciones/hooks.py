from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})
    reservas = env["incas.reserva"].sudo().search([])
    reservas._sincronizar_evento_operativo()
    reservas._sincronizar_lineas_operacion()
