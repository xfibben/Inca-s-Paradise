from random import randint
from uuid import uuid4
import os
import json
import logging
import re
from urllib.request import Request, urlopen

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..utils import (
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
    paquete_linea_ids = fields.One2many("incas.reserva.paquete.linea", "reserva_id", string="Líneas del paquete")
    hotel_linea_ids = fields.One2many("incas.reserva.hotel.linea", "reserva_id", string="Hoteles")
    extra_linea_ids = fields.One2many("incas.reserva.extra.linea", "reserva_id", string="Extras")
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
        default="paquete",
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
    servicio_nombre = fields.Char(string="Nombre del servicio", required=True, default="Paquete personalizado", tracking=True)
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
    hotel_id = fields.Many2one("incas.hotel", string="Hotel", tracking=True)
    hotel_tarifa_id = fields.Many2one(
        "incas.hotel.tarifa",
        string="Tarifa de hotel",
        domain="[('hotel_id', '=', hotel_id)]",
        tracking=True,
    )
    hotel_tipo_tarifario = fields.Selection(
        [("ip", "IP"), ("conf", "CONF FIT"), ("fit", "Rack")],
        string="Tarifario hotel",
        default="ip",
        required=True,
        tracking=True,
    )
    fecha_check_in = fields.Date(string="Check-in", tracking=True)
    fecha_check_out = fields.Date(string="Check-out", tracking=True)
    cantidad_noches = fields.Integer(string="Cantidad noches", compute="_compute_cantidad_noches", store=True)
    cantidad_habitaciones = fields.Integer(string="Cantidad habitaciones", default=1, required=True, tracking=True)
    hotel_nombre = fields.Char(string="Nombre del hotel", tracking=True)
    hotel_precio_noche_usd = fields.Float(string="Precio noche hotel base USD", tracking=True)
    hotel_precio_noche = fields.Float(string="Precio noche hotel", tracking=True)
    hotel_descuento = fields.Float(string="Descuento hotel", tracking=True)
    monto_hotel_usd = fields.Float(string="Monto hotel USD", compute="_compute_monto_hotel", store=True)
    monto_hotel = fields.Float(string="Monto hotel", compute="_compute_monto_hotel", store=True, tracking=True)
    extra_id = fields.Many2one("incas.extra", string="Extra", tracking=True)
    extra_tarifa_id = fields.Many2one(
        "incas.extra.tarifa",
        string="Tarifa de extra",
        domain="[('extra_id', '=', extra_id)]",
        tracking=True,
    )
    extra_nombre = fields.Char(string="Nombre del extra", tracking=True)
    extra_unidad = fields.Selection(
        [("unidad", "Unidad"), ("persona", "Persona"), ("tramo", "Tramo"), ("dia", "Día")],
        string="Unidad extra",
        tracking=True,
    )
    cantidad_extra = fields.Integer(string="Cantidad extra", default=1, required=True, tracking=True)
    extra_precio_unitario_usd = fields.Float(string="Precio unitario extra base USD", tracking=True)
    extra_precio_unitario = fields.Float(string="Precio unitario extra", tracking=True)
    extra_descuento = fields.Float(string="Descuento extra", tracking=True)
    monto_extra_usd = fields.Float(string="Monto extra USD", compute="_compute_monto_extra", store=True)
    monto_extra = fields.Float(string="Monto extra", compute="_compute_monto_extra", store=True, tracking=True)
    moneda = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD"), ("EUR", "EUR")],
        string="Moneda",
        required=True,
        default="PEN",
        tracking=True,
    )
    precio_grupal = fields.Float(string="Precio grupal", compute="_compute_precio_grupal", store=True, tracking=True)
    monto_total = fields.Float(string="Monto total", compute="_compute_monto_total", store=True, tracking=True)
    monto_pagado = fields.Float(string="Monto pagado", compute="_compute_monto_pagado", store=True, tracking=True)
    saldo_pendiente = fields.Float(string="Saldo pendiente", compute="_compute_saldo_pendiente", store=True)
    estado_comercial = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("cotizada", "Cotizada"),
            ("pre_reserva", "Pre-reserva"),
            ("confirmada", "Confirmada"),
            ("cancelada", "Cancelada"),
        ],
        string="Estado comercial",
        required=True,
        default="borrador",
        tracking=True,
    )
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
            ("cancelado", "Cancelado"),
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
    cambio_ids = fields.One2many("incas.reserva.cambio", "reserva_id", string="Solicitudes de cambio")
    cambio_count = fields.Integer(string="Cantidad de cambios", compute="_compute_cambio_count")
    documento_directory_id = fields.Many2one("dms.directory", string="Carpeta documental", readonly=True, copy=False)
    estado_documental = fields.Selection(
        [
            ("sin_pasajeros", "Sin pasajeros"),
            ("pendiente", "Pendiente"),
            ("parcial", "Parcial"),
            ("completo", "Completo"),
        ],
        string="Estado documental",
        compute="_compute_estado_documental",
        store=True,
    )
    pasajeros_documentos_pendientes = fields.Integer(
        string="Pasajeros con documentos pendientes",
        compute="_compute_estado_documental",
        store=True,
    )
    origen_web = fields.Boolean(string="Origen web", default=False, tracking=True)
    active = fields.Boolean(default=True)

    @api.depends("cantidad_adultos", "cantidad_ninos", "pasajero_ids")
    def _compute_cantidad_pasajeros(self):
        for record in self:
            if record.pasajero_ids:
                record.cantidad_pasajeros = len(record.pasajero_ids)
            else:
                record.cantidad_pasajeros = (record.cantidad_adultos or 0) + (record.cantidad_ninos or 0) or 1

    @api.model
    def _nombre_directorio_seguro(self, valor, fallback):
        nombre = (valor or fallback or "").strip()
        nombre = re.sub(r"[\\/:*?\"<>|]+", "-", nombre)
        nombre = re.sub(r"\s+", " ", nombre).strip(" .-_")
        return nombre or fallback

    @api.model
    def _obtener_directorio_raiz_pasajeros(self):
        directory_model = self.env["dms.directory"].sudo()
        pasajeros_directory = directory_model.search(
            [("is_root_directory", "=", True), ("name", "=", "Pasajeros")],
            limit=1,
        )
        if not pasajeros_directory:
            storage = self.env["dms.storage"].sudo().search([], order="id", limit=1)
            if not storage:
                return self.env["dms.directory"]
            pasajeros_directory = directory_model.create(
                {
                    "name": "Pasajeros",
                    "storage_id": storage.id,
                    "is_root_directory": True,
                }
            )
        return pasajeros_directory

    def _asegurar_carpeta_documental(self):
        directory_model = self.env["dms.directory"].sudo()
        pasajeros_directory = self._obtener_directorio_raiz_pasajeros()
        if not pasajeros_directory:
            return
        for record in self:
            nombre_carpeta = self._nombre_directorio_seguro(record.name, f"RESERVA-{record.id}")
            directory = record.documento_directory_id
            if directory:
                valores = {}
                if directory.parent_id != pasajeros_directory:
                    valores["parent_id"] = pasajeros_directory.id
                if directory.name != nombre_carpeta:
                    valores["name"] = nombre_carpeta
                if valores:
                    directory.write(valores)
                continue
            existente = directory_model.search(
                [("parent_id", "=", pasajeros_directory.id), ("name", "=", nombre_carpeta)],
                limit=1,
            )
            if not existente:
                existente = directory_model.create(
                    {
                        "name": nombre_carpeta,
                        "parent_id": pasajeros_directory.id,
                        "is_root_directory": False,
                    }
                )
            record.documento_directory_id = existente.id

    @api.model
    def _separar_nombre_pasajero(self, nombre_completo):
        partes = [parte for parte in (nombre_completo or "").split() if parte]
        if len(partes) >= 4:
            return " ".join(partes[:-2]), " ".join(partes[-2:])
        if len(partes) == 3:
            return " ".join(partes[:2]), partes[2]
        if len(partes) == 2:
            return partes[0], partes[1]
        if len(partes) == 1:
            return partes[0], "Principal"
        return "Pasajero", "Principal"

    def _asegurar_pasajero_principal(self):
        pasajero_model = self.env["incas.pasajero"].sudo()
        for record in self:
            if record.pasajero_ids:
                continue
            nombre_base = record.nombre or record.partner_id.name or "Pasajero principal"
            nombres, apellidos = self._separar_nombre_pasajero(nombre_base)
            pasajero_model.create(
                {
                    "reserva_id": record.id,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "tipo_documento": record.tipo_documento,
                    "numero_documento": record.numero_documento,
                    "nacionalidad": record.nacionalidad,
                    "email": record.email or record.partner_id.email,
                    "telefono": record.telefono or record.partner_id.phone,
                }
            )

    @api.depends("pasajero_ids", "pasajero_ids.estado_documental")
    def _compute_estado_documental(self):
        for record in self:
            pasajeros = record.pasajero_ids
            pendientes = pasajeros.filtered(lambda pasajero: pasajero.estado_documental != "completo")
            record.pasajeros_documentos_pendientes = len(pendientes)
            if not pasajeros:
                record.estado_documental = "sin_pasajeros"
            elif len(pendientes) == len(pasajeros):
                record.estado_documental = "pendiente"
            elif pendientes:
                record.estado_documental = "parcial"
            else:
                record.estado_documental = "completo"

    @api.depends("servicio_id", "tipo_servicio")
    def _compute_vehiculo_disponible_ids(self):
        for record in self:
            if record.servicio_id and record.tipo_servicio == "transporte":
                record.vehiculo_disponible_ids = record.servicio_id.obtener_vehiculos_transporte()
            else:
                record.vehiculo_disponible_ids = self.env["incas.catalogo.vehiculo"]

    @api.depends("fecha_check_in", "fecha_check_out")
    def _compute_cantidad_noches(self):
        for record in self:
            if record.fecha_check_in and record.fecha_check_out and record.fecha_check_out > record.fecha_check_in:
                record.cantidad_noches = (record.fecha_check_out - record.fecha_check_in).days
            else:
                record.cantidad_noches = 0

    @api.depends("cantidad_noches", "cantidad_habitaciones", "hotel_precio_noche_usd", "hotel_linea_ids.monto_hotel_usd", "hotel_linea_ids.monto_hotel")
    def _compute_monto_hotel(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if record.hotel_linea_ids:
                record.monto_hotel_usd = sum(record.hotel_linea_ids.mapped("monto_hotel_usd"))
                record.monto_hotel = sum(record.hotel_linea_ids.mapped("monto_hotel"))
            else:
                record.monto_hotel_usd = (record.cantidad_habitaciones or 0) * (record.cantidad_noches or 0) * (record.hotel_precio_noche_usd or 0)
                record.monto_hotel = record._convertir_desde_usd(record.monto_hotel_usd, record.moneda, rates)

    @api.depends("cantidad_extra", "extra_precio_unitario_usd", "extra_linea_ids.monto_extra_usd", "extra_linea_ids.monto_extra")
    def _compute_monto_extra(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if record.extra_linea_ids:
                record.monto_extra_usd = sum(record.extra_linea_ids.mapped("monto_extra_usd"))
                record.monto_extra = sum(record.extra_linea_ids.mapped("monto_extra"))
            else:
                record.monto_extra_usd = (record.cantidad_extra or 0) * (record.extra_precio_unitario_usd or 0)
                record.monto_extra = record._convertir_desde_usd(record.monto_extra_usd, record.moneda, rates)

    @api.depends(
        "cantidad_adultos",
        "cantidad_ninos",
        "precio_adulto",
        "precio_nino",
        "descuento",
        "paquete_linea_ids.precio_adulto_neto",
        "paquete_linea_ids.precio_nino_neto",
    )
    def _compute_precio_grupal(self):
        for record in self:
            if record.paquete_linea_ids:
                record.precio_grupal = sum(
                    ((record.cantidad_adultos or 0) * (linea.precio_adulto_neto or 0))
                    + ((record.cantidad_ninos or 0) * (linea.precio_nino_neto or 0))
                    for linea in record.paquete_linea_ids
                )
                continue
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.precio_grupal = subtotal - descuento_monto

    @api.depends("cantidad_adultos", "cantidad_ninos", "precio_adulto", "precio_nino", "descuento", "monto_hotel", "monto_extra")
    def _compute_monto_total(self):
        for record in self:
            subtotal = ((record.cantidad_adultos or 0) * (record.precio_adulto or 0)) + ((record.cantidad_ninos or 0) * (record.precio_nino or 0))
            descuento_monto = subtotal * ((record.descuento or 0) / 100)
            record.monto_total = (subtotal - descuento_monto) + (record.monto_hotel or 0) + (record.monto_extra or 0)

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

    @api.depends("cambio_ids")
    def _compute_cambio_count(self):
        for record in self:
            record.cambio_count = len(record.cambio_ids)

    @api.depends("pago_ids.estado", "pago_ids.monto_reserva")
    def _compute_monto_pagado(self):
        for record in self:
            record.monto_pagado = sum(record.pago_ids.filtered(lambda pago: pago.estado == "pagado").mapped("monto_reserva"))

    @api.depends("estado_reserva", "pago_ids.estado", "pago_ids.monto_reserva", "precio_tour", "monto_total")
    def _compute_estado_pago(self):
        for record in self:
            if record.estado_reserva == "cancelado":
                record.estado_pago = "cancelado"
                continue
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

    def _get_resumen_servicio(self):
        self.ensure_one()
        if not self.paquete_linea_ids:
            return {
                "tipo_servicio": self.tipo_servicio or "paquete",
                "tipo_tour": self.tipo_tour,
                "estilo_transporte_id": self.estilo_transporte_id,
                "servicio_id": self.servicio_id,
                "servicio_nombre": self.servicio_nombre,
                "precio_adulto_usd": self.precio_adulto_usd or 0,
                "precio_nino_usd": self.precio_nino_usd or 0,
                "precio_adulto": self.precio_adulto or 0,
                "precio_nino": self.precio_nino or 0,
                "descuento": self.descuento or 0,
            }
        precio_adulto_usd = sum(self.paquete_linea_ids.mapped("precio_adulto_neto_usd"))
        precio_nino_usd = sum(self.paquete_linea_ids.mapped("precio_nino_neto_usd"))
        precio_adulto = sum(self.paquete_linea_ids.mapped("precio_adulto_neto"))
        precio_nino = sum(self.paquete_linea_ids.mapped("precio_nino_neto"))
        if len(self.paquete_linea_ids) == 1:
            linea = self.paquete_linea_ids[0]
            return {
                "tipo_servicio": linea.tipo_servicio,
                "tipo_tour": linea.tipo_tour,
                "estilo_transporte_id": linea.estilo_transporte_id,
                "servicio_id": linea.servicio_id,
                "servicio_nombre": linea.nombre,
                "precio_adulto_usd": precio_adulto_usd,
                "precio_nino_usd": precio_nino_usd,
                "precio_adulto": precio_adulto,
                "precio_nino": precio_nino,
                "descuento": linea.descuento,
            }
        return {
            "tipo_servicio": "paquete",
            "tipo_tour": False,
            "estilo_transporte_id": self.env["incas.estilo.transporte"],
            "servicio_id": self.env["incas.servicio.catalogo"],
            "servicio_nombre": "Paquete personalizado",
            "precio_adulto_usd": precio_adulto_usd,
            "precio_nino_usd": precio_nino_usd,
            "precio_adulto": precio_adulto,
            "precio_nino": precio_nino,
            "descuento": 0,
        }

    def _aplicar_resumen_paquete(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            vals = {}
            if not record.paquete_linea_ids:
                if record.tipo_servicio == "paquete":
                    vals = {
                        "tipo_servicio": "paquete",
                        "tipo_tour": False,
                        "estilo_transporte_id": False,
                        "servicio_id": False,
                        "servicio_nombre": False,
                        "precio_adulto_usd": 0,
                        "precio_nino_usd": 0,
                        "precio_adulto": 0,
                        "precio_nino": 0,
                        "descuento": 0,
                    }
                    if record._origin.id:
                        super(IncasReserva, record.with_context(skip_resumen_paquete_sync=True)).write(vals)
                    else:
                        for field_name, value in vals.items():
                            record[field_name] = value
                continue
            resumen = record._get_resumen_servicio()
            vals = {
                "tipo_servicio": resumen["tipo_servicio"],
                "tipo_tour": resumen["tipo_tour"],
                "estilo_transporte_id": resumen["estilo_transporte_id"].id if resumen["estilo_transporte_id"] else False,
                "servicio_id": resumen["servicio_id"].id if resumen["servicio_id"] else False,
                "servicio_nombre": resumen["servicio_nombre"],
                "precio_adulto_usd": resumen["precio_adulto_usd"],
                "precio_nino_usd": resumen["precio_nino_usd"],
                "precio_adulto": record._convertir_desde_usd(resumen["precio_adulto_usd"], record.moneda, rates),
                "precio_nino": record._convertir_desde_usd(resumen["precio_nino_usd"], record.moneda, rates),
                "descuento": resumen["descuento"],
            }
            if record._origin.id:
                super(IncasReserva, record.with_context(skip_resumen_paquete_sync=True)).write(vals)
            else:
                for field_name, value in vals.items():
                    record[field_name] = value

    def _actualizar_estado_comercial_desde_pagos(self):
        for record in self:
            if record.estado_reserva == "cancelado":
                if record._origin.id:
                    super(IncasReserva, record.with_context(skip_estado_comercial_sync=True)).write({"estado_comercial": "cancelada"})
                else:
                    record.estado_comercial = "cancelada"
                continue
            if record.monto_pagado > 0 or record.pago_ids.filtered(lambda pago: pago.estado == "pagado"):
                if record.estado_comercial != "cancelada":
                    if record._origin.id:
                        super(IncasReserva, record.with_context(skip_estado_comercial_sync=True)).write({"estado_comercial": "confirmada"})
                    else:
                        record.estado_comercial = "confirmada"

    def _aplicar_moneda_desde_base(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            record.precio_adulto = record._convertir_desde_usd(record.precio_adulto_usd or 0, record.moneda, rates)
            record.precio_nino = record._convertir_desde_usd(record.precio_nino_usd or 0, record.moneda, rates)
            record.hotel_precio_noche = record._convertir_desde_usd(record.hotel_precio_noche_usd or 0, record.moneda, rates)
            record.extra_precio_unitario = record._convertir_desde_usd(record.extra_precio_unitario_usd or 0, record.moneda, rates)

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

    # Replica los datos del hotel desde la cotización para mantener el total consistente.
    def _aplicar_tarifa_hotel(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if not record.hotel_tarifa_id:
                record.hotel_nombre = record.hotel_id.name or False
                record.hotel_precio_noche_usd = 0
                record.hotel_precio_noche = 0
                record.hotel_descuento = 0
                continue
            record.hotel_id = record.hotel_tarifa_id.hotel_id
            record.hotel_nombre = record.hotel_tarifa_id.hotel_id.name
            record.hotel_precio_noche_usd = record.hotel_tarifa_id.obtener_precio_noche_neto_usd(record.hotel_tipo_tarifario)
            record.hotel_precio_noche = record._convertir_desde_usd(record.hotel_precio_noche_usd, record.moneda, rates)
            record.hotel_descuento = record.hotel_tarifa_id.descuento or 0

    def _aplicar_tarifa_extra(self):
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        for record in self:
            if not record.extra_tarifa_id:
                record.extra_nombre = record.extra_id.name or False
                record.extra_unidad = False
                record.extra_precio_unitario_usd = 0
                record.extra_precio_unitario = 0
                record.extra_descuento = 0
                continue
            record.extra_id = record.extra_tarifa_id.extra_id
            record.extra_nombre = record.extra_tarifa_id.extra_id.name
            record.extra_unidad = record.extra_tarifa_id.unidad
            record.extra_precio_unitario_usd = record.extra_tarifa_id.obtener_precio_unitario_neto_usd()
            record.extra_precio_unitario = record._convertir_desde_usd(record.extra_precio_unitario_usd, record.moneda, rates)
            record.extra_descuento = record.extra_tarifa_id.descuento or 0

    @api.model
    def _normalizar_fecha_web(self, valor):
        if not valor:
            return False
        texto_fecha = str(valor)
        return texto_fecha[:10]

    @api.model
    def _buscar_servicio_web(self, reserva_data):
        servicio_model = self.env["incas.servicio.catalogo"].sudo()
        transporte_model = self.env["incas.catalogo.transporte"].sudo()
        tour_web_model = self.env["incas.tour"].sudo()
        service_id = reserva_data.get("serviceId") or reserva_data.get("tourServiceId")
        tour_slug = (reserva_data.get("tourSlug") or reserva_data.get("tour_slug") or "").strip()
        nombre_servicio = (reserva_data.get("tourNombre") or "").strip()
        transporte_slug = (reserva_data.get("transporteSlug") or "").strip()
        for intento in range(2):
            servicio = False
            if service_id:
                servicio = servicio_model.search([("id", "=", int(service_id))], limit=1)
            elif tour_slug:
                tour_web = tour_web_model.search([("slug", "=", tour_slug)], limit=1)
                servicio = tour_web.servicio_id if tour_web else False
            elif transporte_slug:
                transporte = transporte_model.search([("slug", "=", transporte_slug)], limit=1)
                servicio = transporte.servicio_id if transporte else False
            elif nombre_servicio:
                servicio = servicio_model.search([("tipo_servicio", "=", "transporte"), ("name", "=", nombre_servicio)], limit=1)
            if servicio or intento == 1:
                return servicio
        return False

    @api.model
    def _buscar_vehiculo_web(self, servicio, reserva_data):
        nombre = reserva_data.get("vehiculo_seleccionado")
        if not servicio or servicio.tipo_servicio != "transporte":
            return self.env["incas.catalogo.vehiculo"]
        return servicio.obtener_vehiculo_transporte(nombre=nombre, usar_default=not nombre)

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
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        horario = self._buscar_horario_web(servicio, reserva_data)
        tarifa = servicio.obtener_tarifa_vehiculo_transporte(vehiculo) if servicio.tipo_servicio == "transporte" else {
            "precio_adulto": servicio.precio_adulto or 0,
            "precio_nino": servicio.precio_nino or 0,
            "descuento": servicio.descuento or 0,
        }
        descuento = float(reserva_data.get("descuento") or reserva_data.get("descuento_usd") or tarifa["descuento"] or 0)
        precio_adulto = self._convertir_desde_usd(tarifa["precio_adulto"] or 0, moneda, rates)
        precio_nino = self._convertir_desde_usd(tarifa["precio_nino"] or 0, moneda, rates)
        valores = {
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
            "vehiculo_seleccionado": vehiculo.nombre if vehiculo else reserva_data.get("vehiculo_seleccionado"),
            "idioma": reserva_data.get("idioma") or "es",
            "canal_venta": "web",
            "servicio_id": servicio.id,
            "tipo_servicio": servicio.tipo_servicio,
            "tipo_tour": servicio.tipo_tour,
            "estilo_transporte_id": servicio.estilo_transporte_id.id,
            "servicio_nombre": servicio.name,
            "cantidad_adultos": int(reserva_data.get("cantidad_adultos") or 1),
            "cantidad_ninos": int(reserva_data.get("cantidad_ninos") or 0),
            "moneda": moneda,
            "precio_adulto_usd": tarifa["precio_adulto"] or 0,
            "precio_nino_usd": tarifa["precio_nino"] or 0,
            "precio_adulto": precio_adulto,
            "precio_nino": precio_nino,
            "descuento": descuento,
            "precio_adulto_web": float(reserva_data.get("precio_adulto_web") or 0),
            "precio_nino_web": float(reserva_data.get("precio_nino_web") or 0),
            "origen_web": True,
            "observaciones": reserva_data.get("notas"),
            "estado_comercial": "cotizada",
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
                        "fecha": fecha_inicio or self._normalizar_fecha_web(reserva_data.get("fecha_viaje")),
                    },
                )
            ],
        }
        return valores

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
        self._actualizar_estado_comercial_desde_pagos()

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

    @api.model
    def _obtener_partner_destinatario(self, email, nombre):
        email = (email or "").strip()
        if not email:
            return self.env["res.partner"]
        partner_model = self.env["res.partner"].sudo()
        partner = partner_model.search([("email", "=", email)], limit=1)
        if partner:
            valores = {}
            if nombre and partner.name != nombre:
                valores["name"] = nombre
            if partner.email != email:
                valores["email"] = email
            if valores:
                partner.write(valores)
            return partner
        return partner_model.create(
            {
                "name": nombre or email,
                "email": email,
            }
        )

    def _obtener_remitente_reserva(self):
        self.ensure_one()
        remitente = (
            os.getenv("RESEND_FROM_EMAIL")
            or self.env["ir.config_parameter"].sudo().get_param("mail.default.from")
            or self.env.user.email
            or self.env.company.email
            or self.env.user.partner_id.email
            or ""
        ).strip()
        return remitente or False

    def _resolver_destinatario_cliente(self):
        self.ensure_one()
        email_cliente = (self.email or self.partner_id.email or "").strip()
        if not email_cliente:
            return self.env["res.partner"], False
        partner_cliente = self.partner_id
        if partner_cliente.email != email_cliente:
            partner_cliente = self._obtener_partner_destinatario(
                email_cliente,
                self.nombre or self.partner_id.display_name,
            )
        return partner_cliente, email_cliente

    def _enviar_correo_odoo(self, destinatarios, subject, body_html, pdf_bytes, partners=False, suscribir=False):
        self.ensure_one()
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]
        emails = []
        for email in destinatarios or []:
            email = (email or "").strip()
            if email and email.lower() not in [item.lower() for item in emails]:
                emails.append(email)
        if not partners:
            partners = self.env["res.partner"]
            for email in emails:
                partners |= self._obtener_partner_destinatario(email, email)
        if not partners:
            return
        remitente = self._obtener_remitente_reserva()
        reply_to = self._obtener_reply_to_reserva()
        _logger.info(
            "Reserva %s: enviando correo a=%s asunto=%s remitente=%s reply_to=%s",
            self.id,
            emails,
            subject,
            remitente,
            reply_to,
        )
        self.with_context(mail_notify_force_send=True, mail_post_autofollow=False).message_post(
            body=Markup(body_html),
            subject=subject,
            partner_ids=partners.ids,
            attachments=[(f"comprobante-{self.ticket}.pdf", pdf_bytes)],
            email_from=remitente,
            reply_to=reply_to,
            message_type="email",
            subtype_xmlid="mail.mt_comment",
        )
        if suscribir and partners:
            self.message_subscribe(partner_ids=partners.ids)

    def _obtener_reply_to_reserva(self):
        self.ensure_one()
        return self._obtener_remitente_reserva()

    def _enviar_correos_reserva(self):
        notify_email = os.getenv("RESEND_NOTIFY_EMAIL", "")
        for record in self:
            pdf = generar_pdf_desde_html(render_reserva_html(record))
            html = html_correo_reserva(record, "Confirmación de reserva", f"Hola {record.nombre or record.partner_id.display_name}, tu reserva fue registrada correctamente. Responde a este correo para continuar la conversación sobre esta reserva.")
            partner_cliente, email_cliente = record._resolver_destinatario_cliente()
            destinatarios = []
            partners = self.env["res.partner"]
            remitente = record._obtener_remitente_reserva()
            if remitente:
                partner_remitente = record._obtener_partner_destinatario(remitente, "Reservas Inca's Paradise")
                destinatarios.append(remitente)
                partners |= partner_remitente
            if notify_email:
                partner_admin = record._obtener_partner_destinatario(notify_email, "Notificaciones reservas")
                destinatarios.append(notify_email)
                partners |= partner_admin
            if email_cliente:
                destinatarios.append(email_cliente)
                partners |= partner_cliente
            record._enviar_correo_odoo(
                destinatarios,
                f"INCA'S PARADISE - Reserva {record.ticket}",
                html,
                pdf,
                partners=partners,
                suscribir=True,
            )

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
        servicio_id = vals.get("servicio_id")
        if not servicio_id and vals.get("vehiculo_id") and len(self) == 1 and self.servicio_id and self.servicio_id.tipo_servicio == "transporte":
            servicio = self.servicio_id
            vehiculo = servicio.obtener_vehiculo_transporte(
                nombre=vals.get("vehiculo_seleccionado"),
                vehiculo_id=vals.get("vehiculo_id"),
            )
            if vehiculo and not vals.get("vehiculo_seleccionado"):
                vals["vehiculo_seleccionado"] = vehiculo.nombre
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
                vehiculo_actual=self.vehiculo_id if len(self) == 1 and self.servicio_id == servicio else False,
                usar_default=not vals.get("vehiculo_id")
                and not vals.get("vehiculo_seleccionado")
                and not (len(self) == 1 and self.servicio_id == servicio and self.vehiculo_id),
            )
            if vehiculo and not vals.get("vehiculo_id"):
                vals["vehiculo_id"] = vehiculo.id
            if vehiculo and not vals.get("vehiculo_seleccionado"):
                vals["vehiculo_seleccionado"] = vehiculo.nombre
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
            if record.tipo_servicio == "paquete":
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
            if record.tipo_servicio == "paquete":
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
                record.vehiculo_seleccionado = record.vehiculo_id.nombre if record.vehiculo_id else False
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
            record.vehiculo_seleccionado = record.vehiculo_id.nombre if record.vehiculo_id else False
            tarifa = record.servicio_id.obtener_tarifa_vehiculo_transporte(record.vehiculo_id)
            record.precio_adulto_usd = tarifa["precio_adulto"]
            record.precio_nino_usd = tarifa["precio_nino"]
            record.descuento = tarifa["descuento"]
            record._aplicar_moneda_desde_base()

    @api.model
    def default_get(self, fields_list):
        return super().default_get(fields_list)

    @api.onchange("moneda")
    def _onchange_moneda(self):
        self._aplicar_moneda_desde_base()
        self.paquete_linea_ids._actualizar_precios_desde_usd(self.moneda)
        self.hotel_linea_ids._actualizar_precio_desde_usd(self.moneda)
        self.extra_linea_ids._actualizar_precio_desde_usd(self.moneda)
        self._aplicar_resumen_paquete()

    @api.onchange("paquete_linea_ids", "paquete_linea_ids.nombre", "paquete_linea_ids.servicio_id")
    def _onchange_paquete_linea_ids(self):
        self._aplicar_resumen_paquete()

    @api.onchange("hotel_id")
    def _onchange_hotel_id(self):
        for record in self:
            if record.hotel_tarifa_id and record.hotel_tarifa_id.hotel_id != record.hotel_id:
                record.hotel_tarifa_id = False
            record.hotel_nombre = record.hotel_id.name or False
            if not record.hotel_id:
                record.hotel_tarifa_id = False
                record.hotel_precio_noche_usd = 0
                record.hotel_precio_noche = 0
                record.hotel_descuento = 0

    @api.onchange("hotel_tarifa_id")
    def _onchange_hotel_tarifa_id(self):
        self._aplicar_tarifa_hotel()
        for record in self:
            if record.hotel_tarifa_id:
                record.fecha_check_in = record.fecha_check_in or record.fecha_inicio or record.fecha_viaje or record.hotel_tarifa_id.fecha_desde
                record.fecha_check_out = record.fecha_check_out or record.fecha_fin or record.hotel_tarifa_id.fecha_hasta

    @api.onchange("hotel_tipo_tarifario")
    def _onchange_hotel_tipo_tarifario(self):
        self._aplicar_tarifa_hotel()

    @api.onchange("extra_id")
    def _onchange_extra_id(self):
        for record in self:
            if record.extra_tarifa_id and record.extra_tarifa_id.extra_id != record.extra_id:
                record.extra_tarifa_id = False
            record.extra_nombre = record.extra_id.name or False
            if not record.extra_id:
                record.extra_tarifa_id = False
                record.extra_unidad = False
                record.extra_precio_unitario_usd = 0
                record.extra_precio_unitario = 0
                record.extra_descuento = 0

    @api.onchange("extra_tarifa_id")
    def _onchange_extra_tarifa_id(self):
        self._aplicar_tarifa_extra()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("incas.reserva") or "Nuevo"
            if not vals.get("ticket"):
                vals["ticket"] = self._generar_ticket()
            if not vals.get("access_token"):
                vals["access_token"] = self._generar_access_token()
            vals.setdefault("tipo_servicio", "paquete")
            vals.setdefault("servicio_nombre", "Paquete personalizado")
            self._completar_datos_servicio(vals)
            self._completar_datos_hotel(vals)
            self._completar_datos_extra(vals)
        reservas = super().create(vals_list)
        reservas._aplicar_resumen_paquete()
        reservas._actualizar_estado_comercial_desde_pagos()
        reservas._asegurar_carpeta_documental()
        reservas._asegurar_pasajero_principal()
        return reservas

    def write(self, vals):
        if self.env.context.get("skip_resumen_paquete_sync") or self.env.context.get("skip_estado_comercial_sync"):
            return super().write(vals)
        self._completar_datos_servicio(vals)
        self._completar_datos_hotel(vals)
        self._completar_datos_extra(vals)
        result = super().write(vals)
        self._aplicar_resumen_paquete()
        if "moneda" in vals:
            self.paquete_linea_ids._actualizar_precios_desde_usd(vals["moneda"])
            self.hotel_linea_ids._actualizar_precio_desde_usd(vals["moneda"])
            self.extra_linea_ids._actualizar_precio_desde_usd(vals["moneda"])
        self._actualizar_estado_comercial_desde_pagos()
        if any(campo in vals for campo in ["name"]):
            self._asegurar_carpeta_documental()
        return result

    def _completar_datos_hotel(self, vals):
        hotel_id = vals.get("hotel_id") or (self.hotel_id.id if len(self) == 1 else False)
        hotel_tarifa_id = vals.get("hotel_tarifa_id") or (self.hotel_tarifa_id.id if len(self) == 1 else False)
        tipo_tarifario = vals.get("hotel_tipo_tarifario") or (self.hotel_tipo_tarifario if len(self) == 1 else "ip") or "ip"
        if not hotel_id and not hotel_tarifa_id:
            return vals
        tarifa = self.env["incas.hotel.tarifa"].browse(hotel_tarifa_id) if hotel_tarifa_id else self.env["incas.hotel.tarifa"]
        hotel = self.env["incas.hotel"].browse(hotel_id) if hotel_id else tarifa.hotel_id
        if tarifa and tarifa.exists():
            vals.setdefault("hotel_id", tarifa.hotel_id.id)
            vals["hotel_nombre"] = tarifa.hotel_id.name
            vals.setdefault("hotel_tipo_tarifario", tipo_tarifario)
            vals["hotel_precio_noche_usd"] = tarifa.obtener_precio_noche_neto_usd(tipo_tarifario)
            vals["hotel_descuento"] = tarifa.descuento or 0
            vals.setdefault("fecha_check_in", vals.get("fecha_inicio") or vals.get("fecha_viaje") or tarifa.fecha_desde)
            vals.setdefault("fecha_check_out", vals.get("fecha_fin") or tarifa.fecha_hasta)
        elif hotel and hotel.exists():
            vals["hotel_nombre"] = hotel.name
        moneda = vals.get("moneda") or (self.moneda if len(self) == 1 else "PEN") or "PEN"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vals["hotel_precio_noche"] = self._convertir_desde_usd(vals.get("hotel_precio_noche_usd") or 0, moneda, rates)
        return vals

    def _completar_datos_extra(self, vals):
        extra_id = vals.get("extra_id")
        extra_tarifa_id = vals.get("extra_tarifa_id")
        if not extra_id and not extra_tarifa_id:
            return vals
        tarifa = self.env["incas.extra.tarifa"].browse(extra_tarifa_id) if extra_tarifa_id else self.env["incas.extra.tarifa"]
        extra = self.env["incas.extra"].browse(extra_id) if extra_id else tarifa.extra_id
        if tarifa and tarifa.exists():
            vals.setdefault("extra_id", tarifa.extra_id.id)
            vals["extra_nombre"] = tarifa.extra_id.name
            vals["extra_unidad"] = tarifa.unidad
            vals["extra_precio_unitario_usd"] = tarifa.obtener_precio_unitario_neto_usd()
            vals["extra_descuento"] = tarifa.descuento or 0
        elif extra and extra.exists():
            vals["extra_nombre"] = extra.name
        moneda = vals.get("moneda") or (self.moneda if len(self) == 1 else "PEN") or "PEN"
        rates = self.env["incas.servicio.catalogo"]._get_currency_rates()
        vals["extra_precio_unitario"] = self._convertir_desde_usd(vals.get("extra_precio_unitario_usd") or 0, moneda, rates)
        return vals

    def action_print_pdf(self):
        self.ensure_one()
        idioma = self.idioma if self.idioma in ["es", "en", "pt"] else "es"
        return {
            "type": "ir.actions.act_window",
            "name": "Exportar voucher PDF",
            "res_model": "incas.reserva.pdf.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_reserva_id": self.id,
                "default_idioma": idioma,
            },
        }

    def action_print_package_pdf(self):
        self.ensure_one()
        if not self.paquete_linea_ids:
            raise UserError("Selecciona al menos un tour o un transporte en la pestaña Paquete.")
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/reserva/{self.id}/detalle-paquete-pdf",
            "target": "self",
        }

    def action_marcar_cotizada(self):
        self.write({"estado_comercial": "cotizada"})

    def action_marcar_pre_reserva(self):
        self.write({"estado_comercial": "pre_reserva"})

    def action_confirmar_comercial(self):
        self.write({"estado_comercial": "confirmada"})

    def action_cancelar_comercial(self):
        self.write({"estado_comercial": "cancelada"})

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

    def action_ver_cambios(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Solicitudes de cambio",
            "res_model": "incas.reserva.cambio",
            "view_mode": "list,form",
            "domain": [("reserva_id", "=", self.id)],
            "context": {"default_reserva_id": self.id},
            "target": "current",
        }

    def action_solicitar_cambio(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nueva solicitud de cambio",
            "res_model": "incas.reserva.cambio",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_reserva_id": self.id,
                "default_motivo": "",
                "default_tipo_cambio": "reprogramacion",
            },
        }
