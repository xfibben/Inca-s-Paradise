import base64
import json
import os
from html import escape
from subprocess import run
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from odoo import fields


def texto(valor):
    if valor in (None, False):
        return "-"
    limpio = str(valor).strip()
    return limpio or "-"


def numero(valor):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def moneda_label(moneda):
    if moneda == "PEN":
        return "S/ "
    if moneda == "EUR":
        return "EUR "
    return "$ "


def monto(moneda, valor):
    return f"{moneda_label(moneda)}{numero(valor):.2f}"


def fecha(valor):
    if not valor:
        return "-"
    if isinstance(valor, str):
        return valor
    return fields.Date.to_string(valor)


def telefono_partner(partner):
    return getattr(partner, "phone", False) or getattr(partner, "mobile", False) or "-"


def fila(label, value):
    return f"""
    <tr>
      <td class="label">{escape(texto(label))}</td>
      <td>{escape(texto(value))}</td>
    </tr>
    """


def bloque(titulo, filas):
    return f"""
    <div class="section">
      <div class="section-title">{escape(titulo)}</div>
      <table>
        {''.join(filas)}
      </table>
    </div>
    """


def nombre_servicio_label(tipo_servicio):
    return "Nombre del tour" if tipo_servicio == "tour" else "Nombre del transporte"


def tipo_servicio_titulo(tipo_servicio):
    return "Tour" if tipo_servicio == "tour" else "Transporte"


def detalle_tipo_servicio(record):
    if record.tipo_servicio == "tour":
        if record.tipo_tour == "small_trip":
            return "Small Trip"
        if record.tipo_tour == "package":
            return "Package"
        return "Tour"
    return record.estilo_transporte_id.display_name


def bloque_pagos_reserva(reserva):
    filas = [
        fila("Moneda", reserva.moneda),
        fila("Descuento", f"{numero(reserva.descuento):.2f}%"),
        fila("Precio total del servicio", monto(reserva.moneda, reserva.precio_tour)),
        fila("Adelanto web", monto(reserva.moneda, reserva.monto_web)),
        fila("Precio web adultos", monto(reserva.moneda, reserva.precio_adulto_web)),
        fila("Precio web niños", monto(reserva.moneda, reserva.precio_nino_web)),
    ]

    pagos_agencia = reserva.pago_ids.sorted(lambda pago: (pago.fecha_pago or pago.create_date or fields.Datetime.now(), pago.id))
    if pagos_agencia:
        for indice, pago in enumerate(pagos_agencia, start=1):
            detalle = f"{texto(pago.proveedor)} / {texto(pago.metodo)} / {texto(pago.estado)}"
            if pago.fecha_pago:
                detalle = f"{detalle} / {texto(pago.fecha_pago)}"
            filas.append(
                fila(
                    f"Pago agencia {indice}",
                    f"{monto(reserva.moneda, pago.monto_reserva)} ({detalle})",
                )
            )
    else:
        filas.append(fila("Pagos en agencia", "No registrados"))

    filas.extend(
        [
            fila("Total pagado", monto(reserva.moneda, reserva.monto_pagado)),
            fila("Saldo pendiente", monto(reserva.moneda, reserva.saldo_pendiente)),
            fila("Monto final registrado", monto(reserva.moneda, reserva.monto_final)),
        ]
    )
    return bloque("RESUMEN DE PAGO", filas)


def html_base(titulo, codigo_label, codigo_valor, secciones):
    return f"""
    <html>
      <head>
        <meta charset="utf-8"/>
        <style>
          body {{
            font-family: Arial, sans-serif;
            color: #1f2937;
            font-size: 13px;
            margin: 24px;
          }}
          .title {{
            color: #1aa093;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
          }}
          .subtitle {{
            font-size: 15px;
            color: #374151;
            margin-bottom: 16px;
          }}
          .ticket-box {{
            border: 1px solid #1aa093;
            background: #f5f8f7;
            padding: 12px 16px;
            text-align: center;
            margin-bottom: 18px;
          }}
          .ticket-label {{
            font-size: 11px;
            color: #64748b;
            margin-bottom: 4px;
          }}
          .ticket-value {{
            font-size: 18px;
            font-weight: 700;
            color: #1aa093;
          }}
          .section {{
            margin-top: 14px;
            margin-bottom: 14px;
          }}
          .section-title {{
            background: #1aa093;
            color: #ffffff;
            padding: 8px 12px;
            font-weight: 700;
            font-size: 12px;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
          }}
          td {{
            border: 1px solid #d1d5db;
            padding: 8px 10px;
            vertical-align: top;
          }}
          .label {{
            background: #f8fafc;
            color: #475569;
            font-weight: 700;
            width: 38%;
          }}
        </style>
      </head>
      <body>
        <div class="title">Inca's Paradise</div>
        <div class="subtitle">{escape(titulo)}</div>
        <div class="ticket-box">
          <div class="ticket-label">{escape(codigo_label)}</div>
          <div class="ticket-value">{escape(texto(codigo_valor))}</div>
        </div>
        {''.join(secciones)}
      </body>
    </html>
    """


def render_reserva_html(reserva):
    tipo_servicio = tipo_servicio_titulo(reserva.tipo_servicio)
    return html_base(
        f"Comprobante de reserva de {tipo_servicio}",
        "TICKET",
        reserva.ticket,
        [
            bloque(
                "DATOS DEL PASAJERO",
                [
                    fila("Cliente principal", reserva.nombre or reserva.partner_id.display_name),
                    fila("Correo electrónico", reserva.email or reserva.partner_id.email),
                    fila("Teléfono", reserva.telefono or telefono_partner(reserva.partner_id)),
                    fila("Tipo de documento", (reserva.tipo_documento or "").upper()),
                    fila("Número de documento", reserva.numero_documento),
                    fila("Nacionalidad", reserva.nacionalidad),
                    fila("Idioma", reserva.idioma),
                    fila("Canal", reserva.canal_venta),
                ],
            ),
            bloque(
                f"DETALLES DEL {tipo_servicio.upper()}",
                [
                    fila("Tipo de servicio", detalle_tipo_servicio(reserva)),
                    fila(nombre_servicio_label(reserva.tipo_servicio), reserva.servicio_nombre),
                    fila("Vehículo seleccionado", reserva.vehiculo_seleccionado if reserva.tipo_servicio == "transporte" else "-"),
                    fila("Fecha de inicio", fecha(reserva.fecha_inicio or reserva.fecha_viaje)),
                    fila("Fecha de fin", fecha(reserva.fecha_fin or reserva.fecha_viaje)),
                    fila("Horario", reserva.turno),
                    fila("Adultos", reserva.cantidad_adultos),
                    fila("Niños", reserva.cantidad_ninos),
                    fila("Observaciones", reserva.observaciones),
                    fila("Estado de reserva", reserva.estado_reserva),
                    fila("Estado de pago", reserva.estado_pago),
                ],
            ),
            bloque_pagos_reserva(reserva),
        ],
    )


def render_cotizacion_html(cotizacion):
    tipo_servicio = tipo_servicio_titulo(cotizacion.tipo_servicio)
    return html_base(
        f"Comprobante de cotización de {tipo_servicio}",
        "CÓDIGO",
        cotizacion.name,
        [
            bloque(
                "DATOS DEL CLIENTE",
                [
                    fila("Cliente principal", cotizacion.partner_id.display_name),
                    fila("Correo electrónico", cotizacion.partner_id.email),
                    fila("Teléfono", telefono_partner(cotizacion.partner_id)),
                    fila("Idioma", cotizacion.idioma),
                    fila("Canal", cotizacion.canal_venta),
                ],
            ),
            bloque(
                "DETALLES DE LA COTIZACIÓN",
                [
                    fila("Tipo de servicio", detalle_tipo_servicio(cotizacion)),
                    fila(nombre_servicio_label(cotizacion.tipo_servicio), cotizacion.servicio_nombre),
                    fila("Fecha de cotización", fecha(cotizacion.fecha_cotizacion)),
                    fila("Fecha de viaje", fecha(cotizacion.fecha_viaje)),
                    fila("Adultos", cotizacion.cantidad_adultos),
                    fila("Niños", cotizacion.cantidad_ninos),
                    fila("Observaciones", cotizacion.observaciones),
                    fila("Estado", cotizacion.state),
                ],
            ),
            bloque(
                "RESUMEN DE PAGO",
                [
                    fila("Moneda", cotizacion.moneda),
                    fila("Descuento", f"{numero(cotizacion.descuento):.2f}%"),
                    fila("Precio adulto", monto(cotizacion.moneda, cotizacion.precio_adulto)),
                    fila("Precio niño", monto(cotizacion.moneda, cotizacion.precio_nino)),
                    fila("Monto total", monto(cotizacion.moneda, cotizacion.monto_total)),
                ],
            ),
        ],
    )


def generar_pdf_desde_html(html):
    proceso = run(
        ["/usr/local/bin/wkhtmltopdf", "--quiet", "-", "-"],
        input=html.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return proceso.stdout


def json_get(url, headers=None):
    request = Request(url, headers=headers or {}, method="GET")
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def json_post(url, payload, headers=None):
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def _paypal_base_url():
    return "https://api-m.paypal.com" if os.getenv("PAYPAL_MODE") == "live" else "https://api-m.sandbox.paypal.com"


def get_paypal_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    secret = os.getenv("PAYPAL_SECRET", "")
    if not client_id or not secret:
        raise ValueError("PAYPAL_CLIENT_ID y PAYPAL_SECRET son requeridos")
    credenciales = base64.b64encode(f"{client_id}:{secret}".encode("utf-8")).decode("ascii")
    request = Request(
        f"{_paypal_base_url()}/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {credenciales}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("access_token") or ""


def crear_orden_paypal(monto_pago, moneda):
    token = get_paypal_access_token()
    request = Request(
        f"{_paypal_base_url()}/v2/checkout/orders",
        data=json.dumps(
            {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": moneda,
                            "value": f"{numero(monto_pago):.2f}",
                        }
                    }
                ],
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {"orderID": payload.get("id")}


def capturar_orden_paypal(order_id):
    token = get_paypal_access_token()
    request = Request(
        f"{_paypal_base_url()}/v2/checkout/orders/{order_id}/capture",
        data=b"",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    capture = (((payload.get("purchase_units") or [{}])[0]).get("payments") or {}).get("captures") or [{}]
    capture_data = capture[0]
    return {
        "estado": "pagado" if capture_data.get("status") == "COMPLETED" else "fallido",
        "transaccion_id": capture_data.get("id") or "",
    }


def enviar_correo_resend(api_key, from_email, to_email, subject, html, pdf_bytes, ticket):
    if not api_key or not from_email or not to_email:
        return
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "attachments": [
            {
                "filename": f"comprobante-{ticket}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        ],
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "incas-paradise-odoo/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30):
            return True
    except HTTPError as error:
        raise ValueError(f"Resend respondió {error.code}: {error_http_text(error)}") from error


def html_correo_reserva(reserva, titulo, mensaje):
    detalle = render_reserva_html(reserva)
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background: #f3f7f6; padding: 24px;">
      <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4e2; border-radius: 12px; padding: 28px;">
        <div style="font-size: 12px; letter-spacing: 1.6px; font-weight: 700; color: #1aa093;">INCA'S PARADISE</div>
        <div style="font-size: 28px; line-height: 1.2; font-weight: 700; color: #1f2937; margin-top: 2px;">{escape(titulo)}</div>
        <p style="margin: 12px 0 24px 0; color: #374151;">{escape(mensaje)}</p>
        <div>{detalle}</div>
      </div>
    </div>
    """


def error_http_text(error):
    if isinstance(error, HTTPError):
        try:
            return error.read().decode("utf-8")
        except Exception:
            return str(error)
    return str(error)
