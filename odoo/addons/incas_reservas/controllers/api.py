import json
import logging

from urllib.error import HTTPError

from odoo import http
from odoo.http import request

from ..utils import capturar_orden_paypal, crear_orden_paypal, error_http_text


_logger = logging.getLogger(__name__)


def _lang_base(lang):
    lang = (lang or "es").split("_")[0].split("-")[0].lower()
    if lang in {"en", "pt"}:
        return lang
    return "es"


def _campo_localizado(record, base, lang):
    lang = _lang_base(lang)
    if lang == "en" and hasattr(record, f"{base}_en"):
        return getattr(record, f"{base}_en") or getattr(record, base, False)
    if lang == "pt" and hasattr(record, f"{base}_pt"):
        return getattr(record, f"{base}_pt") or getattr(record, base, False)
    return getattr(record, base, False)


def _image_payload(record, field):
    if not getattr(record, field, False):
        return None
    base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
    return {
        "url": f"{base_url}/web/image?model={record._name}&id={record.id}&field={field}",
    }


def _serialize_vehiculo(vehiculo, lang):
    features = []
    for caracteristica in vehiculo.caracteristica_ids.sorted(lambda item: (item.sequence, item.id)):
        texto = _campo_localizado(caracteristica, "titulo", lang)
        if texto:
            features.append(
                {
                    "text": texto or "",
                    "title": texto or "",
                }
            )
    return {
        "id": vehiculo.id,
        "nombre": _campo_localizado(vehiculo, "nombre", lang),
        "descripcion": _campo_localizado(vehiculo, "descripcion", lang),
        "imagen": _image_payload(vehiculo, "imagen"),
        "nro_asientos": vehiculo.numero_asientos or None,
        "features": features,
    }


def _serialize_transporte(transporte, lang, incluir_tipos=True):
    precios = []
    for tarifa in transporte.tarifa_ids.sorted(lambda item: (item.sequence, item.id)):
        precios.append(
            {
                "precioAdulto": tarifa.precio_adulto_usd or 0,
                "precioNino": tarifa.precio_nino_usd or 0,
                "descuento": tarifa.descuento or 0,
                "vehiculo": [_serialize_vehiculo(tarifa.vehiculo_id, lang)] if tarifa.vehiculo_id else [],
            }
        )
    included_items = []
    for item in transporte.incluye_ids.sorted(lambda x: (x.sequence, x.id)):
        texto = _campo_localizado(item, "texto", lang)
        if texto:
            included_items.append({"text": texto, "icon": "✓"})
    excluded_items = []
    for item in transporte.no_incluye_ids.sorted(lambda x: (x.sequence, x.id)):
        texto = _campo_localizado(item, "texto", lang)
        if texto:
            excluded_items.append({"text": texto, "icon": "✕"})
    data = {
        "id": transporte.id,
        "documentId": None,
        "slug": transporte.slug,
        "nombre": _campo_localizado(transporte, "name", lang),
        "seoTitle": _campo_localizado(transporte, "seo_title", lang),
        "seoDescription": _campo_localizado(transporte, "seo_description", lang),
        "descripcion": _campo_localizado(transporte, "descripcion", lang),
        "image": _image_payload(transporte, "image_data"),
        "wallpaper": _image_payload(transporte, "wallpaper_data"),
        "modelo_vehiculo": transporte.modelo_vehiculo,
        "duracion_viaje": transporte.duracion_viaje,
        "distancia": transporte.distancia,
        "descripcion_origen": False,
        "descripcion_llegada": False,
        "destino_origen": [{"title": _campo_localizado(transporte, "destino_origen_data", lang)}] if _campo_localizado(transporte, "destino_origen_data", lang) else [],
        "destino_llegada": [{"title": _campo_localizado(transporte, "destino_llegada_data", lang)}] if _campo_localizado(transporte, "destino_llegada_data", lang) else [],
        "includedTitle": None,
        "includedItems": included_items,
        "excludedTitle": None,
        "excludedItems": excluded_items,
        "precios": precios,
        "serviceId": transporte.servicio_id.id,
        "slugs": {codigo: transporte.slug for codigo in ["es", "en", "pt", "fr", "it"]},
    }
    if incluir_tipos:
        data["tipos_transporte"] = [
            {
                "nombre": _campo_localizado(estilo, "name", lang),
                "slug": estilo.slug,
            }
            for estilo in transporte.estilo_transporte_ids.sorted(lambda item: (item.nro_orden, item.name or ""))
        ]
    return data


def _serialize_tipo_transporte(estilo, lang, incluir_transportes=False):
    data = {
        "id": estilo.id,
        "documentId": None,
        "slug": estilo.slug,
        "nombre": _campo_localizado(estilo, "name", lang),
        "descripcion": _campo_localizado(estilo, "descripcion", lang),
        "seoTitle": _campo_localizado(estilo, "seo_title", lang),
        "seoDescription": _campo_localizado(estilo, "seo_description", lang),
        "image": _image_payload(estilo, "image_data"),
        "wallpaper": _image_payload(estilo, "wallpaper_data"),
        "nroOrden": estilo.nro_orden or 0,
        "slugs": {codigo: estilo.slug for codigo in ["es", "en", "pt", "fr", "it"]},
    }
    if incluir_transportes:
        data["transportes"] = [
            _serialize_transporte(transporte, lang, incluir_tipos=False)
            for transporte in estilo.transporte_ids.sorted(lambda item: item.name or "")
            if transporte.active
        ]
    return data


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
    @http.route("/incas/api/web/tipo-transportes", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_tipo_transportes(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        estilos = request.env["incas.estilo.transporte"].sudo().search([("active", "=", True)], order="nro_orden, name")
        return response_json({"data": [_serialize_tipo_transporte(estilo, lang) for estilo in estilos]})

    @http.route("/incas/api/web/tipo-transportes/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_tipo_transporte_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        estilo = request.env["incas.estilo.transporte"].sudo().search([("slug", "=", slug), ("active", "=", True)], limit=1)
        if not estilo:
            return response_json({"error": {"message": "Tipo de transporte no encontrado"}}, 404)
        return response_json({"data": _serialize_tipo_transporte(estilo, lang, incluir_transportes=True)})

    @http.route("/incas/api/web/transportes", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_transportes(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        transportes = request.env["incas.catalogo.transporte"].sudo().search([("active", "=", True)], order="name")
        return response_json({"data": [_serialize_transporte(transporte, lang) for transporte in transportes]})

    @http.route("/incas/api/web/transportes/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_transporte_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        transporte = request.env["incas.catalogo.transporte"].sudo().search([("slug", "=", slug), ("active", "=", True)], limit=1)
        if not transporte:
            return response_json({"error": {"message": "Transporte no encontrado"}}, 404)
        return response_json({"data": _serialize_transporte(transporte, lang)})

    @http.route("/incas/api/pagos/tipo-cambio", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def tipo_cambio(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        try:
            rates = request.env["incas.servicio.catalogo"].sudo()._get_currency_rates()
            return response_json(rates)
        except Exception as error:
            _logger.exception("Error en /incas/api/pagos/tipo-cambio")
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
            _logger.exception("Error en /incas/api/reservas")
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
            _logger.exception("Error en /incas/api/pagos/confirmar")
            return response_json({"error": {"message": str(error)}}, 500)
