import json

from urllib.error import HTTPError

from odoo import http
from odoo.http import request

from ..utils import capturar_orden_paypal, crear_orden_paypal, error_http_text


def response_json(payload, status=200):
    headers = [
        ("Content-Type", "application/json"),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]
    return request.make_response(json.dumps(payload), headers=headers, status=status)


def options_response():
    return response_json({})


def body_json():
    raw = request.httprequest.data or b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


class IncasReservasApiController(http.Controller):
    @http.route("/incas/api/pagos/tipo-cambio", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def tipo_cambio(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        try:
            rates = request.env["incas.servicio.catalogo"].sudo()._get_currency_rates()
            return response_json(rates)
        except Exception as error:
            return response_json({"error": {"message": str(error)}}, 500)

    @http.route("/incas/api/pagos/iniciar", type="http", auth="public", methods=["POST", "OPTIONS"], csrf=False)
    def iniciar_pago(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        payload = body_json()
        proveedor = payload.get("proveedor")
        monto = float(payload.get("monto") or 0)
        moneda = payload.get("moneda") or "USD"
        if proveedor != "paypal":
            return response_json({"error": {"message": "Proveedor no soportado"}}, 400)
        if monto <= 0:
            return response_json({"error": {"message": "Monto inválido"}}, 400)
        try:
            return response_json(crear_orden_paypal(monto, moneda))
        except HTTPError as error:
            return response_json({"error": {"message": error_http_text(error)}}, 400)
        except Exception as error:
            return response_json({"error": {"message": str(error)}}, 500)

    @http.route("/incas/api/reservas", type="http", auth="public", methods=["POST", "OPTIONS"], csrf=False)
    def crear_reserva(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        payload = body_json()
        reserva_data = payload.get("reservaData") or payload
        pago_data = payload.get("pagoData") or {
            "proveedor": payload.get("proveedor") or "izipay",
            "metodo": payload.get("metodo") or "tarjeta",
            "moneda": reserva_data.get("moneda") or "USD",
            "monto": payload.get("monto") or reserva_data.get("monto_total") or 0,
            "estado": payload.get("estado") or "pagado",
            "ip_cliente": request.httprequest.remote_addr,
        }
        try:
            reserva = request.env["incas.reserva"].sudo().crear_reserva_web(reserva_data, pago_data)
            return response_json(
                {
                    "ticket": reserva.ticket,
                    "reserva_id": reserva.id,
                    "voucher_url": reserva.get_public_voucher_url(),
                }
            )
        except Exception as error:
            return response_json({"error": {"message": str(error)}}, 400)

    @http.route("/incas/api/pagos/confirmar", type="http", auth="public", methods=["POST", "OPTIONS"], csrf=False)
    def confirmar_pago(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        payload = body_json()
        proveedor = payload.get("proveedor")
        token = payload.get("token")
        reserva_data = payload.get("reservaData") or {}
        if proveedor != "paypal" or not token:
            return response_json({"error": {"message": "Se requieren proveedor y token válidos"}}, 400)
        try:
            resultado = capturar_orden_paypal(token)
            if resultado.get("estado") != "pagado":
                return response_json({"error": {"message": "El pago no fue completado por el proveedor"}}, 400)
            pago_data = {
                "proveedor": "paypal",
                "metodo": "paypal",
                "moneda": "USD",
                "monto": float(reserva_data.get("monto_total") or 0),
                "estado": "pagado",
                "transaccion_id": resultado.get("transaccion_id"),
                "orden_id": token,
                "ip_cliente": request.httprequest.remote_addr,
            }
            reserva = request.env["incas.reserva"].sudo().crear_reserva_web(reserva_data, pago_data)
            return response_json(
                {
                    "ticket": reserva.ticket,
                    "reserva_id": reserva.id,
                    "voucher_url": reserva.get_public_voucher_url(),
                }
            )
        except HTTPError as error:
            return response_json({"error": {"message": error_http_text(error)}}, 400)
        except Exception as error:
            return response_json({"error": {"message": str(error)}}, 500)
