import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasServicioCatalogo(models.Model):
    _name = "incas.servicio.catalogo"
    _description = "Catálogo de servicios"
    _order = "tipo_servicio, name"

    name = fields.Char(string="Nombre", required=True)
    tipo_servicio = fields.Selection(
        [
            ("tour", "Tour"),
            ("transporte", "Transporte"),
        ],
        string="Tour o transporte",
        required=True,
        index=True,
    )
    tipo_tour = fields.Selection(
        [
            ("tour", "Tour"),
            ("small_trip", "Small Trip"),
            ("package", "Package"),
        ],
        string="Tipo de tour",
    )
    estilo_transporte_id = fields.Many2one(
        "incas.estilo.transporte", string="Estilo de transporte"
    )
    precio_adulto = fields.Float(string="Precio adulto")
    precio_nino = fields.Float(string="Precio niño")
    descuento = fields.Float(string="Descuento")
    strapi_id = fields.Integer(string="ID Strapi", index=True)
    strapi_document_id = fields.Char(string="Document ID Strapi")
    slug = fields.Char(string="Slug")
    active = fields.Boolean(default=True)

    @api.model
    def _get_strapi_base_url(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("incas_reservas.strapi_url")
            or os.getenv("ODOO_STRAPI_CONECTION_URL")
            or "https://api.incasparadise.com"
        )

    @api.model
    def _fetch_strapi_records(self, endpoint, params):
        base_url = self._get_strapi_base_url().rstrip("/")
        page = 1
        page_size = 100
        records = []
        while True:
            request_params = dict(params)
            request_params["pagination[page]"] = page
            request_params["pagination[pageSize]"] = page_size
            request_params["publicationState"] = "live"
            query = urlencode(request_params)
            with urlopen(f"{base_url}/api/{endpoint}?{query}", timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            data = payload.get("data", [])
            records.extend(data)
            pagination = payload.get("meta", {}).get("pagination", {})
            if page >= pagination.get("pageCount", page):
                break
            page += 1
        return records

    @api.model
    def _strapi_texto_json(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)

    @api.model
    def _upsert_servicio_base(self, dominio, values):
        service = self.with_context(active_test=False).search(dominio, limit=1)
        if service:
            service.write(values)
        else:
            service = self.create(values)
        return service

    @api.model
    def _json_lista(self, valor):
        if not valor:
            return []
        try:
            data = json.loads(valor)
            return data if isinstance(data, list) else []
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    @api.constrains("tipo_servicio", "strapi_id")
    def _check_strapi_id_unico(self):
        for record in self:
            if not record.strapi_id:
                continue
            duplicado = self.search(
                [
                    ("id", "!=", record.id),
                    ("tipo_servicio", "=", record.tipo_servicio),
                    ("strapi_id", "=", record.strapi_id),
                ],
                limit=1,
            )
            if duplicado:
                raise ValidationError("El ID Strapi ya existe para este tipo de servicio.")

    def _horarios_desde_schedule_items(self, schedule_items_data):
        if not schedule_items_data:
            return []
        if isinstance(schedule_items_data, str):
            items = self._json_lista(schedule_items_data)
        else:
            items = schedule_items_data if isinstance(schedule_items_data, list) else []
        horarios = []
        for item in items:
            if not isinstance(item, dict):
                continue
            titulo = str(item.get("title") or "").strip()
            hora_entrada = str(
                item.get("horaEntrada") or item.get("hora_entrada") or ""
            ).strip()
            hora_salida = str(
                item.get("horaSalida") or item.get("hora_salida") or ""
            ).strip()
            rango = " - ".join(valor for valor in [hora_entrada, hora_salida] if valor)
            if titulo and rango:
                valor = f"{titulo}: {rango}"
            elif titulo:
                valor = titulo
            else:
                valor = rango
            if valor and valor not in horarios:
                horarios.append(valor)
        return horarios

    def _sync_horarios_servicio(self, servicio, schedule_items_data):
        horario_model = self.env["incas.horario.opcion"]
        existentes = horario_model.search([("servicio_id", "=", servicio.id)])
        nombres = self._horarios_desde_schedule_items(schedule_items_data)
        vistos = []
        for indice, nombre in enumerate(nombres, start=1):
            valores = {
                "name": nombre,
                "sequence": indice * 10,
                "servicio_id": servicio.id,
            }
            horario = existentes.filtered(lambda item: item.name == nombre)[:1]
            if horario:
                horario.write(valores)
                vistos.append(horario.id)
            else:
                nuevo = horario_model.create(valores)
                vistos.append(nuevo.id)
        (existentes - horario_model.browse(vistos)).unlink()

    def _obtener_detalle_transporte(self):
        self.ensure_one()
        if self.tipo_servicio != "transporte":
            return self.env["incas.catalogo.transporte"]
        return self.env["incas.catalogo.transporte"].search([("servicio_id", "=", self.id)], limit=1)

    def obtener_vehiculos_transporte(self):
        self.ensure_one()
        if self.tipo_servicio != "transporte":
            return self.env["incas.catalogo.vehiculo"]
        detalle = self._obtener_detalle_transporte()
        if detalle.tarifa_ids:
            return detalle.tarifa_ids.mapped("vehiculo_id")
        return self.env["incas.catalogo.vehiculo"]

    def obtener_vehiculo_transporte(self, nombre=None, vehiculo_id=None, vehiculo_actual=None, usar_default=True):
        self.ensure_one()
        vehiculos = self.obtener_vehiculos_transporte()
        if vehiculo_id:
            vehiculo = vehiculos.filtered(lambda item: item.id == vehiculo_id)
            if vehiculo:
                return vehiculo[:1]
        if nombre:
            vehiculo = vehiculos.filtered(lambda item: item.name == nombre)
            if vehiculo:
                return vehiculo[:1]
        if vehiculo_actual and vehiculo_actual.id in vehiculos.ids:
            return vehiculo_actual[:1]
        if usar_default:
            return vehiculos[:1]
        return self.env["incas.catalogo.vehiculo"]

    def obtener_tarifa_vehiculo_transporte(self, vehiculo):
        self.ensure_one()
        detalle = self._obtener_detalle_transporte()
        if detalle.tarifa_ids and vehiculo:
            tarifa = detalle.tarifa_ids.filtered(lambda item: item.vehiculo_id == vehiculo)[:1]
            if tarifa:
                return {
                    "precio_adulto": tarifa.precio_adulto_usd or 0,
                    "precio_nino": tarifa.precio_nino_usd or 0,
                    "descuento": tarifa.descuento or 0,
                }
        if detalle.tarifa_ids:
            tarifa = detalle.tarifa_ids.sorted(lambda item: (item.sequence, item.id))[:1]
            if tarifa:
                return {
                    "precio_adulto": tarifa.precio_adulto_usd or 0,
                    "precio_nino": tarifa.precio_nino_usd or 0,
                    "descuento": tarifa.descuento or 0,
                }
        return {
            "precio_adulto": self.precio_adulto or 0,
            "precio_nino": self.precio_nino or 0,
            "descuento": self.descuento or 0,
        }

    @api.model
    def _get_currency_rates(self):
        self._asegurar_tasas_monitoreadas()
        company = self.env.company
        fecha = fields.Date.context_today(self)
        currency_model = self.env["res.currency"].with_context(active_test=False)
        usd_currency = currency_model.search([("name", "=", "USD")], limit=1)
        pen_currency = currency_model.search([("name", "=", "PEN")], limit=1)
        eur_currency = currency_model.search([("name", "=", "EUR")], limit=1)

        if not usd_currency:
            raise ValueError("No se encontró la moneda USD en Odoo")

        # Las tarifas del frontend usan USD como base.
        return {
            "PEN": float(usd_currency._convert(1.0, pen_currency, company, fecha)) if pen_currency else 3.75,
            "EUR": float(usd_currency._convert(1.0, eur_currency, company, fecha)) if eur_currency else 0.92,
        }

    @api.model
    def _obtener_tasas_usd_desde_api(self):
        token = os.getenv("APIS_NET_PE_TOKEN", "")
        fecha = fields.Date.context_today(self)
        fecha_texto = fields.Date.to_string(fecha)
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        usd_pen = 3.75
        try:
            request = Request(
                "https://apis.net.pe/v1/tipo-cambio/sbs/average",
                headers=headers,
                method="GET",
            )
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            usd_pen = float(payload.get("venta") or 3.75)
        except Exception:
            usd_pen = 3.75

        usd_eur = 0.92
        try:
            request = Request(
                f"https://apis.net.pe/v1/tipo-cambio/sbs/accounting?date={fecha_texto}&currency=EUR",
                headers=headers,
                method="GET",
            )
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            eur_pen = float(payload.get("venta") or 0)
            if eur_pen > 0:
                usd_eur = usd_pen / eur_pen
        except Exception:
            usd_eur = 0.92

        return {
            "USD": 1.0,
            "PEN": usd_pen,
            "EUR": usd_eur,
        }

    @api.model
    def _asegurar_tasas_monitoreadas(self):
        rate_model = self.env["res.currency.rate"].sudo()
        currency_model = self.env["res.currency"].with_context(active_test=False)
        fecha = fields.Date.context_today(self)
        monedas = currency_model.search([("name", "in", ["USD", "PEN", "EUR"])])
        if len(monedas) < 3:
            return
        for company in self.env["res.company"].sudo().search([]):
            dominio = [
                ("currency_id", "in", monedas.ids),
                ("name", "=", fecha),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ]
            if rate_model.search_count(dominio) >= len(monedas):
                continue
            self._cron_actualizar_tipos_cambio_odoo()
            return

    @api.model
    def _cron_actualizar_tipos_cambio_odoo(self):
        tasas_usd = self._obtener_tasas_usd_desde_api()
        currency_model = self.env["res.currency"].with_context(active_test=False).sudo()
        rate_model = self.env["res.currency.rate"].sudo()
        fecha = fields.Date.context_today(self)
        monedas = {
            codigo: currency_model.search([("name", "=", codigo)], limit=1)
            for codigo in ("USD", "PEN", "EUR")
        }

        for company in self.env["res.company"].sudo().search([]):
            moneda_empresa = company.currency_id
            valor_empresa_usd = tasas_usd.get(moneda_empresa.name)
            if not moneda_empresa or not valor_empresa_usd:
                continue
            for codigo, currency in monedas.items():
                if not currency:
                    continue
                valor_moneda_usd = tasas_usd.get(codigo)
                if not valor_moneda_usd:
                    continue
                rate = valor_moneda_usd / valor_empresa_usd
                valores = {
                    "name": fecha,
                    "currency_id": currency.id,
                    "company_id": company.id,
                    "rate": rate,
                }
                if "inverse_company_rate" in rate_model._fields and rate:
                    valores["inverse_company_rate"] = 1.0 / rate
                registro = rate_model.search(
                    [
                        ("currency_id", "=", currency.id),
                        ("company_id", "=", company.id),
                        ("name", "=", fecha),
                    ],
                    limit=1,
                )
                if registro:
                    registro.write(valores)
                else:
                    rate_model.create(valores)

    @api.model
    def _sync_tours(self):
        tour_model = self.env["incas.catalogo.tour"]
        records = self._fetch_strapi_records(
            "tour-detalles",
            {
                "populate[0]": "destinos",
                "populate[1]": "estilos",
                "populate[2]": "ogImage",
                "populate[3]": "twitterImage",
                "populate[4]": "heroSlideImages",
                "populate[5]": "highlightsItems",
                "populate[6]": "featuredImages.image",
                "populate[7]": "itineraryItems.image",
                "populate[8]": "itineraryItems.includes",
                "populate[9]": "scheduleItems",
                "populate[10]": "includedItems",
                "populate[11]": "excludedItems",
                "populate[12]": "faqItems",
            },
        )
        seen_ids = []
        for item in records:
            strapi_id = item.get("id")
            if not strapi_id:
                continue
            seen_ids.append(strapi_id)
            values = {
                "name": item.get("title"),
                "tipo_servicio": "tour",
                "tipo_tour": item.get("tourType") or "tour",
                "estilo_transporte_id": False,
                "precio_adulto": float(item.get("adultUnitPrice") or 0),
                "precio_nino": float(item.get("childUnitPrice") or 0),
                "descuento": float(item.get("discount") or 0),
                "strapi_id": strapi_id,
                "strapi_document_id": item.get("documentId"),
                "slug": item.get("slug"),
                "active": True,
            }
            service = self._upsert_servicio_base(
                [("tipo_servicio", "=", "tour"), ("strapi_id", "=", strapi_id)],
                values,
            )
            detail_values = {
                "destination_slug": item.get("destinationSlug"),
                "destinos_data": self._strapi_texto_json(item.get("destinos")),
                "estilos_data": self._strapi_texto_json(item.get("estilos")),
                "meta_title": item.get("metaTitle"),
                "meta_description": item.get("metaDescription"),
                "seo_title": item.get("seoTitle"),
                "seo_description": item.get("seoDescription"),
                "seo_keywords": item.get("seoKeywords"),
                "seo_canonical_url": item.get("seoCanonicalUrl"),
                "seo_no_index": bool(item.get("seoNoIndex")),
                "og_title": item.get("ogTitle"),
                "og_description": item.get("ogDescription"),
                "og_image_data": self._strapi_texto_json(item.get("ogImage")),
                "twitter_title": item.get("twitterTitle"),
                "twitter_description": item.get("twitterDescription"),
                "twitter_image_data": self._strapi_texto_json(item.get("twitterImage")),
                "hero_title": item.get("heroTitle"),
                "hero_description": item.get("heroDescription"),
                "hero_slide_images_data": self._strapi_texto_json(item.get("heroSlideImages")),
                "highlights_title": item.get("highlightsTitle"),
                "highlights_lead": item.get("highlightsLead"),
                "highlights_question": item.get("highlightsQuestion"),
                "highlights_cta_label": item.get("highlightsCtaLabel"),
                "highlights_cta_url": item.get("highlightsCtaUrl"),
                "highlights_items_data": self._strapi_texto_json(item.get("highlightsItems")),
                "featured_title": item.get("featuredTitle"),
                "featured_images_data": self._strapi_texto_json(item.get("featuredImages")),
                "itinerary_title": item.get("itineraryTitle"),
                "itinerary_item_label": item.get("itineraryItemLabel"),
                "itinerary_expand_label": item.get("itineraryExpandLabel"),
                "itinerary_collapse_label": item.get("itineraryCollapseLabel"),
                "itinerary_items_data": self._strapi_texto_json(item.get("itineraryItems")),
                "schedule_title": item.get("scheduleTitle"),
                "schedule_items_data": self._strapi_texto_json(item.get("scheduleItems")),
                "included_title": item.get("includedTitle"),
                "included_items_data": self._strapi_texto_json(item.get("includedItems")),
                "excluded_title": item.get("excludedTitle"),
                "excluded_items_data": self._strapi_texto_json(item.get("excludedItems")),
                "faq_title": item.get("faqTitle"),
                "faq_items_data": self._strapi_texto_json(item.get("faqItems")),
                "show_in_styles": bool(item.get("showInStyles")),
                "duration_days": int(item.get("durationDays") or 0),
            }
            detail = tour_model.search([("servicio_id", "=", service.id)], limit=1)
            if detail:
                detail.write(detail_values)
            else:
                tour_model.create({"servicio_id": service.id, **detail_values})
            self._sync_horarios_servicio(service, item.get("scheduleItems"))
        stale_records = self.search(
            [("tipo_servicio", "=", "tour"), ("strapi_id", "not in", seen_ids)]
        )
        if stale_records:
            stale_records.write({"active": False})

    def sync_from_strapi(self, *args, **kwargs):
        self._sync_tours()
        return True
