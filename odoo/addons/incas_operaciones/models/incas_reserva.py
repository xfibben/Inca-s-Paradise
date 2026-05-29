import json
from datetime import datetime, time, timedelta

from odoo import api, fields, models, tools


class IncasReserva(models.Model):
    _inherit = "incas.reserva"

    agenda_evento_ids = fields.One2many("incas.agenda.evento", "reserva_id", string="Eventos operativos")
    operacion_linea_ids = fields.One2many("incas.reserva.operacion.linea", "reserva_id", string="Matriz operativa")
    lugar_recojo = fields.Char(string="Lugar de recojo", tracking=True)
    operacion_agencia = fields.Char(string="Agencia", compute="_compute_operacion_resumen")
    operacion_rango_fechas = fields.Char(string="Rango", compute="_compute_operacion_resumen")
    operacion_resumen = fields.Char(string="Resumen operativo", compute="_compute_operacion_resumen")
    operacion_cronograma_html = fields.Html(string="Cronograma operativo", compute="_compute_operacion_resumen", sanitize=False)

    def _fecha_inicio_agenda(self):
        self.ensure_one()
        fecha = self.fecha_inicio or self.fecha_viaje or fields.Date.context_today(self)
        return fields.Datetime.to_string(datetime.combine(fecha, time(hour=9, minute=0)))

    def _fecha_fin_agenda(self):
        self.ensure_one()
        fecha = self.fecha_fin or self.fecha_inicio or self.fecha_viaje or fields.Date.context_today(self)
        return fields.Datetime.to_string(datetime.combine(fecha, time(hour=11, minute=0)))

    def _nombre_evento_reserva(self):
        self.ensure_one()
        codigo = self.ticket or self.name or f"RES-{self.id}"
        servicio = self.servicio_nombre or "Servicio"
        return f"{codigo} - {servicio}"

    def _valores_evento_reserva(self):
        self.ensure_one()
        estado = "cancelado" if self.estado_reserva == "cancelado" else "confirmado"
        return {
            "name": self._nombre_evento_reserva(),
            "tipo_evento": "reserva",
            "fecha_inicio": self._fecha_inicio_agenda(),
            "fecha_fin": self._fecha_fin_agenda(),
            "all_day": True,
            "partner_id": self.partner_id.id,
            "responsable_id": (self.responsable_id or self.env.user).id,
            "estado": estado,
            "reserva_id": self.id,
            "notas": self.observaciones or False,
        }

    def _sincronizar_evento_operativo(self):
        evento_model = self.env["incas.agenda.evento"].sudo()
        for reserva in self:
            evento = evento_model.search([("reserva_id", "=", reserva.id), ("tipo_evento", "=", "reserva")], limit=1)
            valores = reserva._valores_evento_reserva()
            if evento:
                evento.write(valores)
            else:
                evento_model.create(valores)

    @api.model_create_multi
    def create(self, vals_list):
        reservas = super().create(vals_list)
        reservas._sincronizar_evento_operativo()
        reservas._sincronizar_lineas_operacion()
        return reservas

    def write(self, vals):
        result = super().write(vals)
        campos_sync = {
            "ticket",
            "name",
            "servicio_nombre",
            "fecha_inicio",
            "fecha_fin",
            "fecha_viaje",
            "estado_reserva",
            "partner_id",
            "responsable_id",
            "observaciones",
        }
        if campos_sync.intersection(vals.keys()):
            self._sincronizar_evento_operativo()
        campos_operacion = {
            "fecha_inicio",
            "fecha_fin",
            "fecha_viaje",
            "fecha_reserva",
            "estado_reserva",
            "tipo_servicio",
            "tipo_tour",
            "servicio_nombre",
            "cantidad_adultos",
            "cantidad_ninos",
            "lugar_recojo",
            "hotel_linea_ids",
            "extra_linea_ids",
            "paquete_linea_ids",
            "monto_pagado",
            "saldo_pendiente",
        }
        if campos_operacion.intersection(vals.keys()):
            self._sincronizar_lineas_operacion()
        return result

    def _operacion_json_lista(self, valor):
        if not valor:
            return []
        try:
            data = json.loads(valor)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _operacion_texto_item(self, item):
        if isinstance(item, dict):
            for clave in ("title", "titulo", "label", "name", "text"):
                texto = item.get(clave)
                if texto:
                    return " ".join(tools.html2plaintext(str(texto)).split())
            for clave in ("description", "descripcion", "body"):
                texto = item.get(clave)
                if texto:
                    return " ".join(tools.html2plaintext(str(texto)).split())
        if isinstance(item, str):
            return " ".join(tools.html2plaintext(item).split())
        return ""

    def _operacion_fecha_inicio_base(self):
        self.ensure_one()
        return self.fecha_inicio or self.fecha_viaje or self.fecha_reserva or fields.Date.context_today(self)

    def _operacion_rango_reserva(self):
        self.ensure_one()
        inicio = self._operacion_fecha_inicio_base()
        fin = self.fecha_fin or inicio

        for linea in self.paquete_linea_ids:
            fecha_linea = linea.fecha or inicio
            dias_itinerario = len(self._operacion_json_lista(linea.itinerary_items_data))
            duracion = max(linea.duration_days or 0, dias_itinerario, 1)
            fin = max(fin, fecha_linea + timedelta(days=duracion - 1))

        for hotel in self.hotel_linea_ids:
            fecha_check_in = hotel.fecha_check_in or inicio
            noches = hotel.cantidad_noches or 1
            fin = max(fin, fecha_check_in + timedelta(days=max(noches - 1, 0)))

        return inicio, max(fin, inicio)

    def _operacion_agregar_bloque(self, agenda, fecha, tipo, texto):
        if not fecha or not texto:
            return
        agenda.setdefault(fecha, []).append(
            {
                "tipo": tipo,
                "texto": texto,
            }
        )

    def _operacion_agenda_por_fecha(self):
        self.ensure_one()
        inicio, _fin = self._operacion_rango_reserva()
        agenda = {}

        for linea in self.paquete_linea_ids.sorted(lambda item: (item.fecha or inicio, item.sequence, item.id)):
            fecha_linea = linea.fecha or inicio
            itinerario = self._operacion_json_lista(linea.itinerary_items_data)
            if itinerario:
                for indice, item in enumerate(itinerario, start=1):
                    fecha_item = fecha_linea + timedelta(days=indice - 1)
                    titulo = self._operacion_texto_item(item) or linea.nombre or "Paquete"
                    self._operacion_agregar_bloque(agenda, fecha_item, "paquete", f"Dia {indice}: {titulo}")
                continue

            duracion = max(linea.duration_days or 0, 1)
            for indice in range(duracion):
                fecha_item = fecha_linea + timedelta(days=indice)
                sufijo = f"Dia {indice + 1}" if duracion > 1 else "Servicio"
                self._operacion_agregar_bloque(agenda, fecha_item, "paquete", f"{sufijo}: {linea.nombre}")

        for hotel in self.hotel_linea_ids.sorted(lambda item: (item.fecha_check_in or inicio, item.sequence, item.id)):
            fecha_check_in = hotel.fecha_check_in or inicio
            noches = max(hotel.cantidad_noches or 1, 1)
            for indice in range(noches):
                fecha_hotel = fecha_check_in + timedelta(days=indice)
                self._operacion_agregar_bloque(agenda, fecha_hotel, "hotel", hotel.hotel_nombre or "Hotel")

        fecha_extra = inicio
        for extra in self.extra_linea_ids.sorted(lambda item: (item.sequence, item.id)):
            cantidad = extra.cantidad_extra or 1
            nombre = extra.extra_nombre or "Extra"
            self._operacion_agregar_bloque(agenda, fecha_extra, "extra", f"{nombre} x{cantidad}")

        return agenda

    def _operacion_horario_por_fecha(self):
        self.ensure_one()
        inicio = self._operacion_fecha_inicio_base()
        horarios = {}
        for linea in self.paquete_linea_ids.sorted(lambda item: (item.fecha or inicio, item.sequence, item.id)):
            fecha_linea = linea.fecha or inicio
            horario = linea.horario_id.name or linea.horario or False
            if horario and fecha_linea not in horarios:
                horarios[fecha_linea] = horario
        return horarios

    def _operacion_tipo_servicio_texto(self):
        self.ensure_one()
        if self.tipo_servicio == "transporte":
            return "Transporte"
        if self.tipo_tour == "small_trip":
            return "Small Trip"
        if self.tipo_tour == "package":
            return "Paquete"
        if self.tipo_servicio == "tour":
            return "Tour"
        return self.tipo_servicio or ""

    def _operacion_lineas_base(self):
        self.ensure_one()
        horarios = self._operacion_horario_por_fecha()
        empresa = self.env.company.name or "Inca's Paradise"
        lineas = []
        primera_linea = True

        for linea in self.paquete_linea_ids.sorted(lambda item: (item.fecha or self._operacion_fecha_inicio_base(), item.sequence, item.id)):
            fecha_linea = linea.fecha or self._operacion_fecha_inicio_base()
            itinerario = self._operacion_json_lista(linea.itinerary_items_data)
            duracion = max(linea.duration_days or 0, len(itinerario), 1)
            for indice in range(duracion):
                fecha_item = fecha_linea + timedelta(days=indice)
                texto = (
                    self._operacion_texto_item(itinerario[indice])
                    if indice < len(itinerario)
                    else linea.nombre
                ) or linea.nombre or self.servicio_nombre
                lineas.append(
                    {
                        "origen_tipo": "paquete",
                        "origen_clave": f"paquete-{linea.id}-dia-{indice + 1}",
                        "fecha": fecha_item,
                        "agencia": empresa,
                        "proveedor": empresa if self.tipo_servicio in {"tour", "transporte"} else "",
                        "estado_operacion": self.estado_reserva or "",
                        "nro_pasajeros": self.cantidad_pasajeros or 0,
                        "horario": horarios.get(fecha_item) or self.turno or "",
                        "lugar_recojo": self.lugar_recojo or "",
                        "servicio": texto,
                        "tipo_servicio": self._operacion_tipo_servicio_texto(),
                        "hotel_nombre": "",
                        "extras": "",
                        "saldo_pagar": 0.0,
                        "saldo_cobrar": (self.saldo_pendiente or 0.0) if primera_linea else 0.0,
                        "pagado": str(self.monto_pagado or 0.0) if primera_linea else "",
                    }
                )
                primera_linea = False

        for hotel in self.hotel_linea_ids.sorted(lambda item: (item.fecha_check_in or self._operacion_fecha_inicio_base(), item.sequence, item.id)):
            fecha_check_in = hotel.fecha_check_in or self._operacion_fecha_inicio_base()
            noches = max(hotel.cantidad_noches or 1, 1)
            for indice in range(noches):
                fecha_hotel = fecha_check_in + timedelta(days=indice)
                lineas.append(
                    {
                        "origen_tipo": "hotel",
                        "origen_clave": f"hotel-{hotel.id}-dia-{indice + 1}",
                        "fecha": fecha_hotel,
                        "agencia": empresa,
                        "proveedor": "",
                        "estado_operacion": "",
                        "nro_pasajeros": self.cantidad_pasajeros or 0,
                        "horario": "",
                        "lugar_recojo": "",
                        "servicio": "",
                        "tipo_servicio": "Hotel",
                        "hotel_nombre": hotel.hotel_nombre or "",
                        "extras": "",
                        "saldo_pagar": 0.0,
                        "saldo_cobrar": 0.0,
                        "pagado": "",
                    }
                )

        for extra in self.extra_linea_ids.sorted(lambda item: (item.sequence, item.id)):
            fecha_extra = self._operacion_fecha_inicio_base()
            lineas.append(
                {
                    "origen_tipo": "extra",
                    "origen_clave": f"extra-{extra.id}",
                    "fecha": fecha_extra,
                    "agencia": empresa,
                    "proveedor": "",
                    "estado_operacion": "",
                    "nro_pasajeros": self.cantidad_pasajeros or 0,
                    "horario": "",
                    "lugar_recojo": "",
                    "servicio": "",
                    "tipo_servicio": "Extra",
                    "hotel_nombre": "",
                    "extras": f"{extra.extra_nombre or 'Extra'} x{extra.cantidad_extra or 1}",
                    "saldo_pagar": 0.0,
                    "saldo_cobrar": 0.0,
                    "pagado": "",
                }
            )

        lineas.sort(key=lambda item: (item["fecha"], item["origen_tipo"] != "paquete", item["sequence"] if "sequence" in item else 0, item["origen_clave"]))
        return lineas

    def _sincronizar_lineas_operacion(self):
        linea_model = self.env["incas.reserva.operacion.linea"].sudo()
        for reserva in self:
            existentes = {
                (linea.origen_tipo, linea.origen_clave): linea
                for linea in reserva.operacion_linea_ids
                if linea.origen_tipo and linea.origen_clave
            }
            legadas_por_fecha = {}
            for linea in reserva.operacion_linea_ids.filtered(lambda item: not item.origen_tipo or not item.origen_clave):
                legadas_por_fecha.setdefault(linea.fecha, []).append(linea)

            usadas = self.env["incas.reserva.operacion.linea"]
            for indice, valores_base in enumerate(reserva._operacion_lineas_base(), start=1):
                clave = (valores_base["origen_tipo"], valores_base["origen_clave"])
                valores_sync = {
                    "sequence": indice * 10,
                    "origen_tipo": valores_base["origen_tipo"],
                    "origen_clave": valores_base["origen_clave"],
                    "fecha": valores_base["fecha"],
                    "agencia": valores_base["agencia"],
                    "nro_pasajeros": valores_base["nro_pasajeros"],
                    "horario": valores_base["horario"],
                    "lugar_recojo": valores_base["lugar_recojo"],
                    "servicio": valores_base["servicio"],
                    "tipo_servicio": valores_base["tipo_servicio"],
                    "hotel_nombre": valores_base["hotel_nombre"],
                    "extras": valores_base["extras"],
                    "saldo_cobrar": valores_base["saldo_cobrar"],
                    "pagado": valores_base["pagado"],
                }
                linea = existentes.get(clave)
                if not linea and legadas_por_fecha.get(valores_base["fecha"]):
                    linea = legadas_por_fecha[valores_base["fecha"]].pop(0)
                if linea:
                    update_vals = dict(valores_sync)
                    if not linea.proveedor:
                        update_vals["proveedor"] = valores_base["proveedor"]
                    if not linea.estado_operacion:
                        update_vals["estado_operacion"] = valores_base["estado_operacion"]
                    linea.write(update_vals)
                    usadas |= linea
                    continue
                create_vals = dict(valores_base)
                create_vals.update(
                    {
                        "sequence": indice * 10,
                        "reserva_id": reserva.id,
                    }
                )
                usadas |= linea_model.create(create_vals)

            (reserva.operacion_linea_ids - usadas).filtered(
                lambda item: item.origen_tipo and item.origen_clave and not any(
                    [item.guia, item.asistencia, item.observacion, item.seguimiento]
                )
            ).unlink()

    def _operacion_badge_html(self, tipo, texto):
        colores = {
            "paquete": ("#dbeafe", "#1d4ed8"),
            "hotel": ("#dcfce7", "#166534"),
            "extra": ("#fef3c7", "#92400e"),
        }
        fondo, color = colores.get(tipo, ("#e5e7eb", "#374151"))
        return (
            f"<div style='margin-bottom:6px; padding:6px 8px; border-radius:8px; "
            f"background:{fondo}; color:{color}; font-size:12px; line-height:1.35;'>"
            f"{tools.html_escape(texto)}</div>"
        )

    def _operacion_cronograma_html(self):
        self.ensure_one()
        inicio, fin = self._operacion_rango_reserva()
        agenda = self._operacion_agenda_por_fecha()
        dias = []
        fecha_cursor = inicio
        while fecha_cursor <= fin:
            dias.append(fecha_cursor)
            fecha_cursor += timedelta(days=1)

        encabezados = "".join(
            f"<th style='padding:10px; min-width:170px; border:1px solid #d1d5db; background:#0f766e; color:#fff; font-size:12px;'>"
            f"{tools.html_escape(fecha.strftime('%d/%m/%Y'))}</th>"
            for fecha in dias
        )
        celdas = "".join(
            "<td style='vertical-align:top; padding:8px; border:1px solid #d1d5db; background:#fff;'>"
            + "".join(
                self._operacion_badge_html(bloque["tipo"], bloque["texto"])
                for bloque in agenda.get(fecha, [])
            )
            + (
                ""
                if agenda.get(fecha)
                else "<div style='color:#9ca3af; font-size:12px;'>-</div>"
            )
            + "</td>"
            for fecha in dias
        )

        return f"""
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; table-layout:fixed;">
                <thead>
                    <tr>
                        {encabezados}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        {celdas}
                    </tr>
                </tbody>
            </table>
        </div>
        """

    @api.depends(
        "fecha_inicio",
        "fecha_fin",
        "fecha_viaje",
        "fecha_reserva",
        "paquete_linea_ids",
        "paquete_linea_ids.fecha",
        "paquete_linea_ids.nombre",
        "paquete_linea_ids.itinerary_items_data",
        "paquete_linea_ids.duration_days",
        "hotel_linea_ids",
        "hotel_linea_ids.fecha_check_in",
        "hotel_linea_ids.cantidad_noches",
        "hotel_linea_ids.hotel_nombre",
        "extra_linea_ids",
        "extra_linea_ids.extra_nombre",
        "extra_linea_ids.cantidad_extra",
    )
    def _compute_operacion_resumen(self):
        empresa = self.env.company.name or "Inca's Paradise"
        for record in self:
            inicio, fin = record._operacion_rango_reserva()
            dias = ((fin - inicio).days or 0) + 1
            record.operacion_agencia = empresa
            record.operacion_rango_fechas = f"{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
            record.operacion_resumen = f"{dias} dia(s) | {len(record.paquete_linea_ids)} paquete(s) | {len(record.hotel_linea_ids)} hotel(es) | {len(record.extra_linea_ids)} extra(s)"
            record.operacion_cronograma_html = record._operacion_cronograma_html()

    def action_regenerar_matriz_operativa(self):
        self._sincronizar_lineas_operacion()
        return True

    def action_print_pase_operativo(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/incas/operaciones/reserva/{self.id}/pase-pdf",
            "target": "self",
        }
