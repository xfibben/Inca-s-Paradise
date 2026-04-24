import json
import os
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from odoo import api, fields, models


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
    strapi_id = fields.Integer(string="ID Strapi", required=True, index=True)
    strapi_document_id = fields.Char(string="Document ID Strapi")
    slug = fields.Char(string="Slug")
    active = fields.Boolean(default=True)

    _incas_servicio_catalogo_strapi_unique = models.Constraint(
        "UNIQUE(tipo_servicio, strapi_id)",
        "El servicio ya existe en el catálogo.",
    )

    @api.model
    def _get_strapi_base_url(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("incas_reservas.strapi_url")
            or os.getenv("STRAPI_URL")
            or "http://backend:1336"
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
    def _get_currency_rates(self):
        base_url = self._get_strapi_base_url().rstrip("/")
        try:
            with urlopen(f"{base_url}/api/pagos/tipo-cambio", timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, ValueError, json.JSONDecodeError):
            payload = {}
        return {
            "PEN": float(payload.get("PEN") or 3.75),
            "EUR": float(payload.get("EUR") or 0.92),
        }

    @api.model
    def _sync_estilos_transporte(self):
        estilo_model = self.env["incas.estilo.transporte"]
        records = self._fetch_strapi_records(
            "tipo-transportes",
            {
                "fields[0]": "nombre",
                "fields[1]": "slug",
            },
        )
        seen_ids = []
        for item in records:
            strapi_id = item.get("id")
            if not strapi_id:
                continue
            seen_ids.append(strapi_id)
            values = {
                "name": item.get("nombre"),
                "strapi_id": strapi_id,
                "slug": item.get("slug"),
                "active": True,
            }
            estilo = estilo_model.search([("strapi_id", "=", strapi_id)], limit=1)
            if estilo:
                estilo.write(values)
            else:
                estilo_model.create(values)
        stale_records = estilo_model.search([("strapi_id", "not in", seen_ids)])
        if stale_records:
            stale_records.write({"active": False})

    @api.model
    def _sync_tours(self):
        records = self._fetch_strapi_records(
            "tour-detalles",
            {
                "fields[0]": "title",
                "fields[1]": "slug",
                "fields[2]": "tourType",
                "fields[3]": "adultUnitPrice",
                "fields[4]": "childUnitPrice",
                "fields[5]": "discount",
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
            service = self.search(
                [("tipo_servicio", "=", "tour"), ("strapi_id", "=", strapi_id)], limit=1
            )
            if service:
                service.write(values)
            else:
                self.create(values)
        stale_records = self.search(
            [("tipo_servicio", "=", "tour"), ("strapi_id", "not in", seen_ids)]
        )
        if stale_records:
            stale_records.write({"active": False})

    @api.model
    def _sync_transportes(self):
        records = self._fetch_strapi_records(
            "transportes",
            {
                "fields[0]": "nombre",
                "fields[1]": "slug",
                "populate[tipos_transporte][fields][0]": "nombre",
                "populate[tipos_transporte][fields][1]": "slug",
                "populate[precios][fields][0]": "precioAdulto",
                "populate[precios][fields][1]": "precioNino",
                "populate[precios][fields][2]": "descuento",
            },
        )
        seen_ids = []
        estilo_model = self.env["incas.estilo.transporte"]
        for item in records:
            strapi_id = item.get("id")
            if not strapi_id:
                continue
            seen_ids.append(strapi_id)
            estilo = False
            tipos_transporte = item.get("tipos_transporte") or []
            if tipos_transporte:
                estilo = estilo_model.search(
                    [("strapi_id", "=", tipos_transporte[0].get("id"))], limit=1
                )
            values = {
                "name": item.get("nombre"),
                "tipo_servicio": "transporte",
                "tipo_tour": False,
                "estilo_transporte_id": estilo.id if estilo else False,
                "precio_adulto": float(
                    ((item.get("precios") or [{}])[0]).get("precioAdulto") or 0
                ),
                "precio_nino": float(
                    ((item.get("precios") or [{}])[0]).get("precioNino") or 0
                ),
                "descuento": float(
                    ((item.get("precios") or [{}])[0]).get("descuento") or 0
                ),
                "strapi_id": strapi_id,
                "strapi_document_id": item.get("documentId"),
                "slug": item.get("slug"),
                "active": True,
            }
            service = self.search(
                [("tipo_servicio", "=", "transporte"), ("strapi_id", "=", strapi_id)],
                limit=1,
            )
            if service:
                service.write(values)
            else:
                self.create(values)
        stale_records = self.search(
            [("tipo_servicio", "=", "transporte"), ("strapi_id", "not in", seen_ids)]
        )
        if stale_records:
            stale_records.write({"active": False})

    @api.model
    def sync_from_strapi(self):
        self._sync_estilos_transporte()
        self._sync_tours()
        self._sync_transportes()
        return True
