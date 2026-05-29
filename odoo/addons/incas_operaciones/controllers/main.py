from odoo import http
from odoo.http import request

from odoo.addons.incas_reservas.utils import generar_pdf_desde_html, texto
from ..utils import render_pase_operativo_html


class IncasOperacionesPdfController(http.Controller):
    @http.route("/incas/operaciones/reserva/<int:reserva_id>/pase-pdf", type="http", auth="user")
    def reserva_pase_operativo_pdf(self, reserva_id, **kwargs):
        reserva = request.env["incas.reserva"].browse(reserva_id)
        reserva.check_access("read")
        reserva._sincronizar_lineas_operacion()
        pdf = generar_pdf_desde_html(render_pase_operativo_html(reserva))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="pase-operativo-{texto(reserva.ticket)}.pdf"'),
            ],
        )
