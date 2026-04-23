from odoo import http
from odoo.http import request

from ..utils import (
    generar_pdf_desde_html,
    render_cotizacion_html,
    render_reserva_html,
    texto,
)


class IncasReservasPdfController(http.Controller):
    @http.route("/incas/reserva/<int:reserva_id>/pdf", type="http", auth="user")
    def reserva_pdf(self, reserva_id, **kwargs):
        reserva = request.env["incas.reserva"].browse(reserva_id)
        reserva.check_access("read")
        pdf = generar_pdf_desde_html(render_reserva_html(reserva))
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
        pdf = generar_pdf_desde_html(render_reserva_html(reserva))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="comprobante-{texto(reserva.ticket)}.pdf"'),
            ],
        )

    @http.route("/incas/cotizacion/<int:cotizacion_id>/pdf", type="http", auth="user")
    def cotizacion_pdf(self, cotizacion_id, **kwargs):
        cotizacion = request.env["incas.cotizacion"].browse(cotizacion_id)
        cotizacion.check_access("read")
        pdf = generar_pdf_desde_html(render_cotizacion_html(cotizacion))
        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf))),
                ("Content-Disposition", f'attachment; filename="cotizacion-{texto(cotizacion.name)}.pdf"'),
            ],
        )
