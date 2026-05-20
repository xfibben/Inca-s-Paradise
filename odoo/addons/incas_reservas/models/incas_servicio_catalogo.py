import json
from urllib.request import Request, urlopen

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
    ip = fields.Selection(
        [
            ("ip3", "IP 3"),
            ("ip2", "IP 2"),
        ],
        string="IP",
        required=True,
        default="ip3",
        index=True,
    )
    slug = fields.Char(string="Slug")
    active = fields.Boolean(default=True)

    def _auto_init(self):
        res = super()._auto_init()
        self.env.cr.execute(
            """
            UPDATE incas_servicio_catalogo
               SET ip = 'ip3'
             WHERE ip IS NULL
            """
        )
        return res

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
            vehiculo = vehiculos.filtered(
                lambda item: nombre in {
                    item.nombre,
                    item.nombre_en,
                    item.nombre_pt,
                }
            )
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
        tasas_fallback = self._obtener_tasas_usd_desde_api()
        try:
            self._asegurar_tasas_monitoreadas()
            company = self.env.company
            fecha = fields.Date.context_today(self)
            currency_model = self.env["res.currency"].with_context(active_test=False)
            usd_currency = currency_model.search([("name", "=", "USD")], limit=1)
            pen_currency = currency_model.search([("name", "=", "PEN")], limit=1)
            eur_currency = currency_model.search([("name", "=", "EUR")], limit=1)

            if not usd_currency:
                return {
                    "PEN": tasas_fallback["PEN"],
                    "EUR": tasas_fallback["EUR"],
                }

            # Si una tasa no está cargada en Odoo, cae a la API externa sin romper el frontend.
            pen_rate = tasas_fallback["PEN"]
            eur_rate = tasas_fallback["EUR"]

            if pen_currency:
                try:
                    pen_rate = float(usd_currency._convert(1.0, pen_currency, company, fecha))
                except Exception:
                    pen_rate = tasas_fallback["PEN"]

            if eur_currency:
                try:
                    eur_rate = float(usd_currency._convert(1.0, eur_currency, company, fecha))
                except Exception:
                    eur_rate = tasas_fallback["EUR"]

            return {
                "PEN": pen_rate,
                "EUR": eur_rate,
            }
        except Exception:
            return {
                "PEN": tasas_fallback["PEN"],
                "EUR": tasas_fallback["EUR"],
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
        return True

    @api.model
    def _cleanup_legacy_catalogo_tour(self):
        xmlids = [
            "incas_reservas.view_incas_catalogo_tour_list",
            "incas_reservas.view_incas_catalogo_tour_search",
            "incas_reservas.view_incas_catalogo_tour_form",
            "incas_reservas.action_incas_catalogo_tour",
            "incas_reservas.menu_incas_catalogo_tour",
            "incas_reservas.access_incas_catalogo_tour_system_xml",
            "incas_reservas.access_incas_catalogo_tour_admin_xml",
            "incas_reservas.access_incas_catalogo_tour_gerencia_xml",
        ]
        for xmlid in xmlids:
            record = self.env.ref(xmlid, raise_if_not_found=False)
            if record:
                record.sudo().unlink()
        self.env["ir.model.data"].sudo().search(
            [
                ("module", "=", "incas_reservas"),
                ("name", "in", [xmlid.split(".")[1] for xmlid in xmlids]),
            ]
        ).unlink()
        self.env["ir.ui.view"].sudo().search([("model", "=", "incas.catalogo.tour")]).unlink()
        self.env["ir.actions.act_window"].sudo().search([("res_model", "=", "incas.catalogo.tour")]).unlink()
        self.env["ir.ui.menu"].sudo().search([("name", "in", ["Catalogo de tours", "Catálogo de tours"])]).unlink()
        model = self.env["ir.model"].sudo().search([("model", "=", "incas.catalogo.tour")], limit=1)
        if model:
            self.env["ir.model.access"].sudo().search([("model_id", "=", model.id)]).unlink()
        self.env.cr.execute("DROP TABLE IF EXISTS incas_catalogo_destino_tour_rel CASCADE")
        self.env.cr.execute("DROP TABLE IF EXISTS incas_subcategoria_tour_catalogo_tour_rel CASCADE")
        self.env.cr.execute("DROP TABLE IF EXISTS incas_catalogo_tour CASCADE")
        return True
