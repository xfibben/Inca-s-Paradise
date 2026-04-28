from random import randint
from uuid import uuid4
import os
import json
import logging
from urllib.request import Request, urlopen

from odoo import api, fields, models

from ..utils import (
    enviar_correo_resend,
    generar_pdf_desde_html,
    html_correo_reserva,
    render_reserva_html,
)

_logger = logging.getLogger(__name__)


class IncasReserva(models.Model):
    _name = "incas.reserva"
    _description = "Reserva"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Código", required=True, copy=False, readonly=True, default="Nuevo", tracking=True)
    ticket = fields.Char(string="Ticket", copy=False, readonly=True, index=True, tracking=True)
    access_token = fields.Char(string="Token de acceso", copy=False, readonly=True, index=True)
    cotizacion_id = fields.Many2one("incas.cotizacion", string="Cotización", tracking=True)
    paquete_linea_ids = fields.One2many(related="cotizacion_id.paquete_linea_ids", string="Líneas del paquete", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Cliente principal", required=True, tracking=True)
    nombre = fields.Char(string="Nombre completo", tracking=True)
    email = fields.Char(string="Correo electrónico", tracking=True)
    telefono = fields.Char(string="Teléfono", tracking=True)
    tipo_documento = fields.Selection(
        [
            ("dni", "DNI"),
            ("pasaporte", "Pasaporte"),
            ("rut", "RUT"),
            ("ce", "CE"),
            ("otro", "Otro"),
        ],
        string="Tipo de documento",
        tracking=True,
    )
    numero_documento = fields.Char(string="Número de documento", tracking=True)
    nacionalidad = fields.Char(string="Nacionalidad", tracking=True)
    fecha_reserva = fields.Date(string="Fecha de reserva", default=fields.Date.context_today, required=True, tracking=True)
    fecha_inicio = fields.Date(string="Fecha de inicio", tracking=True)
    fecha_fin = fields.Date(string="Fecha de fin", tracking=True)
    fecha_viaje = fields.Date(string="Fecha de viaje", tracking=True)
    turno = fields.Char(string="Horario", tracking=True)
    vehiculo_id = fields.Many2one("incas.catalogo.vehiculo", string="Vehículo", tracking=True)
    vehiculo_disponible_ids = fields.Many2many("incas.catalogo.vehiculo", compute="_compute_vehiculo_disponible_ids")
    vehiculo_seleccionado = fields.Char(string="Vehículo seleccionado", tracking=True)
    idioma = fields.Selection(
        [
            ("es", "Español"),
            ("en", "Inglés"),
            ("pt", "Portugués"),
            ("fr", "Francés"),
            ("it", "Italiano"),
        ],
        string="Idioma",
        required=True,
        default="es",
        tracking=True,
    )
    canal_venta = fields.Selection(
        [
            ("web", "Web"),
            ("whatsapp", "WhatsApp"),
            ("correo", "Correo"),
            ("agencia", "Agencia"),
            ("oficina", "Oficina"),
            ("otro", "Otro"),
        ],
        string="Canal",
        required=True,
        default="web",
        tracking=True,
    )
    tipo_servicio = fields.Selection(
        [
            ("tour", "Tour"),
            ("transporte", "Transporte"),
            ("paquete", "Paquete"),
        ],
        string="Tour o transporte",
        required=True,
        tracking=True,
    )
    tipo_tour = fields.Selection(
        [
            ("tour", "Tour"),
            ("small_trip", "Small Trip"),
            ("package", "Package"),
        ],
        string="Tipo de tour",
        tracking=True,
    )
    estilo_transporte_id = fields.Many2one("incas.estilo.transporte", string="Estilo de transporte", tracking=True)
    servicio_id = fields.Many2one(
        "incas.servicio.catalogo",
        string="Servicio",
        domain="[('tipo_servicio', '=', tipo_servicio), '|', ('tipo_tour', '=', False), ('tipo_tour', '=', tipo_tour), '|', ('estilo_transporte_id', '=', False), ('estilo_transporte_id', '=', estilo_transporte_id)]",
        tracking=True,
    )
    servicio_nombre = fields.Char(string="Nombre del servicio", required=True, tracking=True)
    precio_adulto_usd = fields.Float(string="Precio adulto base USD")
    precio_nino_usd = fields.Float(string="Precio niño base USD")
    precio_adulto = fields.Float(string="Precio adulto", tracking=True)
    precio_nino = fields.Float(string="Precio niño", tracking=True)
    descuento = fields.Float(string="Descuento", tracking=True)
    precio_tour = fields.Float(string="Precio total del servicio", compute="_compute_precio_tour", store=True, tracking=True)
    precio_adulto_web = fields.Float(string="Precio web adultos", tracking=True)
    precio_nino_web = fields.Float(string="Precio web niños", tracking=True)
    monto_web = fields.Float(string="Monto pagado en web", compute="_compute_monto_web", store=True, tracking=True)
    pago_restante = fields.Float(string="Pago restante", compute="_compute_pago_restante", store=True, tracking=True)
    monto_final = fields.Float(string="Monto final", compute="_compute_monto_final", store=True, tracking=True)
    cantidad_adultos = fields.Integer(string="Cantidad adultos", default=1, required=True, tracking=True)
    cantidad_ninos = fields.Integer(string="Cantidad niños", default=0, required=True, tracking=True)
    cantidad_pasajeros = fields.Integer(string="Cantidad de pasajeros", compute="_compute_cantidad_pasajeros", store=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="PEN",
        tracking=True,
    )
    monto_total = fields.Float(string="Monto total", compute="_compute_monto_total", store=True, tracking=True)
    monto_pagado = fields.Float(string="Monto pagado", compute="_compute_monto_pagado", store=True, tracking=True)
    saldo_pendiente = fields.Float(string="Saldo pendiente", compute="_compute_saldo_pendiente", store=True)
    estado_reserva = fields.Selection(
        [
            ("reservado", "Reservado"),
            ("por_coordinar", "Por coordinar"),
            ("falta_pago", "Falta pago"),
            ("pagado", "Pagado"),
            ("completado", "Completado"),
            ("finalizado", "Finalizado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado de reserva",
        required=True,
        default="reservado",
        tracking=True,
    )
    estado_pago = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("parcial", "Parcial"),
            ("pagado", "Pagado"),
            ("reembolsado", "Reembolsado"),
        ],
        string="Estado de pago",
        compute="_compute_estado_pago",
        store=True,
        tracking=True,
    )
    responsable_id = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user, tracking=True)
    observaciones = fields.Text(string="Observaciones")
    pago_ids = fields.One2many("incas.pago", "reserva_id", string="Pagos")
    pago_count = fields.Integer(string="Cantidad de pagos", compute="_compute_pago_count")
    pasajero_ids = fields.One2many("incas.pasajero", "reserva_id", string="Pasajeros")
    origen_web = fields.Boolean(string="Origen web", default=False, tracking=True)
    active = fields.Boolean(default=True)

    @api.depends("cantidad_adultos", "cantidad_ninos", "pasajero_ids")
    def _compute_cantidad_pasajeros(self):
        for record in self:
            if record.pasajero_ids:
                record.cantidad_pasajeros = len(record.pasajero_ids)
            else:
                record.cantidad_pasajeros = (record.cantidad_adultos or 0) + (record.cantidad_ninos or 0) or record.cotizacion_id.cantidad_pasajeros or 1

    @api.depends("servicio_id", "tipo_servicio")
    def _compute_vehiculo_disponible_ids(self):
        for record in self:
            if record.servicio_id and record.tipo_servicio == "transporte":
                record.vehiculo_disponible_ids = record.servicio_id.obtener_vehiculos_transporte()
            else:
                record.vehiculo_disponible_ids = self.env["incas.catalogo.vehiculo"]

    @api.depends("cantidad_adultos", "cantidad_ninos", "precio_adulto", "precio_nino", "descuento")
    def _compute_monto_total(self):
        for record in self:
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.monto_total = subtotal - descuento_monto

    @api.depends("precio_tour", "monto_total", "monto_pagado")
    def _compute_saldo_pendiente(self):
        for record in self:
            total_objetivo = record.precio_tour or record.monto_total
            record.saldo_pendiente = total_objetivo - record.monto_pagado

    @api.depends("saldo_pendiente")
    def _compute_pago_restante(self):
        for record in self:
            record.pago_restante = record.saldo_pendiente or 0

    @api.depends("precio_adulto_web", "precio_nino_web")
    def _compute_monto_web(self):
        for record in self:
            record.monto_web = (record.precio_adulto_web or 0) + (record.precio_nino_web or 0)

    @api.depends("monto_web", "saldo_pendiente")
    def _compute_monto_final(self):
        for record in self:
            record.monto_final = (record.monto_web or 0) + (record.saldo_pendiente or 0)

    @api.depends("monto_total")
    def _compute_precio_tour(self):
        for record in self:
            record.precio_tour = record.monto_total or 0

    @api.depends("pago_ids")
    def _compute_pago_count(self):
        for record in self:
            record.pago_count = len(record.pago_ids)

    @api.depends("pago_ids.estado", "pago_ids.monto_reserva")
    def _compute_monto_pagado(self):
        for record in self:
            record.monto_pagado = sum(record.pago_ids.filtered(lambda pago: pago.estado == "pagado").mapped("monto_reserva"))

    @api.depends("pago_ids.estado", "pago_ids.monto_reserva", "precio_tour", "monto_total")
    def _compute_estado_pago(self):
        for record in self:
            monto_objetivo = record.precio_tour or record.monto_total
            monto_pagado = sum(record.pago_ids.filtered(lambda pago: pago.estado == "pagado").mapped("monto_reserva"))
            estados = set(record.pago_ids.mapped("estado"))
            if "reembolsado" in estados and not {"pagado", "pendiente"} & estados:
                record.estado_pago = "reembolsado"
            elif monto_objetivo > 0 and monto_pagado >= monto_objetivo:
                record.estado_pago = "pagado"
            elif monto_pagado > 0:
                record.estado_pago = "parcial"
            else:
                record.estado_pago = "pendiente"

    def _convertir_desde_usd(self, monto_usd, moneda, rates):
        if moneda == "PEN":
            return monto_usd * rates["PEN"]
        if moneda == "EUR":
            return monto_usd * rates["EUR"]
        return monto_usd

    def _aplicar_moneda_desde_base(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            record.precio_adulto = record._convertir_desde_usd(record.precio_adulto_usd or 0, record.moneda, rates)
            record.precio_nino = record._convertir_desde_usd(record.precio_nino_usd or 0, record.moneda, rates)

    @api.model
    def _generar_ticket(self):
        fecha = fields.Date.context_today(self)
        yyyymmdd = fecha.strftime("%Y%m%d")
        return f"TICKET-{yyyymmdd}-{randint(0, 99999):05d}"

    @api.model
    def _generar_access_token(self):
        return uuid4().hex

    def _limpiar_servicio(self):
        for record in self:
            record.servicio_id = False
            record.servicio_nombre = False
            record.precio_adulto_usd = 0
            record.precio_nino_usd = 0
            record.precio_adulto = 0
            record.precio_nino = 0
            record.descuento = 0

    def _aplicar_cotizacion(self, cotizacion):
        self.ensure_one()
        values = self._valores_desde_cotizacion(cotizacion)
        for field_name, value in values.items():
            self[field_name] = value
        self._compute_monto_total()
        self._compute_precio_tour()
        self._compute_saldo_pendiente()
        self._compute_pago_restante()
        self._compute_monto_final()

    @api.model
    def _valores_desde_cotizacion(self, cotizacion):
        resumen = cotizacion._get_resumen_servicio()
        vehiculo = cotizacion.paquete_linea_ids[:1].vehiculo_id if len(cotizacion.paquete_linea_ids) == 1 else self.env["incas.catalogo.vehiculo"]
        horario = cotizacion.paquete_linea_ids[:1].horario if len(cotizacion.paquete_linea_ids) == 1 else False
        return {
            "partner_id": cotizacion.partner_id,
            "fecha_viaje": cotizacion.fecha_viaje,
            "turno": horario,
            "idioma": cotizacion.idioma,
            "canal_venta": cotizacion.canal_venta,
            "tipo_servicio": resumen["tipo_servicio"],
            "tipo_tour": resumen["tipo_tour"],
            "estilo_transporte_id": resumen["estilo_transporte_id"],
            "servicio_id": resumen["servicio_id"],
            "servicio_nombre": cotizacion.servicio_nombre or resumen["servicio_nombre"],
            "precio_adulto_usd": resumen["precio_adulto_usd"],
            "precio_nino_usd": resumen["precio_nino_usd"],
            "precio_adulto": resumen["precio_adulto"],
            "precio_nino": resumen["precio_nino"],
            "descuento": resumen["descuento"],
            "cantidad_adultos": cotizacion.cantidad_adultos,
            "cantidad_ninos": cotizacion.cantidad_ninos,
            "moneda": cotizacion.moneda,
            "responsable_id": cotizacion.responsable_id,
            "vehiculo_id": vehiculo,
            "vehiculo_seleccionado": vehiculo.name if vehiculo else False,
            "observaciones": cotizacion.observaciones,
        }

    @api.model
    def _normalizar_fecha_web(self, valor):
        if not valor:
            return False
        texto_fecha = str(valor)
        return texto_fecha[:10]

    @api.model
    def _buscar_servicio_web(self, reserva_data):
        servicio_model = self.env["incas.servicio.catalogo"].sudo()
        tour_document_id = reserva_data.get("tourDocumentId")
        transporte_document_id = reserva_data.get("transporteDocumentId")
        tour_numeric_id = reserva_data.get("tourNumericId")
        transporte_numeric_id = reserva_data.get("transporteNumericId")
        tour_rel = ((reserva_data.get("tour") or {}).get("connect") or [None])[0]
        transporte_rel = ((reserva_data.get("transportes") or {}).get("connect") or [None])[0]
        if isinstance(tour_rel, str) and not tour_document_id:
            tour_document_id = tour_rel
        if isinstance(transporte_rel, str) and not transporte_document_id:
            transporte_document_id = transporte_rel
        if isinstance(tour_rel, dict) and not tour_numeric_id:
            tour_numeric_id = tour_rel.get("id")
        if isinstance(transporte_rel, dict) and not transporte_numeric_id:
            transporte_numeric_id = transporte_rel.get("id")
        for intento in range(2):
            servicio = False
            if tour_document_id:
                servicio = servicio_model.search([("tipo_servicio", "=", "tour"), ("strapi_document_id", "=", tour_document_id)], limit=1)
            elif tour_numeric_id:
                servicio = servicio_model.search([("tipo_servicio", "=", "tour"), ("strapi_id", "=", int(tour_numeric_id))], limit=1)
            elif transporte_document_id:
                servicio = servicio_model.search([("tipo_servicio", "=", "transporte"), ("strapi_document_id", "=", transporte_document_id)], limit=1)
            elif transporte_numeric_id:
                servicio = servicio_model.search([("tipo_servicio", "=", "transporte"), ("strapi_id", "=", int(transporte_numeric_id))], limit=1)
            if servicio or intento == 1:
                return servicio
            servicio_model.sync_from_strapi()
        return False

    @api.model
    def _buscar_vehiculo_web(self, servicio, reserva_data):
        nombre = reserva_data.get("vehiculo_seleccionado")
        if not servicio or servicio.tipo_servicio != "transporte":
            return self.env["incas.catalogo.vehiculo"]
        return servicio.obtener_vehiculo_transporte(nombre=nombre)

    @api.model
    def _buscar_horario_web(self, servicio, reserva_data):
        nombre = (reserva_data.get("turno") or "").strip()
        if not servicio or not nombre:
            return self.env["incas.horario.opcion"]
        return self.env["incas.horario.opcion"].sudo().search(
            [("servicio_id", "=", servicio.id), ("name", "=", nombre)],
            limit=1,
        )

    @api.model
    def _obtener_partner_web(self, reserva_data):
        partner_model = self.env["res.partner"].sudo()
        email = (reserva_data.get("email") or "").strip()
        telefono = (reserva_data.get("telefono") or "").strip()
        nombre = (reserva_data.get("nombre") or "").strip() or "Cliente web"
        partner = False
        if email:
            partner = partner_model.search([("email", "=", email)], limit=1)
        if not partner and telefono:
            partner = partner_model.search([("phone", "=", telefono)], limit=1)
        values = {
            "name": nombre,
            "email": email or False,
            "phone": telefono or False,
        }
        if partner:
            partner.write(values)
        else:
            partner = partner_model.create(values)
        return partner

    @api.model
    def _preparar_valores_web(self, reserva_data):
        servicio = self._buscar_servicio_web(reserva_data)
        if not servicio:
            raise ValueError("No se encontró el servicio en Odoo")
        vehiculo = self._buscar_vehiculo_web(servicio, reserva_data)
        partner = self._obtener_partner_web(reserva_data)
        moneda = reserva_data.get("moneda") or reserva_data.get("moneda_usuario") or "USD"
        fecha_inicio = self._normalizar_fecha_web(reserva_data.get("fecha_inicio"))
        fecha_fin = self._normalizar_fecha_web(reserva_data.get("fecha_fin"))
        cotizacion = self._crear_cotizacion_web(reserva_data, partner, servicio, moneda, fecha_inicio)
        resumen = cotizacion._get_resumen_servicio()
        valores = {
            "cotizacion_id": cotizacion.id,
            "partner_id": partner.id,
            "nombre": reserva_data.get("nombre"),
            "email": reserva_data.get("email"),
            "telefono": reserva_data.get("telefono"),
            "tipo_documento": reserva_data.get("tipo_documento") or "otro",
            "numero_documento": reserva_data.get("numero_documento"),
            "nacionalidad": reserva_data.get("nacionalidad"),
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_viaje": fecha_inicio or self._normalizar_fecha_web(reserva_data.get("fecha_viaje")),
            "vehiculo_id": vehiculo.id,
            "vehiculo_seleccionado": vehiculo.name if vehiculo else reserva_data.get("vehiculo_seleccionado"),
            "idioma": reserva_data.get("idioma") or "es",
            "canal_venta": "web",
            "servicio_id": resumen["servicio_id"].id,
            "tipo_servicio": resumen["tipo_servicio"],
            "tipo_tour": resumen["tipo_tour"],
            "estilo_transporte_id": resumen["estilo_transporte_id"].id,
            "servicio_nombre": resumen["servicio_nombre"],
            "cantidad_adultos": int(reserva_data.get("cantidad_adultos") or 1),
            "cantidad_ninos": int(reserva_data.get("cantidad_ninos") or 0),
            "moneda": moneda,
            "precio_adulto_usd": resumen["precio_adulto_usd"],
            "precio_nino_usd": resumen["precio_nino_usd"],
            "precio_adulto": resumen["precio_adulto"],
            "precio_nino": resumen["precio_nino"],
            "descuento": resumen["descuento"],
            "precio_adulto_web": float(reserva_data.get("precio_adulto_web") or 0),
            "precio_nino_web": float(reserva_data.get("precio_nino_web") or 0),
            "origen_web": True,
            "observaciones": reserva_data.get("notas"),
        }
        return valores

    @api.model
    def _crear_cotizacion_web(self, reserva_data, partner, servicio, moneda, fecha_viaje):
        cotizacion_model = self.env["incas.cotizacion"].sudo()
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vehiculo = self._buscar_vehiculo_web(servicio, reserva_data)
        horario = self._buscar_horario_web(servicio, reserva_data)
        tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo) if servicio.tipo_servicio == "transporte" else {
            "precio_adulto": servicio.precio_adulto or 0,
            "precio_nino": servicio.precio_nino or 0,
            "descuento": servicio.descuento or 0,
        }
        descuento = float(reserva_data.get("descuento") or reserva_data.get("descuento_usd") or tarifa["descuento"] or 0)
        precio_adulto = self._convertir_desde_usd(tarifa["precio_adulto"] or 0, moneda, rates)
        precio_nino = self._convertir_desde_usd(tarifa["precio_nino"] or 0, moneda, rates)
        return cotizacion_model.create(
            {
                "partner_id": partner.id,
                "fecha_viaje": fecha_viaje or self._normalizar_fecha_web(reserva_data.get("fecha_viaje")),
                "idioma": reserva_data.get("idioma") or "es",
                "canal_venta": "web",
                "tipo_servicio": servicio.tipo_servicio,
                "tipo_tour": servicio.tipo_tour,
                "estilo_transporte_id": servicio.estilo_transporte_id.id,
                "servicio_id": servicio.id,
                "cantidad_adultos": int(reserva_data.get("cantidad_adultos") or 1),
                "cantidad_ninos": int(reserva_data.get("cantidad_ninos") or 0),
                "moneda": moneda,
                "observaciones": reserva_data.get("notas"),
                "paquete_linea_ids": [
                    (
                        0,
                        0,
                        {
                            "servicio_id": servicio.id,
                            "vehiculo_id": vehiculo.id,
                            "horario": horario.name or reserva_data.get("turno"),
                            "horario_id": horario.id,
                            "precio_adulto": precio_adulto,
                            "precio_nino": precio_nino,
                            "descuento": descuento,
                        },
                    )
                ],
            }
        )

    def _actualizar_pendientes(self):
        for record in self:
            total_objetivo = record.precio_tour or record.monto_total
            saldo = max(total_objetivo - record.monto_pagado, 0)
            estado_reserva = "pagado" if saldo <= 0 else "falta_pago"
            super(IncasReserva, record).write(
                {
                    "estado_reserva": estado_reserva,
                }
            )

    def _sincronizar_con_sheets(self):
        url = os.getenv("GOOGLE_APPS_SCRIPT_URL", "")
        if not url:
            return
        for record in self:
            entry = {
                "fecha": fields.Datetime.to_string(fields.Datetime.now()),
                "id": record.ticket or record.id,
                "nombre_pax": record.nombre or record.partner_id.display_name or "",
                "email": record.email or record.partner_id.email or "",
                "telefono": record.telefono or record.partner_id.phone or "",
                "tipo_documento": record.tipo_documento or "",
                "numero_documento": record.numero_documento or "",
                "nacionalidad": record.nacionalidad or "",
                "cantidad_adultos": record.cantidad_adultos or 0,
                "cantidad_ninos": record.cantidad_ninos or 0,
                "precio_adulto": record.precio_adulto or 0,
                "precio_nino": record.precio_nino or 0,
                "precio_adulto_web": record.precio_adulto_web or 0,
                "precio_nino_web": record.precio_nino_web or 0,
                "fecha_inicio": fields.Date.to_string(record.fecha_inicio or record.fecha_viaje or False) or "",
                "fecha_fin": fields.Date.to_string(record.fecha_fin or record.fecha_viaje or False) or "",
                "hora_recojo": record.turno or "",
                "vehiculo": record.vehiculo_seleccionado or "",
                "nombre_reserva": record.servicio_nombre or "",
                "tipo_servicio": record.tipo_servicio or "",
                "descuento": record.descuento or 0,
                "precio_tour": record.precio_tour or 0,
                "adelanto": record.monto_web or 0,
                "saldo": record.saldo_pendiente or 0,
                "pago_total": record.monto_final or 0,
                "estado": record.estado_reserva or "reservado",
                "estado_pago": record.estado_pago or "",
                "moneda": record.moneda or "USD",
                "canal_venta": "Web" if record.origen_web else "Back Office",
                "notas": record.observaciones or "",
                "prepend": True,
            }
            body = json.dumps({"entry": entry}).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            request_data = Request(url, data=body, headers=headers, method="POST")
            urlopen(request_data, timeout=20).read()

    def _enviar_correos_reserva(self):
        api_key = os.getenv("RESEND_API_KEY", "")
        from_email = os.getenv("RESEND_FROM_EMAIL", "")
        from_name = (os.getenv("RESEND_FROM_NAME", "INCA'S PARADISE") or "INCA'S PARADISE").upper()
        notify_email = os.getenv("RESEND_NOTIFY_EMAIL", "")
        if not api_key or not from_email:
            return
        remitente = f"{from_name} <{from_email}>"
        for record in self:
            pdf = generar_pdf_desde_html(render_reserva_html(record))
            html_admin = html_correo_reserva(record, "Nueva reserva recibida", "Se registró una nueva reserva y el comprobante PDF va adjunto.")
            html_cliente = html_correo_reserva(record, "Confirmación de reserva", f"Hola {record.nombre or record.partner_id.display_name}, tu reserva fue registrada correctamente. Adjuntamos el comprobante PDF.")
            if notify_email:
                enviar_correo_resend(api_key, remitente, notify_email, f"INCA'S PARADISE - Nueva reserva {record.ticket}", html_admin, pdf, record.ticket)
            if record.email:
                enviar_correo_resend(api_key, remitente, record.email, f"INCA'S PARADISE - Confirmación de reserva {record.ticket}", html_cliente, pdf, record.ticket)

    def _post_reserva_web(self):
        for record in self:
            record._actualizar_pendientes()
            try:
                record._sincronizar_con_sheets()
            except Exception:
                _logger.exception("Error al sincronizar reserva %s con Google Sheets", record.ticket)
            try:
                record._enviar_correos_reserva()
            except Exception:
                _logger.exception("Error al enviar correos de la reserva %s", record.ticket)

    def get_public_voucher_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        return f"{base_url}/incas/public/reserva/{self.id}/pdf/{self.access_token}"

    @api.model
    def crear_reserva_web(self, reserva_data, pago_data=None):
        valores = self._preparar_valores_web(reserva_data)
        reserva = self.sudo().create(valores)
        if pago_data:
            self.env["incas.pago"].sudo().create(
                {
                    "reserva_id": reserva.id,
                    "proveedor": pago_data.get("proveedor") or "izipay",
                    "metodo": pago_data.get("metodo") or "tarjeta",
                    "moneda": pago_data.get("moneda") or reserva.moneda,
                    "monto": float(pago_data.get("monto") or 0),
                    "estado": pago_data.get("estado") or "pagado",
                    "transaccion_id": pago_data.get("transaccion_id"),
                    "orden_id": pago_data.get("orden_id"),
                    "codigo_respuesta": pago_data.get("codigo_respuesta"),
                    "mensaje_respuesta": pago_data.get("mensaje_respuesta"),
                    "qr_url": pago_data.get("qr_url"),
                    "fecha_pago": pago_data.get("fecha_pago") or fields.Datetime.now(),
                    "ip_cliente": pago_data.get("ip_cliente"),
                }
            )
        reserva._post_reserva_web()
        return reserva

    @api.model
    def _completar_datos_servicio(self, vals):
        cotizacion_id = vals.get("cotizacion_id")
        if cotizacion_id:
            cotizacion = self.env["incas.cotizacion"].browse(cotizacion_id)
            if cotizacion.exists():
                values = self._valores_desde_cotizacion(cotizacion)
                vals.update(
                    {
                        "partner_id": values["partner_id"].id,
                        "fecha_viaje": values["fecha_viaje"],
                        "turno": values["turno"],
                        "idioma": values["idioma"],
                        "canal_venta": values["canal_venta"],
                        "tipo_servicio": values["tipo_servicio"],
                        "tipo_tour": values["tipo_tour"],
                        "estilo_transporte_id": values["estilo_transporte_id"].id,
                        "servicio_id": values["servicio_id"].id,
                        "servicio_nombre": values["servicio_nombre"],
                        "precio_adulto_usd": values["precio_adulto_usd"],
                        "precio_nino_usd": values["precio_nino_usd"],
                        "precio_adulto": values["precio_adulto"],
                        "precio_nino": values["precio_nino"],
                        "descuento": values["descuento"],
                        "cantidad_adultos": values["cantidad_adultos"],
                        "cantidad_ninos": values["cantidad_ninos"],
                        "moneda": values["moneda"],
                        "responsable_id": values["responsable_id"].id,
                        "vehiculo_id": values["vehiculo_id"].id,
                        "vehiculo_seleccionado": values["vehiculo_seleccionado"],
                        "observaciones": values["observaciones"],
                    }
                )
                return vals
        servicio_id = vals.get("servicio_id")
        if not servicio_id and vals.get("vehiculo_id") and len(self) == 1 and self.servicio_id and self.servicio_id.tipo_servicio == "transporte":
            servicio = self.servicio_id
            vehiculo = servicio.obtener_vehiculo_transporte(
                nombre=vals.get("vehiculo_seleccionado"),
                vehiculo_id=vals.get("vehiculo_id"),
            )
            if vehiculo and not vals.get("vehiculo_seleccionado"):
                vals["vehiculo_seleccionado"] = vehiculo.name
            tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo)
            vals.setdefault("precio_adulto_usd", tarifa["precio_adulto"])
            vals.setdefault("precio_nino_usd", tarifa["precio_nino"])
            vals.setdefault("descuento", tarifa["descuento"])
            moneda = vals.get("moneda") or self.moneda or "PEN"
            rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
            vals["precio_adulto"] = self._convertir_desde_usd(vals.get("precio_adulto_usd") or 0, moneda, rates)
            vals["precio_nino"] = self._convertir_desde_usd(vals.get("precio_nino_usd") or 0, moneda, rates)
            return vals
        if not servicio_id:
            return vals
        servicio = self.env["incas.servicio.catalogo"].browse(servicio_id)
        if not servicio.exists():
            return vals
        vals.setdefault("tipo_servicio", servicio.tipo_servicio)
        vals.setdefault("tipo_tour", servicio.tipo_tour)
        vals.setdefault("estilo_transporte_id", servicio.estilo_transporte_id.id)
        vals.setdefault("servicio_nombre", servicio.name)
        vehiculo = False
        if servicio.tipo_servicio == "transporte":
            vehiculo = servicio.obtener_vehiculo_transporte(
                nombre=vals.get("vehiculo_seleccionado"),
                vehiculo_id=vals.get("vehiculo_id"),
            )
            if vehiculo and not vals.get("vehiculo_id"):
                vals["vehiculo_id"] = vehiculo.id
            if vehiculo and not vals.get("vehiculo_seleccionado"):
                vals["vehiculo_seleccionado"] = vehiculo.name
            tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo)
            vals.setdefault("precio_adulto_usd", tarifa["precio_adulto"])
            vals.setdefault("precio_nino_usd", tarifa["precio_nino"])
            vals.setdefault("descuento", tarifa["descuento"])
        else:
            vals.setdefault("vehiculo_id", False)
            vals.setdefault("vehiculo_seleccionado", False)
            vals.setdefault("precio_adulto_usd", servicio.precio_adulto)
            vals.setdefault("precio_nino_usd", servicio.precio_nino)
            vals.setdefault("descuento", servicio.descuento)
        moneda = vals.get("moneda") or "PEN"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vals["precio_adulto"] = self._convertir_desde_usd(vals.get("precio_adulto_usd") or 0, moneda, rates)
        vals["precio_nino"] = self._convertir_desde_usd(vals.get("precio_nino_usd") or 0, moneda, rates)
        return vals

    @api.onchange("tipo_servicio")
    def _onchange_tipo_servicio(self):
        for record in self:
            if record.cotizacion_id or record.tipo_servicio == "paquete":
                continue
            if record.tipo_servicio == "tour":
                record.estilo_transporte_id = False
                if not record.tipo_tour:
                    record.tipo_tour = "tour"
            elif record.tipo_servicio == "transporte":
                record.tipo_tour = False
            if not record.servicio_id:
                record._limpiar_servicio()
                continue
            if record.servicio_id.tipo_servicio != record.tipo_servicio:
                record._limpiar_servicio()

    @api.onchange("tipo_tour", "estilo_transporte_id")
    def _onchange_tipo_detalle_servicio(self):
        for record in self:
            if record.cotizacion_id or record.tipo_servicio == "paquete":
                continue
            if not record.servicio_id:
                record._limpiar_servicio()
                continue
            if record.tipo_servicio == "tour" and record.servicio_id.tipo_tour != record.tipo_tour:
                record._limpiar_servicio()
            if record.tipo_servicio == "transporte" and record.servicio_id.estilo_transporte_id != record.estilo_transporte_id:
                record._limpiar_servicio()

    @api.onchange("servicio_id")
    def _onchange_servicio_id(self):
        for record in self:
            if record.cotizacion_id:
                continue
            if not record.servicio_id:
                continue
            record.tipo_servicio = record.servicio_id.tipo_servicio
            record.tipo_tour = record.servicio_id.tipo_tour
            record.estilo_transporte_id = record.servicio_id.estilo_transporte_id
            record.servicio_nombre = record.servicio_id.name
            if record.servicio_id.tipo_servicio == "transporte":
                record.vehiculo_id = record.servicio_id.obtener_vehiculo_transporte(
                    nombre=record.vehiculo_seleccionado,
                    vehiculo_id=record.vehiculo_id.id,
                )
                record.vehiculo_seleccionado = record.vehiculo_id.name if record.vehiculo_id else False
                tarifa = record.servicio_id.obtener_tarifa_vehiculo_transporte(record.vehiculo_id)
                record.precio_adulto_usd = tarifa["precio_adulto"]
                record.precio_nino_usd = tarifa["precio_nino"]
                record.descuento = tarifa["descuento"]
            else:
                record.vehiculo_id = False
                record.vehiculo_seleccionado = False
                record.precio_adulto_usd = record.servicio_id.precio_adulto
                record.precio_nino_usd = record.servicio_id.precio_nino
                record.descuento = record.servicio_id.descuento
            record._aplicar_moneda_desde_base()

    @api.onchange("vehiculo_id")
    def _onchange_vehiculo_id(self):
        for record in self:
            if record.tipo_servicio != "transporte" or not record.servicio_id:
                continue
            record.vehiculo_seleccionado = record.vehiculo_id.name if record.vehiculo_id else False
            tarifa = record.servicio_id.obtener_tarifa_vehiculo_transporte(record.vehiculo_id)
            record.precio_adulto_usd = tarifa["precio_adulto"]
            record.precio_nino_usd = tarifa["precio_nino"]
            record.descuento = tarifa["descuento"]
            record._aplicar_moneda_desde_base()

    @api.onchange("cotizacion_id")
    def _onchange_cotizacion_id(self):
        for record in self:
            cotizacion = record.cotizacion_id
            if not cotizacion:
                continue
            record._aplicar_cotizacion(cotizacion)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        cotizacion_id = self.env.context.get("default_cotizacion_id")
        if cotizacion_id:
            cotizacion = self.env["incas.cotizacion"].browse(cotizacion_id)
            if cotizacion.exists():
                resumen = self._valores_desde_cotizacion(cotizacion)
                values.update(
                    {
                        "partner_id": resumen["partner_id"].id,
                        "fecha_viaje": resumen["fecha_viaje"],
                        "turno": resumen["turno"],
                        "idioma": resumen["idioma"],
                        "canal_venta": resumen["canal_venta"],
                        "tipo_servicio": resumen["tipo_servicio"],
                        "tipo_tour": resumen["tipo_tour"],
                        "estilo_transporte_id": resumen["estilo_transporte_id"].id,
                        "servicio_id": resumen["servicio_id"].id,
                        "servicio_nombre": resumen["servicio_nombre"],
                        "precio_adulto_usd": resumen["precio_adulto_usd"],
                        "precio_nino_usd": resumen["precio_nino_usd"],
                        "precio_adulto": resumen["precio_adulto"],
                        "precio_nino": resumen["precio_nino"],
                        "descuento": resumen["descuento"],
                        "cantidad_adultos": resumen["cantidad_adultos"],
                        "cantidad_ninos": resumen["cantidad_ninos"],
                        "moneda": resumen["moneda"],
                        "responsable_id": resumen["responsable_id"].id,
                        "vehiculo_id": resumen["vehiculo_id"].id,
                        "vehiculo_seleccionado": resumen["vehiculo_seleccionado"],
                        "observaciones": resumen["observaciones"],
                    }
                )
        return values

    @api.onchange("moneda")
    def _onchange_moneda(self):
        if self.cotizacion_id:
            return
        self._aplicar_moneda_desde_base()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.reserva") or "Nuevo"
            if not vals.get("ticket"):
                vals["ticket"] = self._generar_ticket()
            if not vals.get("access_token"):
                vals["access_token"] = self._generar_access_token()
            self._completar_datos_servicio(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._completar_datos_servicio(vals)
        return super().write(vals)

    def action_print_pdf(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/reserva/{self.id}/pdf",
            "target": "self",
        }

    def action_ver_pagos(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Pagos",
            "res_model": "incas.pago",
            "view_mode": "list,form",
            "domain": [("reserva_id", "=", self.id)],
            "context": {
                "default_reserva_id": self.id,
                "default_moneda": self.moneda,
                "default_monto": self.saldo_pendiente or self.precio_tour or self.monto_total,
            },
        }

    def action_nuevo_pago(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nuevo pago",
            "res_model": "incas.pago",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_reserva_id": self.id,
                "default_moneda": self.moneda,
                "default_monto": self.saldo_pendiente or self.precio_tour or self.monto_total,
                "default_estado": "pendiente",
            },
        }
