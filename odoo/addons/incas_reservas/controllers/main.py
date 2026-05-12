from odoo import http
from odoo.http import request

from ..utils import (
    generar_pdf_desde_html,
    render_reserva_paquete_html,
    render_reserva_html,
    texto,
)


class IncasReservasPdfController(http.Controller):
    @http.route("/incas/reserva/<int:reserva_id>/pdf", type="http", auth="user")
    def reserva_pdf(self, reserva_id, **kwargs):
        reserva = request.env["incas.reserva"].browse(reserva_id)
        reserva.check_access("read")
        pdf = generar_pdf_desde_html(render_reserva_html(reserva, kwargs.get("idioma")))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="comprobante-{texto(reserva.ticket)}.pdf"'),
            ],
        )

    @http.route("/incas/public/reserva/<int:reserva_id>/pdf/<string:access_token>", type="http", auth="public", csrf=False)
    def reserva_pdf_publico(self, reserva_id, access_token, **kwargs):
        reserva = request.env["incas.reserva"].sudo().browse(reserva_id)
        if not reserva.exists() or reserva.access_token != access_token:
            return request.not_found()
        pdf = generar_pdf_desde_html(render_reserva_html(reserva, kwargs.get("idioma") or reserva.idioma))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="comprobante-{texto(reserva.ticket)}.pdf"'),
            ],
        )

    @http.route("/incas/reserva/<int:reserva_id>/detalle-paquete-pdf", type="http", auth="user")
    def reserva_paquete_pdf(self, reserva_id, **kwargs):
        reserva = request.env["incas.reserva"].browse(reserva_id)
        reserva.check_access("read")
        pdf = generar_pdf_desde_html(render_reserva_paquete_html(reserva))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="detalle-paquete-{texto(reserva.name)}.pdf"'),
            ],
        )
