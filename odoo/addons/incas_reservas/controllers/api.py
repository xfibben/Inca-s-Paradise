import base64
import json
import logging

from urllib.parse import urlencode
from urllib.error import HTTPError

from odoo import http
from odoo.http import request
from odoo.tools.mimetypes import guess_mimetype

from ..utils import capturar_orden_paypal, crear_orden_paypal, error_http_text


_logger = logging.getLogger(__name__)

_PUBLIC_IMAGE_FIELDS = {
    "incas.catalogo.destino": {"imagen", "imagen_fondo"},
    "incas.catalogo.destino.icono": {"imagen"},
    "incas.nosotros.seccion": {"imagen"},
    "incas.sostenibilidad.articulo": {"imagen_portada"},
    "incas.catalogo.transporte": {"image_data", "wallpaper_data"},
    "incas.catalogo.vehiculo": {"imagen"},
    "incas.estilo.transporte": {"image_data", "wallpaper_data"},
    "incas.estilo.viaje": {"image", "wallpaper"},
    "incas.tour": {"imagen"},
    "incas.tour.imagen.destacada": {"imagen"},
    "incas.tour.itinerario.imagen": {"imagen"},
}


def _lang_base(lang):
    lang = (lang or "es").split("_")[0].split("-")[0].lower()
    if lang in {"en", "pt", "fr", "it"}:
        return lang
    return "es"


def _domain_ip(ip_value):
    if ip_value in {"ip2", "ip3"}:
        return [("ip", "=", ip_value)]
    return []


def _campo_localizado(record, base, lang):
    lang = _lang_base(lang)
    if lang == "en" and hasattr(record, f"{base}_en"):
        return getattr(record, f"{base}_en") or getattr(record, base, False)
    if lang == "pt" and hasattr(record, f"{base}_pt"):
        return getattr(record, f"{base}_pt") or getattr(record, base, False)
    if lang == "fr" and hasattr(record, f"{base}_fr"):
        return getattr(record, f"{base}_fr") or getattr(record, base, False)
    if lang == "it" and hasattr(record, f"{base}_it"):
        return getattr(record, f"{base}_it") or getattr(record, base, False)
    return getattr(record, base, False)


def _image_payload(record, field):
    if not getattr(record, field, False):
        return None
    base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
    db_name = request.db or request.session.db or request.env.cr.dbname or ""
    query_params = {
        "model": record._name,
        "id": record.id,
        "field": field,
    }
    if db_name:
        query_params["db"] = db_name
    return {
        "url": f"{base_url}/incas/public/image?{urlencode(query_params)}",
    }


def _normalizar_alt_imagen(nombre):
    texto = (nombre or "").strip()
    if not texto:
        return False
    texto = texto.rsplit(".", 1)[0]
    return "-".join(texto.split()) or False


def _binary_content_type(record, field, binary_value):
    archivo = getattr(record, f"{field}_file_id", False)
    if archivo and archivo.mimetype:
        return archivo.mimetype
    return guess_mimetype(base64.b64decode(binary_value)) or "image/png"


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
        "ip": transporte.ip or "ip3",
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


def _slug_localizado(record, lang):
    return _campo_localizado(record, "slug", lang)


def _slugs_localizados(record):
    base = getattr(record, "slug", False) or ""
    slug_en = getattr(record, "slug_en", False) or base
    slug_pt = getattr(record, "slug_pt", False) or base
    slug_fr = getattr(record, "slug_fr", False) or base
    slug_it = getattr(record, "slug_it", False) or base
    return {
        "es": base,
        "en": slug_en or base,
        "pt": slug_pt or base,
        "fr": slug_fr or base,
        "it": slug_it or base,
    }


def _tours_relacionados_sostenibilidad(articulo, lang):
    tours = articulo.tour_ids
    return [
        _serialize_tour_card(tour, lang)
        for tour in tours.sorted(lambda rec: (_campo_localizado(rec, "nombre", lang) or "", rec.id))
        if tour.active
    ]


def _serialize_sostenibilidad_articulo(articulo, lang):
    return {
        "id": articulo.id,
        "title": _campo_localizado(articulo, "titulo", lang),
        "slug": _slug_localizado(articulo, lang),
        "slugs": _slugs_localizados(articulo),
        "contentHtml": _campo_localizado(articulo, "contenido_html", lang),
        "seoTitle": _campo_localizado(articulo, "seo_titulo", lang),
        "seoDescription": _campo_localizado(articulo, "seo_descripcion", lang),
        "image": _image_payload(articulo, "imagen_portada"),
        "publishedAt": articulo.fecha_publicacion.isoformat() if articulo.fecha_publicacion else None,
        "showInHome": bool(articulo.mostrar_en_portada),
        "showInMenu": bool(articulo.mostrar_en_portada),
        "destinations": [
            _serialize_destino_minimo(destino, lang)
            for destino in articulo.destino_ids.sorted(lambda rec: (_campo_localizado(rec, "nombre", lang) or "", rec.id))
            if destino.active
        ],
        "tags": [etiqueta.name for etiqueta in articulo.etiqueta_ids.sorted(lambda rec: (rec.name or "", rec.id)) if etiqueta.name],
        "relatedTours": _tours_relacionados_sostenibilidad(articulo, lang),
    }


def _serialize_termino_condicion(termino, lang):
    return {
        "id": termino.id,
        "slug": termino.slug,
        "slugs": {
            "es": termino.slug,
            "en": termino.slug_en or termino.slug,
            "pt": termino.slug_pt or termino.slug,
        },
        "title": _campo_localizado(termino, "titulo", lang),
        "description": _campo_localizado(termino, "descripcion", lang),
        "seoTitle": _campo_localizado(termino, "seo_titulo", lang),
        "seoDescription": _campo_localizado(termino, "seo_descripcion", lang),
        "sections": [
            {
                "title": _campo_localizado(seccion, "titulo", lang),
                "text": _campo_localizado(seccion, "texto_html", lang),
            }
            for seccion in termino.seccion_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(seccion, "titulo", lang) or _campo_localizado(seccion, "texto_html", lang)
        ],
    }


def _serialize_nosotros(nosotros, lang):
    return {
        "id": nosotros.id,
        "title": _campo_localizado(nosotros, "titulo", lang),
        "description": _campo_localizado(nosotros, "descripcion", lang),
        "metaTitle": _campo_localizado(nosotros, "meta_titulo", lang),
        "metaDescription": _campo_localizado(nosotros, "meta_descripcion", lang),
        "sections": [
            {
                "title": _campo_localizado(seccion, "titulo", lang),
                "text": _campo_localizado(seccion, "texto_html", lang),
                "image": _image_payload(seccion, "imagen"),
            }
            for seccion in nosotros.seccion_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(seccion, "titulo", lang)
            or _campo_localizado(seccion, "texto_html", lang)
            or seccion.imagen
        ],
    }


def _serialize_politica(politica, lang):
    return {
        "id": politica.id,
        "slug": _slug_localizado(politica, lang),
        "slugs": _slugs_localizados(politica),
        "titulo": _campo_localizado(politica, "titulo", lang),
        "descripcion": _campo_localizado(politica, "descripcion", lang),
        "metaTitle": _campo_localizado(politica, "meta_titulo", lang),
        "metaDescription": _campo_localizado(politica, "meta_descripcion", lang),
        "secciones": [
            {
                "titulo": _campo_localizado(seccion, "titulo", lang),
                "contenido": _campo_localizado(seccion, "contenido", lang),
            }
            for seccion in politica.seccion_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(seccion, "titulo", lang) or _campo_localizado(seccion, "contenido", lang)
        ],
    }


def _serialize_cancelacion(cancelacion, lang):
    return {
        "id": cancelacion.id,
        "slug": _slug_localizado(cancelacion, lang),
        "slugs": _slugs_localizados(cancelacion),
        "titulo": _campo_localizado(cancelacion, "titulo", lang),
        "descripcion": _campo_localizado(cancelacion, "descripcion", lang),
        "metaTitle": _campo_localizado(cancelacion, "meta_titulo", lang),
        "metaDescription": _campo_localizado(cancelacion, "meta_descripcion", lang),
        "secciones": [
            {
                "titulo": _campo_localizado(seccion, "titulo", lang),
                "contenido": _campo_localizado(seccion, "contenido", lang),
            }
            for seccion in cancelacion.seccion_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(seccion, "titulo", lang) or _campo_localizado(seccion, "contenido", lang)
        ],
    }


def _serialize_pregunta_frecuente(pregunta_frecuente, lang):
    return {
        "id": pregunta_frecuente.id,
        "slug": _slug_localizado(pregunta_frecuente, lang),
        "slugs": _slugs_localizados(pregunta_frecuente),
        "titulo": _campo_localizado(pregunta_frecuente, "titulo", lang),
        "descripcion": _campo_localizado(pregunta_frecuente, "descripcion", lang),
        "metaTitle": _campo_localizado(pregunta_frecuente, "meta_titulo", lang),
        "metaDescription": _campo_localizado(pregunta_frecuente, "meta_descripcion", lang),
        "sections": [
            {
                "pregunta": _campo_localizado(seccion, "pregunta", lang),
                "respuesta": _campo_localizado(seccion, "respuesta", lang),
            }
            for seccion in pregunta_frecuente.seccion_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(seccion, "pregunta", lang) or _campo_localizado(seccion, "respuesta", lang)
        ],
    }


def _serialize_tour_media_list(tour):
    imagenes = []
    payload_principal = _image_payload(tour, "imagen")
    if payload_principal:
        imagenes.append(payload_principal)
    for item in tour.imagen_destacada_ids.sorted(lambda rec: (rec.sequence, rec.id)):
        payload = _image_payload(item, "imagen")
        if payload and payload not in imagenes:
            imagenes.append(payload)
    return imagenes


def _serialize_tour_featured_media_list(tour):
    imagenes = []
    for item in tour.imagen_destacada_ids.sorted(lambda rec: (rec.sequence, rec.id)):
        payload = _image_payload(item, "imagen")
        if payload:
            imagenes.append(payload)
    return imagenes


def _serialize_tour_card(tour, lang):
    hero_images = _serialize_tour_media_list(tour)
    return {
        "id": tour.id,
        "documentId": None,
        "ip": tour.ip or "ip3",
        "serviceId": tour.servicio_id.id if tour.servicio_id else None,
        "slug": _slug_localizado(tour, lang),
        "slugs": _slugs_localizados(tour),
        "title": _campo_localizado(tour, "nombre", lang),
        "nombre": _campo_localizado(tour, "nombre", lang),
        "metaTitle": _campo_localizado(tour, "meta_titulo", lang),
        "metaDescription": _campo_localizado(tour, "meta_descripcion", lang),
        "adultUnitPrice": tour.precio_adulto or 0,
        "childUnitPrice": tour.precio_nino or 0,
        "discount": tour.descuento or 0,
        "tourType": tour.tipo_tour or "tour",
        "durationDays": tour.dias or max(len(tour.itinerario_item_ids), 1),
        "showInStyles": bool(tour.estilo_ids),
        "heroSlideImages": hero_images,
    }


def _serialize_destino_minimo(destino, lang):
    return {
        "id": destino.id,
        "title": _campo_localizado(destino, "nombre", lang),
        "name": _campo_localizado(destino, "nombre", lang),
        "slug": _slug_localizado(destino, lang),
        "slugs": _slugs_localizados(destino),
        "galleryThumbnail": _image_payload(destino, "imagen"),
        "heroSlideImages": [payload for payload in [_image_payload(destino, "imagen_fondo"), _image_payload(destino, "imagen")] if payload],
    }


def _serialize_estilo_viaje_minimo(estilo, lang):
    return {
        "id": estilo.id,
        "name": _campo_localizado(estilo, "name", lang),
        "slug": _slug_localizado(estilo, lang),
        "slugs": _slugs_localizados(estilo),
        "image": _image_payload(estilo, "image"),
    }


def _serialize_subcategoria_destino(subcategoria, lang):
    return {
        "id": subcategoria.id,
        "nombre": _campo_localizado(subcategoria, "nombre", lang),
        "tours": [
            _serialize_tour_card(tour, lang)
            for tour in subcategoria.tour_ids.sorted(lambda rec: (_campo_localizado(rec, "nombre", lang) or "", rec.id))
            if tour.active
        ],
    }


def _serialize_destino(destino, lang, incluir_tours=False):
    tours = request.env["incas.tour"].sudo().search(
        [("destino_ids", "in", destino.id), ("active", "=", True)],
        order="nombre, id",
    )
    icon_items = []
    for item in destino.icono_item_ids.sorted(lambda rec: (rec.sequence, rec.id)):
        label = _campo_localizado(item, "titulo", lang)
        icon_items.append(
            {
                "iconKey": "",
                "label": label,
                "description": "",
                "iconAlt": label or "",
                "icon": _image_payload(item, "imagen"),
            }
        )
    data = {
        "id": destino.id,
        "documentId": None,
        "title": _campo_localizado(destino, "nombre", lang),
        "name": _campo_localizado(destino, "nombre", lang),
        "slug": _slug_localizado(destino, lang),
        "slugs": _slugs_localizados(destino),
        "description": _campo_localizado(destino, "descripcion", lang),
        "seoTitle": _campo_localizado(destino, "seo_titulo", lang),
        "seoDescription": _campo_localizado(destino, "seo_descripcion", lang),
        "ogTitle": _campo_localizado(destino, "seo_titulo", lang),
        "ogDescription": _campo_localizado(destino, "seo_descripcion", lang),
        "twitterTitle": _campo_localizado(destino, "seo_titulo", lang),
        "twitterDescription": _campo_localizado(destino, "seo_descripcion", lang),
        "introTitle": _campo_localizado(destino, "titulo_intro", lang),
        "introContent": _campo_localizado(destino, "contenido_intro", lang),
        "primaryRibbon": _campo_localizado(destino, "cinta_principal", lang),
        "secondaryRibbon": False,
        "blogTitle": False,
        "blogButton": False,
        "catalogViewMoreLabel": False,
        "catalogViewLessLabel": False,
        "catalogInitialVisibleCount": destino.cantidad_inicial_catalogo or 6,
        "galleryThumbnail": _image_payload(destino, "imagen"),
        "heroSlideImages": [payload for payload in [_image_payload(destino, "imagen_fondo"), _image_payload(destino, "imagen")] if payload],
        "iconCatalog": icon_items,
        "iconItems": icon_items,
        "subcategorias_tour": [_serialize_subcategoria_destino(item, lang) for item in destino.subcategoria_destino_ids.sorted(lambda rec: (rec.sequence, rec.id)) if item.active],
    }
    if incluir_tours:
        data["tours"] = [_serialize_tour_card(tour, lang) for tour in tours]
    return data


def _serialize_estilo_viaje(estilo, lang, incluir_tours=False):
    tours = request.env["incas.tour"].sudo().search([("estilo_ids", "in", estilo.id), ("active", "=", True)], order="nombre, id")
    data = {
        "id": estilo.id,
        "documentId": None,
        "name": _campo_localizado(estilo, "name", lang),
        "slug": _slug_localizado(estilo, lang),
        "slugs": _slugs_localizados(estilo),
        "description": _campo_localizado(estilo, "description", lang),
        "middle_tittle": _campo_localizado(estilo, "middle_title", lang),
        "middle_description": _campo_localizado(estilo, "middle_description", lang),
        "seoTitle": _campo_localizado(estilo, "seo_title", lang),
        "seoDescription": _campo_localizado(estilo, "seo_description", lang),
        "displayOrder": estilo.display_order or 0,
        "image": _image_payload(estilo, "image"),
        "wallpaper": _image_payload(estilo, "wallpaper"),
      }
    if incluir_tours:
        data["tours"] = [_serialize_tour_card(tour, lang) for tour in tours]
    return data


def _serialize_web_tour(tour, lang, incluir_relaciones=True, incluir_relacionados=True):
    hero_images = _serialize_tour_media_list(tour)
    featured_media = _serialize_tour_featured_media_list(tour)
    featured_images = [
        {
            "image": payload,
            "alt": f"{_campo_localizado(tour, 'nombre', lang) or 'Tour'} {index + 1}",
        }
        for index, payload in enumerate(featured_media)
    ]
    itinerary_items = []
    for item in tour.itinerario_item_ids.sorted(lambda rec: (rec.sequence, rec.id)):
        imagenes = [
            {
                **payload,
                "alt": _normalizar_alt_imagen(imagen.nombre or imagen.imagen_file_id.name),
            }
            for imagen in item.imagen_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if (payload := _image_payload(imagen, "imagen"))
        ]
        imagen = imagenes[0] if imagenes else False
        itinerary_items.append(
            {
                "title": _campo_localizado(item, "titulo", lang),
                "highlight": "",
                "description": _campo_localizado(item, "descripcion", lang),
                "optional": "",
                "imageAlt": (imagen or {}).get("alt") or _campo_localizado(item, "titulo", lang),
                "image": imagen,
                "images": imagenes,
                "includes": [],
            }
        )
    schedule_items = [
        {
            "title": "",
            "horaEntrada": item.horario_inicial or "",
            "horaSalida": item.horario_final or "",
        }
        for item in tour.horario_ids.sorted(lambda rec: (rec.sequence, rec.id))
        if item.horario_inicial or item.horario_final
    ]
    data = {
        "id": tour.id,
        "documentId": None,
        "ip": tour.ip or "ip3",
        "serviceId": tour.servicio_id.id if tour.servicio_id else None,
        "slug": _slug_localizado(tour, lang),
        "slugs": _slugs_localizados(tour),
        "title": _campo_localizado(tour, "nombre", lang),
        "nombre": _campo_localizado(tour, "nombre", lang),
        "metaTitle": _campo_localizado(tour, "meta_titulo", lang),
        "metaDescription": _campo_localizado(tour, "meta_descripcion", lang),
        "seoTitle": _campo_localizado(tour, "meta_titulo", lang),
        "seoDescription": _campo_localizado(tour, "meta_descripcion", lang),
        "seoKeywords": False,
        "seoCanonicalUrl": False,
        "seoNoIndex": False,
        "ogTitle": _campo_localizado(tour, "meta_titulo", lang),
        "ogDescription": _campo_localizado(tour, "meta_descripcion", lang),
        "twitterTitle": _campo_localizado(tour, "meta_titulo", lang),
        "twitterDescription": _campo_localizado(tour, "meta_descripcion", lang),
        "heroSlideImages": hero_images,
        "highlightsTitle": _campo_localizado(tour, "destacados_titulo", lang),
        "highlightsLead": _campo_localizado(tour, "destacados_lead", lang),
        "highlightsQuestion": False,
        "highlightsCtaLabel": False,
        "highlightsCtaUrl": False,
        "highlightsItems": [
            {
                "title": _campo_localizado(item, "titulo", lang),
                "description": _campo_localizado(item, "contenido", lang),
            }
            for item in tour.destacado_item_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(item, "titulo", lang) or _campo_localizado(item, "contenido", lang)
        ],
        "featuredTitle": False,
        "featuredImages": featured_images,
        "itineraryTitle": False,
        "itineraryItemLabel": False,
        "itineraryExpandLabel": False,
        "itineraryCollapseLabel": False,
        "itineraryItems": itinerary_items,
        "scheduleTitle": False,
        "scheduleItems": schedule_items,
        "includedTitle": False,
        "includedItems": [
            {"text": _campo_localizado(item, "titulo", lang), "icon": "✓"}
            for item in tour.incluye_item_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(item, "titulo", lang)
        ],
        "excludedTitle": False,
        "excludedItems": [
            {"text": _campo_localizado(item, "titulo", lang), "icon": "✕"}
            for item in tour.no_incluye_item_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if _campo_localizado(item, "titulo", lang)
        ],
        "faqTitle": False,
        "faqItems": [],
        "adultUnitPrice": tour.precio_adulto or 0,
        "childUnitPrice": tour.precio_nino or 0,
        "discount": tour.descuento or 0,
        "tourType": tour.tipo_tour or "tour",
        "durationDays": tour.dias or max(len(tour.itinerario_item_ids), 1),
        "showInStyles": bool(tour.estilo_ids),
    }
    if incluir_relaciones:
        data["destinos"] = [_serialize_destino_minimo(destino, lang) for destino in tour.destino_ids.sorted(lambda rec: (_campo_localizado(rec, "nombre", lang) or "", rec.id))]
        data["estilos"] = [_serialize_estilo_viaje_minimo(estilo, lang) for estilo in tour.estilo_ids.sorted(lambda rec: (rec.display_order, _campo_localizado(rec, "name", lang) or "", rec.id))]
    if incluir_relacionados:
        related_domain = [("active", "=", True), ("id", "!=", tour.id)]
        destino_ids = tour.destino_ids.ids
        estilo_ids = tour.estilo_ids.ids
        if destino_ids and estilo_ids:
            related_domain += ["|", ("destino_ids", "in", destino_ids), ("estilo_ids", "in", estilo_ids)]
        elif destino_ids:
            related_domain += [("destino_ids", "in", destino_ids)]
        elif estilo_ids:
            related_domain += [("estilo_ids", "in", estilo_ids)]
        else:
            related_domain += [("tipo_tour", "=", tour.tipo_tour or "tour")]
        related_tours = request.env["incas.tour"].sudo().search(related_domain, order="nombre, id", limit=12)
        data["relatedTours"] = [_serialize_tour_card(item, lang) for item in related_tours]
    return data


def _buscar_por_slug_localizado(model_name, slug):
    model = request.env[model_name].sudo()
    campos_slug = [campo for campo in ("slug", "slug_en", "slug_pt", "slug_fr", "slug_it") if campo in model._fields]
    domain = [("active", "=", True)]
    if not campos_slug:
        return model.browse()
    if len(campos_slug) == 1:
        domain.append((campos_slug[0], "=", slug))
    else:
        domain.extend(["|"] * (len(campos_slug) - 1))
        domain.extend((campo, "=", slug) for campo in campos_slug)
    return model.search(domain, limit=1)


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
    @http.route("/incas/public/image", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def public_image(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()

        model = (request.params.get("model") or "").strip()
        field = (request.params.get("field") or "").strip()
        record_id = request.params.get("id")

        if model not in _PUBLIC_IMAGE_FIELDS or field not in _PUBLIC_IMAGE_FIELDS[model]:
            return request.not_found()

        try:
            record_id = int(record_id)
        except (TypeError, ValueError):
            return request.not_found()

        record = request.env[model].sudo().browse(record_id)
        if not record.exists():
            return request.not_found()

        binary_value = getattr(record, field, False)
        if not binary_value:
            return request.not_found()

        headers = [
            ("Content-Type", _binary_content_type(record, field, binary_value)),
            ("Cache-Control", "public, max-age=86400"),
        ]
        return request.make_response(base64.b64decode(binary_value), headers=headers)

    @http.route("/incas/api/web/estilos-viaje", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_estilos_viaje(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        estilos = request.env["incas.estilo.viaje"].sudo().search([("active", "=", True)], order="display_order, name")
        return response_json({"data": [_serialize_estilo_viaje(estilo, lang) for estilo in estilos]})

    @http.route("/incas/api/web/estilos-viaje/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_estilo_viaje_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        estilo = _buscar_por_slug_localizado("incas.estilo.viaje", slug)
        if not estilo:
            return response_json({"error": {"message": "Estilo de viaje no encontrado"}}, 404)
        return response_json({"data": _serialize_estilo_viaje(estilo, lang, incluir_tours=True)})

    @http.route("/incas/api/web/destinos", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_destinos(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        destinos = request.env["incas.catalogo.destino"].sudo().search([("active", "=", True)], order="orden_visual, nombre")
        return response_json({"data": [_serialize_destino(destino, lang, incluir_tours=True) for destino in destinos]})

    @http.route("/incas/api/web/destinos/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_destino_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        destino = _buscar_por_slug_localizado("incas.catalogo.destino", slug)
        if not destino:
            return response_json({"error": {"message": "Destino no encontrado"}}, 404)
        return response_json({"data": _serialize_destino(destino, lang, incluir_tours=True)})

    @http.route("/incas/api/web/sostenibilidad", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_sostenibilidad(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        articulos = request.env["incas.sostenibilidad.articulo"].sudo().search(
            [("active", "=", True)],
            order="fecha_publicacion desc, sequence, id desc",
        )
        return response_json({"data": [_serialize_sostenibilidad_articulo(articulo, lang) for articulo in articulos]})

    @http.route("/incas/api/web/sostenibilidad/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_sostenibilidad_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        articulo = _buscar_por_slug_localizado("incas.sostenibilidad.articulo", slug)
        if not articulo:
            return response_json({"error": {"message": "Articulo de sostenibilidad no encontrado"}}, 404)
        return response_json({"data": _serialize_sostenibilidad_articulo(articulo, lang)})

    @http.route("/incas/api/web/terminos", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_terminos(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        termino = request.env["incas.termino.condicion"].sudo().search([("active", "=", True)], order="id asc", limit=1)
        if not termino:
            return response_json({"data": None})
        return response_json({"data": _serialize_termino_condicion(termino, lang)})

    @http.route("/incas/api/web/nosotros", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_nosotros(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        nosotros = request.env["incas.nosotros"].sudo().search([("active", "=", True)], order="id asc", limit=1)
        if not nosotros:
            return response_json({"data": None})
        return response_json({"data": _serialize_nosotros(nosotros, lang)})

    @http.route("/incas/api/web/politicas", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_politicas(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        politica = request.env["incas.politica"].sudo().search([("active", "=", True)], order="id asc", limit=1)
        if not politica:
            return response_json({"data": None})
        return response_json({"data": _serialize_politica(politica, lang)})

    @http.route("/incas/api/web/cancelaciones", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_cancelaciones(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        cancelacion = request.env["incas.cancelacion"].sudo().search([("active", "=", True)], order="id asc", limit=1)
        if not cancelacion:
            return response_json({"data": None})
        return response_json({"data": _serialize_cancelacion(cancelacion, lang)})

    @http.route("/incas/api/web/preguntas-frecuentes", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_preguntas_frecuentes(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        pregunta_frecuente = request.env["incas.pregunta.frecuente"].sudo().search([("active", "=", True)], order="id asc", limit=1)
        if not pregunta_frecuente:
            return response_json({"data": None})
        return response_json({"data": _serialize_pregunta_frecuente(pregunta_frecuente, lang)})

    @http.route("/incas/api/web/tours", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_tours(self, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        ip_value = request.params.get("ip")
        domain = [("active", "=", True)] + _domain_ip(ip_value)
        tours = request.env["incas.tour"].sudo().search(domain, order="nombre, id")
        return response_json({"data": [_serialize_tour_card(tour, lang) for tour in tours]})

    @http.route("/incas/api/web/tours/<string:slug>", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False)
    def web_tour_detalle(self, slug, **kwargs):
        if request.httprequest.method == "OPTIONS":
            return options_response()
        lang = request.params.get("lang") or "es"
        tour = _buscar_por_slug_localizado("incas.tour", slug)
        if not tour:
            return response_json({"error": {"message": "Tour no encontrado"}}, 404)
        return response_json({"data": _serialize_web_tour(tour, lang)})

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
        ip_value = request.params.get("ip")
        domain = [("active", "=", True)] + _domain_ip(ip_value)
        transportes = request.env["incas.catalogo.transporte"].sudo().search(domain, order="name")
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
