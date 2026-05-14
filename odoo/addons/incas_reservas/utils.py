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


def tiene_contenido(valor, ocultar_cero=False):
    if valor in (None, False):
        return False
    if isinstance(valor, str):
        return bool(valor.strip())
    if ocultar_cero:
        return numero(valor) != 0
    return True


def fila(label, value):
    return f"""
    <tr>
      <td class="label">{escape(texto(label))}</td>
      <td>{escape(texto(value))}</td>
    </tr>
    """


def fila_si(label, value, render=None, ocultar_cero=False):
    if not tiene_contenido(value, ocultar_cero=ocultar_cero):
        return ""
    return fila(label, render if render is not None else value)


def bloque(titulo, filas):
    filas_validas = [fila_html for fila_html in filas if fila_html]
    if not filas_validas:
        return ""
    return f"""
    <div class="section">
      <div class="section-title">{escape(titulo)}</div>
      <table>
        {"".join(filas_validas)}
      </table>
    </div>
    """


def nombre_servicio_label(tipo_servicio):
    if tipo_servicio == "tour":
        return "Nombre del tour"
    if tipo_servicio == "transporte":
        return "Nombre del transporte"
    return "Nombre del paquete"


def tipo_servicio_titulo(tipo_servicio):
    if tipo_servicio == "tour":
        return "Tour"
    if tipo_servicio == "transporte":
        return "Transporte"
    return "Paquete"


def detalle_tipo_servicio(record):
    if record.tipo_servicio == "paquete":
        return "Paquete"
    if record.tipo_servicio == "tour":
        if record.tipo_tour == "small_trip":
            return "Small Trip"
        if record.tipo_tour == "package":
            return "Package"
        return "Tour"
    return record.estilo_transporte_id.display_name


def tipo_documento_valor(reserva):
    if not reserva.tipo_documento:
        return ""
    if reserva.tipo_documento == "otro" and not reserva.numero_documento:
        return ""
    return (reserva.tipo_documento or "").upper()


def bloque_pagos_reserva(reserva):
    filas = [
        fila("Moneda", reserva.moneda),
        fila("Precio total del servicio", monto(reserva.moneda, reserva.precio_tour)),
        fila_si(
            "Descuento aplicado",
            reserva.descuento,
            render=f"{numero(reserva.descuento):.2f}%",
            ocultar_cero=True,
        ),
        fila("Total pagado", monto(reserva.moneda, reserva.monto_pagado)),
        fila_si(
            "Saldo pendiente",
            reserva.saldo_pendiente,
            render=monto(reserva.moneda, reserva.saldo_pendiente),
            ocultar_cero=True,
        ),
    ]

    pagos_agencia = reserva.pago_ids.sorted(
        lambda pago: (
            pago.fecha_pago or pago.create_date or fields.Datetime.now(),
            pago.id,
        )
    )
    if pagos_agencia:
        for indice, pago in enumerate(pagos_agencia, start=1):
            detalle = (
                f"{texto(pago.proveedor)} / {texto(pago.metodo)} / {texto(pago.estado)}"
            )
            if pago.fecha_pago:
                detalle = f"{detalle} / {texto(pago.fecha_pago)}"
            filas.append(
                fila(
                    f"Detalle de pago {indice}",
                    f"{monto(reserva.moneda, pago.monto_reserva)} ({detalle})",
                )
            )
    return bloque("RESUMEN DE PAGO", filas)


def fecha_corta(valor):
    if not valor:
        return "-"
    if isinstance(valor, str):
        partes = valor.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
        return valor
    return valor.strftime("%d/%m/%Y")


def _voucher_logo_data_uri():
    module_dir = os.path.dirname(__file__)
    logo_dir = os.path.join(
        os.path.dirname(module_dir),
        "static",
        "src",
        "img",
    )
    logo_path = ""
    for filename in ["certificado_imagen.png", "voucher_logo.svg", "voucher_logo.png", "voucher_logo.jpg", "voucher_logo.jpeg"]:
        candidate = os.path.join(logo_dir, filename)
        if os.path.exists(candidate):
            logo_path = candidate
            break
    if not os.path.exists(logo_path):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        logo_path = os.path.join(
            root_dir,
            "frontend",
            "public",
            "landing page images",
            "nuevo_logo.svg",
        )
    if not os.path.exists(logo_path):
        return ""
    with open(logo_path, "rb") as logo_file:
        data = base64.b64encode(logo_file.read()).decode("ascii")
    extension = os.path.splitext(logo_path)[1].lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
    }.get(extension, "image/svg+xml")
    return f"data:{mime};base64,{data}"


def _voucher_valor_linea(reserva, precio_adulto, precio_nino):
    return ((reserva.cantidad_adultos or 0) * (precio_adulto or 0)) + (
        (reserva.cantidad_ninos or 0) * (precio_nino or 0)
    )


def _metodo_pago_reserva(reserva):
    pago = reserva.pago_ids.sorted(
        lambda item: (
            item.fecha_pago or item.create_date or fields.Datetime.now(),
            item.id,
        ),
        reverse=True,
    )[:1]
    if not pago:
        return "-"
    metodo = pago.metodo or pago.proveedor
    if not metodo:
        return "-"
    return texto(metodo).replace("_", " ").title()


def _voucher_filas_servicio(reserva):
    lineas = reserva.paquete_linea_ids.sorted(lambda linea: (linea.sequence, linea.id))
    if not lineas:
        servicio = reserva.servicio_nombre
        if reserva.tipo_servicio == "transporte" and reserva.vehiculo_seleccionado:
            servicio = f"{servicio} ({reserva.vehiculo_seleccionado})"
        factor = 1 - ((reserva.descuento or 0) / 100)
        return [
            {
                "fecha": fecha_corta(reserva.fecha_inicio or reserva.fecha_viaje),
                "hora": reserva.turno,
                "servicio": servicio,
                "valor": _voucher_valor_linea(
                    reserva,
                    (reserva.precio_adulto or 0) * factor,
                    (reserva.precio_nino or 0) * factor,
                ),
            }
        ]
    filas = []
    for linea in lineas:
        servicio = linea.nombre
        vehiculo = _vehiculo_linea_paquete(linea)
        if linea.tipo_servicio == "transporte" and vehiculo:
            servicio = f"{servicio} ({vehiculo})"
        filas.append(
            {
                "fecha": fecha_corta(linea.fecha or reserva.fecha_inicio or reserva.fecha_viaje),
                "hora": linea.horario_id.name or linea.horario or reserva.turno,
                "servicio": servicio,
                "valor": _voucher_valor_linea(
                    reserva,
                    linea.precio_adulto_neto,
                    linea.precio_nino_neto,
                ),
            }
        )
    return filas


def _voucher_tabla_servicios(reserva):
    filas = _voucher_filas_servicio(reserva)
    pasajeros = (reserva.cantidad_adultos or 0) + (reserva.cantidad_ninos or 0)
    html_filas = []
    for indice, fila_servicio in enumerate(filas):
        pax = ""
        if indice == 0:
            pax = f'<td class="pax" rowspan="{len(filas)}">X{int(pasajeros or 1)}</td>'
        html_filas.append(
            f"""
            <tr>
              <td class="date-cell">{escape(texto(fila_servicio["fecha"]))}</td>
              {pax}
              <td class="hour-cell">{escape(texto(fila_servicio["hora"]))}</td>
              <td class="service-cell">{escape(texto(fila_servicio["servicio"]))}</td>
              <td class="value-cell">{escape(monto(reserva.moneda, fila_servicio["valor"]))}</td>
            </tr>
            """
        )
    return "".join(html_filas)


def _voucher_total_servicios(reserva):
    return sum(fila["valor"] for fila in _voucher_filas_servicio(reserva))


def _voucher_hoteles(reserva):
    lineas = reserva.hotel_linea_ids.sorted(lambda linea: (linea.sequence, linea.id))
    if lineas:
        hoteles = []
        for linea in lineas:
            hotel = texto(linea.hotel_nombre or linea.hotel_id.name)
            if linea.fecha_check_in and linea.fecha_check_out:
                hotel = f"{hotel} ({fecha_corta(linea.fecha_check_in)} - {fecha_corta(linea.fecha_check_out)})"
            hoteles.append(hotel)
        return " / ".join(hoteles)
    return texto(reserva.hotel_nombre or reserva.hotel_id.name)


def _voucher_textos(idioma):
    textos = {
        "es": {
            "phone": "Número de celular",
            "client": "Clientes(s):",
            "hotel": "Hotel:",
            "mobile": "Celular:",
            "issue_date": "Fecha de emisión:",
            "date": "FECHA",
            "pax": "Nro PAX",
            "hour": "HORA",
            "service": "SERVICIO",
            "total_val": "TOTAL VAL.",
            "payment_method": "MEDIO DE PAGO",
            "advance_payment": "PAGO ADELANTADO",
            "balance": "SALDO A PAGAR",
            "total": "TOTAL",
            "note": "NOTA: * El pago del saldo se debe realizar en efectivo en Dólares, los dólares deben estar en buenas condiciones casi nuevo. (sin roturas, dobleces muy marcados, ni gastados). También se puede realizar el pago en soles. De acuerdo al tipo de cambio",
        },
        "en": {
            "phone": "Mobile number",
            "client": "Client(s):",
            "hotel": "Hotel:",
            "mobile": "Phone:",
            "issue_date": "Issue date:",
            "date": "DATE",
            "pax": "PAX",
            "hour": "TIME",
            "service": "SERVICE",
            "total_val": "TOTAL VAL.",
            "payment_method": "PAYMENT METHOD",
            "advance_payment": "ADVANCE PAYMENT",
            "balance": "BALANCE DUE",
            "total": "TOTAL",
            "note": "NOTE: * The balance must be paid in cash in US dollars. Bills must be in very good condition, without tears, strong folds, or excessive wear. Payment can also be made in soles according to the exchange rate.",
        },
        "pt": {
            "phone": "Número de celular",
            "client": "Cliente(s):",
            "hotel": "Hotel:",
            "mobile": "Celular:",
            "issue_date": "Data de emissão:",
            "date": "DATA",
            "pax": "Nro PAX",
            "hour": "HORA",
            "service": "SERVIÇO",
            "total_val": "TOTAL VAL.",
            "payment_method": "MEIO DE PAGAMENTO",
            "advance_payment": "PAGAMENTO ANTECIPADO",
            "balance": "SALDO A PAGAR",
            "total": "TOTAL",
            "note": "NOTA: * O pagamento do saldo deve ser feito em dinheiro em Dólares. As notas devem estar em muito boas condições, sem rasgos, dobras muito marcadas ou desgaste. Também é possível pagar em soles, de acordo com a taxa de câmbio.",
        },
    }
    return textos.get(idioma, textos["es"])


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
          .text-block {{
            border: 1px solid #d1d5db;
            padding: 10px 12px;
            white-space: pre-wrap;
            line-height: 1.5;
          }}
          .label {{
            background: #f8fafc;
            color: #475569;
            font-weight: 700;
            width: 38%;
          }}
          .package-summary-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            background: #ffffff;
          }}
          .package-summary-table th,
          .package-summary-table td {{
            border: 1px solid #d1d5db;
            padding: 8px 10px;
            text-align: left;
            vertical-align: top;
          }}
          .package-summary-table thead th {{
            background: #1aa093;
            color: #ffffff;
            font-weight: 700;
          }}
          .package-summary-table tfoot td {{
            background: #f5f8f7;
            font-weight: 700;
          }}
          .package-summary-meta-table {{
            margin-bottom: 12px;
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
        {"".join(secciones)}
      </body>
    </html>
    """


def render_reserva_html(reserva, idioma=None):
    idioma = idioma if idioma in ["es", "en", "pt"] else "es"
    t = _voucher_textos(idioma)
    logo = _voucher_logo_data_uri()
    cliente = reserva.nombre or reserva.partner_id.display_name
    email = reserva.email or reserva.partner_id.email
    telefono = reserva.telefono or telefono_partner(reserva.partner_id)
    total = _voucher_total_servicios(reserva)
    pagado = reserva.monto_pagado
    saldo = total - pagado
    return f"""
    <html>
      <head>
        <meta charset="utf-8"/>
        <style>
          @page {{ size: A4 landscape; margin: 7mm; }}
          body {{
            margin: 0;
            color: #050505;
            font-family: "Times New Roman", serif;
            font-size: 17px;
          }}
          .voucher {{
            border: 3px solid #1aa093;
            border-radius: 7px;
            overflow: hidden;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
          }}
          td, th {{
            border: 1px solid #58bdb4;
            padding: 4px 7px;
            vertical-align: middle;
          }}
          .top td {{
            height: 118px;
            border-top: 0;
          }}
          .logo-cell {{
            width: 24%;
            text-align: center;
          }}
          .logo-cell img {{
            width: 84px;
            height: auto;
          }}
          .agency {{
            width: 38%;
            text-align: center;
            font-weight: 700;
            font-size: 23px;
            line-height: 1.14;
          }}
          .agency .address {{
            display: block;
            font-size: 18px;
          }}
          .agency .phone {{
            display: block;
            font-size: 17px;
            font-style: italic;
            font-weight: 400;
          }}
          .voucher-title {{
            width: 38%;
            text-align: center;
            font-weight: 700;
            font-size: 21px;
          }}
          .bar {{
            background: #1aa093;
            color: #ffffff;
            font-size: 22px;
            font-weight: 700;
            padding: 4px 0;
          }}
          .number {{
            display: block;
            margin-top: 8px;
            font-size: 19px;
          }}
          .meta td {{
            background: #fff4cb;
            height: 22px;
          }}
          .meta .label {{
            width: 24%;
            font-weight: 700;
          }}
          .meta .value {{
            width: 76%;
            font-weight: 700;
          }}
          .meta .email {{
            color: #1d73d4;
            text-decoration: underline;
          }}
          .service-head th {{
            background: #1aa093;
            color: #ffffff;
            font-size: 19px;
            font-weight: 700;
            text-align: center;
          }}
          .service-body td {{
            height: 36px;
            font-size: 18px;
          }}
          .date-cell {{
            width: 9%;
            text-align: center;
          }}
          .pax {{
            width: 6%;
            text-align: center;
            font-size: 21px;
            font-weight: 700;
          }}
          .hour-cell {{
            width: 8%;
            text-align: center;
          }}
          .service-cell {{
            width: 63%;
          }}
          .value-cell {{
            width: 14%;
          }}
          .payment td {{
            height: 32px;
            font-size: 18px;
            font-weight: 700;
          }}
          .payment .label {{
            background: #1aa093;
            color: #ffffff;
            text-align: center;
            font-size: 20px;
          }}
          .payment .amount {{
            text-align: center;
            font-size: 23px;
          }}
          .payment .balance {{
            color: #ff0000;
          }}
          .payment .total {{
            color: #001d55;
          }}
          .note {{
            border-top: 1px solid #58bdb4;
            padding: 7px 10px 10px;
            font-family: Arial, sans-serif;
            font-size: 20px;
            font-style: italic;
            line-height: 1.45;
            text-align: center;
          }}
        </style>
      </head>
      <body>
        <div class="voucher">
          <table class="top">
            <tr>
              <td class="logo-cell">{f'<img src="{logo}" alt="Inca Paradise"/>' if logo else ""}</td>
              <td class="agency">
                INCA'S PARADISE<br/>TRAVEL AGENCY
                <span class="address">Jirón Grau Nro. 460 Puno- Perú</span>
                <span class="phone">{escape(t["phone"])} +51-953556680</span>
              </td>
              <td class="voucher-title">
                RUC No: 20601022207
                <div class="bar">VOUCHER</div>
                <span class="number">No:{escape(texto(reserva.ticket or reserva.name))}</span>
              </td>
            </tr>
          </table>
          <table class="meta">
            <tr><td class="label">{escape(t["client"])}</td><td class="value">{escape(texto(cliente))}</td></tr>
            <tr><td class="label">{escape(t["hotel"])}</td><td>{escape(_voucher_hoteles(reserva))}</td></tr>
            <tr><td class="label">E-mail:</td><td class="email">{escape(texto(email))}</td></tr>
            <tr><td class="label">{escape(t["mobile"])}</td><td>{escape(texto(telefono))}</td></tr>
            <tr><td class="label">{escape(t["issue_date"])}</td><td>{escape(fecha_corta(reserva.fecha_reserva or fields.Date.context_today(reserva)))}</td></tr>
          </table>
          <table>
            <thead class="service-head">
              <tr>
                <th>{escape(t["date"])}</th>
                <th>{escape(t["pax"])}</th>
                <th>{escape(t["hour"])}</th>
                <th>{escape(t["service"])}</th>
                <th>{escape(t["total_val"])}</th>
              </tr>
            </thead>
            <tbody class="service-body">
              {_voucher_tabla_servicios(reserva)}
            </tbody>
          </table>
          <table class="payment">
            <tr>
              <td class="label" style="width:24%;">{escape(t["payment_method"])}</td>
              <td colspan="5">{escape(_metodo_pago_reserva(reserva))}</td>
            </tr>
            <tr>
              <td class="label">{escape(t["advance_payment"])}</td>
              <td class="amount" style="width:18%;">{escape(monto(reserva.moneda, pagado))}</td>
              <td class="label" style="width:18%;">{escape(t["balance"])}</td>
              <td class="amount balance" style="width:18%;">{escape(monto(reserva.moneda, saldo))}</td>
              <td class="label" style="width:10%;">{escape(t["total"])}</td>
              <td class="amount total" style="width:12%;">{escape(monto(reserva.moneda, total))}</td>
            </tr>
          </table>
          <div class="note">
            {escape(t["note"])}
          </div>
        </div>
      </body>
    </html>
    """


def _subtotal_linea_paquete(reserva, linea):
    return ((reserva.cantidad_adultos or 0) * (linea.precio_adulto_neto or 0)) + (
        (reserva.cantidad_ninos or 0) * (linea.precio_nino_neto or 0)
    )


def _tipo_linea_paquete(linea):
    if linea.tipo_servicio == "tour":
        if linea.tipo_tour == "small_trip":
            return "Small Trip"
        if linea.tipo_tour == "package":
            return "Package"
        return "Tour"
    return texto(linea.estilo_transporte_id.display_name)


def _vehiculo_record_linea_paquete(linea):
    if linea.tipo_servicio != "transporte":
        return linea.env["incas.catalogo.vehiculo"]
    if linea.vehiculo_id:
        return linea.vehiculo_id
    if linea.servicio_id:
        return linea.servicio_id.obtener_vehiculo_transporte()
    return linea.env["incas.catalogo.vehiculo"]


def _vehiculo_linea_paquete(linea):
    vehiculo = _vehiculo_record_linea_paquete(linea)
    return vehiculo.nombre if vehiculo else ""


def _tabla_lineas_paquete(reserva):
    lineas = reserva.paquete_linea_ids.sorted(
        lambda linea: (linea.sequence, linea.id)
    )
    if not lineas:
        return ""
    filas = []
    for indice, linea in enumerate(lineas, start=1):
        filas.append(
            f"""
            <tr>
              <td>{indice}</td>
              <td>{escape(texto(linea.nombre))}</td>
              <td>{escape(_tipo_linea_paquete(linea))}</td>
              <td>{escape(fecha(linea.fecha))}</td>
              <td>{escape(texto(_vehiculo_linea_paquete(linea)))}</td>
              <td>{escape(monto(reserva.moneda, linea.precio_adulto))}</td>
              <td>{escape(monto(reserva.moneda, linea.precio_nino))}</td>
              <td>{escape(f'{numero(linea.descuento):.2f}%' if numero(linea.descuento) else '-')}</td>
            </tr>
            """
        )
    return f"""
    <div class="section">
      <div class="section-title">LÍNEAS DEL PAQUETE</div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Servicio</th>
            <th>Tipo</th>
            <th>Fecha</th>
            <th>Vehículo</th>
            <th>Precio adulto</th>
            <th>Precio niño</th>
            <th>Descuento</th>
          </tr>
        </thead>
        <tbody>
          {''.join(filas)}
        </tbody>
      </table>
    </div>
    """


def _tabla_resumen_paquete(reserva):
    lineas = reserva.paquete_linea_ids.sorted(
        lambda linea: (linea.sequence, linea.id)
    )
    if not lineas:
        return ""
    filas = []
    total = 0
    for indice, linea in enumerate(lineas, start=1):
        subtotal = _subtotal_linea_paquete(reserva, linea)
        total += subtotal
        filas.append(
            f"""
            <tr>
              <td>{indice}</td>
              <td>{escape(texto(linea.nombre))}</td>
              <td>{escape(_tipo_linea_paquete(linea))}</td>
              <td>{escape(fecha(linea.fecha))}</td>
              <td>{escape(texto(_vehiculo_linea_paquete(linea)))}</td>
              <td>{escape(monto(reserva.moneda, linea.precio_adulto_neto))}</td>
              <td>{escape(monto(reserva.moneda, linea.precio_nino_neto))}</td>
              <td>{escape(monto(reserva.moneda, subtotal))}</td>
            </tr>
            """
        )
    return f"""
    <table class="package-summary-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Servicio</th>
          <th>Tipo</th>
          <th>Fecha</th>
          <th>Vehículo</th>
          <th>Adulto final</th>
          <th>Niño final</th>
          <th>Subtotal</th>
        </tr>
      </thead>
      <tbody>
        {''.join(filas)}
      </tbody>
      <tfoot>
        <tr>
          <td colspan="7">Monto total del paquete</td>
          <td>{escape(monto(reserva.moneda, total))}</td>
        </tr>
      </tfoot>
    </table>
    """


def _tabla_datos_resumen_paquete(reserva):
    return f"""
    <table class="package-summary-table package-summary-meta-table">
      <thead>
        <tr>
          <th colspan="4">Resumen del paquete</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="label">Código</td>
          <td>{escape(texto(reserva.name))}</td>
          <td class="label">Cliente</td>
          <td>{escape(texto(reserva.partner_id.display_name))}</td>
        </tr>
        <tr>
          <td class="label">Fecha de viaje</td>
          <td>{escape(fecha(reserva.fecha_viaje))}</td>
          <td class="label">Items del paquete</td>
          <td>{len(reserva.paquete_linea_ids)}</td>
        </tr>
        <tr>
          <td class="label">Moneda</td>
          <td>{escape(texto(reserva.moneda))}</td>
          <td class="label">Monto total</td>
          <td>{escape(monto(reserva.moneda, reserva.monto_total))}</td>
        </tr>
        <tr>
          <td class="label">Observaciones</td>
          <td colspan="3">{escape(texto(reserva.observaciones))}</td>
        </tr>
      </tbody>
    </table>
    """


def _json_lista(valor):
    if not valor:
        return []
    try:
        data = json.loads(valor)
        return data if isinstance(data, list) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _texto_json_lista(valor, claves):
    items = []
    for item in _json_lista(valor):
        if not isinstance(item, dict):
            continue
        for clave in claves:
            texto_item = str(item.get(clave) or "").strip()
            if texto_item:
                items.append(texto_item)
                break
    return ", ".join(items)


def _texto_json_item(item, claves):
    if not isinstance(item, dict):
        limpio = str(item or "").strip()
        return limpio
    for clave in claves:
        valor = item.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ""


def _texto_json_detallado(item, claves_principales, claves_secundarias=None):
    titulo = _texto_json_item(item, claves_principales)
    if not claves_secundarias:
        return titulo
    detalle = _texto_json_item(item, claves_secundarias)
    if titulo and detalle and detalle != titulo:
        return f"{titulo}: {detalle}"
    return titulo or detalle


def _detalle_catalogo_linea(linea):
    if linea.tipo_servicio == "tour":
        return linea.env["incas.catalogo.tour"].search(
            [("servicio_id", "=", linea.servicio_id.id)], limit=1
        )
    return linea.env["incas.catalogo.transporte"].search(
        [("servicio_id", "=", linea.servicio_id.id)], limit=1
    )


def _strapi_base_url(record):
    return (
        record.env["ir.config_parameter"].sudo().get_param("incas_reservas.strapi_url")
        or os.getenv("ODOO_STRAPI_CONECTION_URL")
        or "https://api.incasparadise.com"
    ).rstrip("/")


def _normalizar_url_imagen(record, url):
    if not url:
        return ""
    texto_url = str(url).strip()
    if not texto_url:
        return ""
    if texto_url.startswith("data:image/"):
        return texto_url
    if texto_url.startswith("http://") or texto_url.startswith("https://"):
        return texto_url
    if texto_url.startswith("/"):
        return f"{_strapi_base_url(record)}{texto_url}"
    return f"{_strapi_base_url(record)}/{texto_url.lstrip('/')}"


def _filtrar_urls_small(urls):
    urls_small = [url for url in urls if "/small_" in url]
    if urls_small:
        return urls_small
    return urls


def _recoger_urls_imagen(valor, acumulado):
    if not valor:
        return
    if isinstance(valor, str):
        limpio = valor.strip()
        if (
            limpio.startswith("http://")
            or limpio.startswith("https://")
            or limpio.startswith("/")
            or limpio.startswith("data:image/")
        ):
            acumulado.append(limpio)
        return
    if isinstance(valor, dict):
        for clave in ("url", "src", "imageUrl", "image_url"):
            url = valor.get(clave)
            if isinstance(url, str) and url.strip():
                acumulado.append(url.strip())
        for contenido in valor.values():
            if isinstance(contenido, (dict, list)):
                _recoger_urls_imagen(contenido, acumulado)
        return
    if isinstance(valor, list):
        for item in valor:
            _recoger_urls_imagen(item, acumulado)


def _extraer_urls_imagen(record, *valores):
    urls = []
    for valor in valores:
        if not valor:
            continue
        data = valor
        if isinstance(valor, str):
            try:
                data = json.loads(valor)
            except (TypeError, ValueError, json.JSONDecodeError):
                data = valor
        _recoger_urls_imagen(data, urls)
    urls_normalizadas = []
    vistos = set()
    for url in urls:
        normalizada = _normalizar_url_imagen(record, url)
        if not normalizada or normalizada in vistos:
            continue
        vistos.add(normalizada)
        urls_normalizadas.append(normalizada)
    return _filtrar_urls_small(urls_normalizadas)


def _extraer_imagenes_data_uri(record, *valores, max_imagenes=4):
    imagenes = []
    contenidos_vistos = set()
    for normalizada in _extraer_urls_imagen(record, *valores):
        if normalizada.startswith("data:image/"):
            if normalizada in contenidos_vistos:
                continue
            contenidos_vistos.add(normalizada)
            imagenes.append(normalizada)
            continue
        try:
            request = Request(
                normalizada, headers={"User-Agent": "Mozilla/5.0"}, method="GET"
            )
            with urlopen(request, timeout=20) as response:
                mime = response.headers.get_content_type() or "image/jpeg"
                contenido = base64.b64encode(response.read()).decode("ascii")
            data_uri = f"data:{mime};base64,{contenido}"
            if data_uri in contenidos_vistos:
                continue
            contenidos_vistos.add(data_uri)
            imagenes.append(data_uri)
        except (HTTPError, OSError, ValueError):
            continue
        if len(imagenes) >= max_imagenes:
            break
    return imagenes


def _render_lista_simple(items):
    items_validos = [item for item in items if item]
    if not items_validos:
        return ""
    return f"<ul class='editorial-list'>{''.join(f'<li>{escape(item)}</li>' for item in items_validos)}</ul>"


def _render_itinerario(record, valor):
    bloques = []
    for item in _json_lista(valor):
        if not isinstance(item, dict):
            continue
        titulo = _texto_json_item(item, ["title", "heading", "label", "name"])
        detalle = _texto_json_item(
            item, ["description", "content", "text", "body", "details"]
        )
        extra = _texto_json_item(item, ["highlight", "time", "duration", "subtitle"])
        optional = _texto_json_item(item, ["optional"])
        incluye = []
        for entrada in item.get("includes") or []:
            texto_incluye = _texto_json_item(
                entrada, ["text", "label", "title", "name"]
            )
            if texto_incluye:
                incluye.append(texto_incluye)
        partes = []
        if titulo:
            partes.append(f"<div class='timeline-title'>{escape(titulo)}</div>")
        if extra:
            partes.append(f"<div class='timeline-meta'>{escape(extra)}</div>")
        if detalle:
            partes.append(f"<div class='timeline-text'>{escape(detalle)}</div>")
        if incluye:
            partes.append(_render_lista_simple(incluye))
        if optional:
            partes.append(f"<div class='timeline-note'>{escape(optional)}</div>")
        if partes:
            bloques.append(f"<div class='timeline-item'>{''.join(partes)}</div>")
    return "".join(bloques)


def _render_galeria(record, *valores, max_imagenes=4, mostrar_urls=False):
    urls = _extraer_urls_imagen(record, *valores)
    imagenes = _extraer_imagenes_data_uri(record, *valores, max_imagenes=max_imagenes)
    if not imagenes:
        return ""
    fallback = ""
    if urls and mostrar_urls:
        fallback = (
            "<div class='image-url-fallback'>"
            "<div class='image-url-title'>URLs de imagen</div>"
            + "".join(
                f"<div class='image-url-item'>{escape(url)}</div>"
                for url in urls[:max_imagenes]
            )
            + "</div>"
        )
    return f"""
    <div class="editorial-gallery">
      {"".join(f'<div class="editorial-image"><img src="{imagen}" alt="Imagen del servicio"/></div>' for imagen in imagenes)}
      {fallback}
    </div>
    """


def _detalle_precio_linea(linea):
    descuento = f"{numero(linea.descuento):.2f}%" if numero(linea.descuento) else "-"
    mostrar_horario = tiene_contenido(getattr(linea, "horario", False))
    return f"""
    <div class="price-card">
      <div class="price-title">Resumen de fecha y precios</div>
      <table class="price-table">
        <thead>
          <tr>
            <th>Fecha</th>
            {"<th>Horario</th>" if mostrar_horario else ""}
            <th>Moneda</th>
            <th>Precio adulto</th>
            <th>Precio niño</th>
            <th>Descuento</th>
            <th>Adulto final</th>
            <th>Niño final</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{escape(fecha(linea.fecha))}</td>
            {f"<td>{escape(texto(linea.horario))}</td>" if mostrar_horario else ""}
            <td>{escape(texto(linea.moneda))}</td>
            <td>{escape(monto(linea.moneda, linea.precio_adulto))}</td>
            <td>{escape(monto(linea.moneda, linea.precio_nino))}</td>
            <td>{escape(descuento)}</td>
            <td>{escape(monto(linea.moneda, linea.precio_adulto_neto))}</td>
            <td>{escape(monto(linea.moneda, linea.precio_nino_neto))}</td>
          </tr>
        </tbody>
      </table>
    </div>
    """


def _seccion_editorial(titulo, contenido):
    if not contenido:
        return ""
    return f"""
    <section class="editorial-section">
      <h3>{escape(titulo)}</h3>
      {contenido}
    </section>
    """


def _parrafo_editorial(texto_largo):
    if not texto_largo:
        return ""
    return f"<p class='editorial-copy'>{escape(texto_largo)}</p>"


def _bloque_highlights_intro(pregunta, lead):
    partes = []
    if pregunta:
        partes.append(f"<div class='story-question'>{escape(pregunta)}</div>")
    if lead:
        partes.append(_parrafo_editorial(lead))
    if not partes:
        return ""
    return f"""
    <section class="editorial-section story-intro">
      {''.join(partes)}
    </section>
    """


def _bloque_tour_editorial(indice, linea, detalle):
    highlights = [
        _texto_json_detallado(
            item, ["title", "label", "name"], ["description", "text", "body"]
        )
        for item in _json_lista(
            linea.highlights_items_data or detalle.highlights_items_data
        )
    ]
    incluye = [
        _texto_json_detallado(item, ["text", "label", "title"], ["description", "body"])
        for item in _json_lista(
            linea.included_items_data or detalle.included_items_data
        )
    ]
    no_incluye = [
        _texto_json_detallado(item, ["text", "label", "title"], ["description", "body"])
        for item in _json_lista(
            linea.excluded_items_data or detalle.excluded_items_data
        )
    ]
    horarios = [
        _texto_json_detallado(
            item, ["title", "label", "time"], ["description", "text", "body"]
        )
        for item in _json_lista(
            linea.schedule_items_data or detalle.schedule_items_data
        )
    ]
    galeria = _render_galeria(
        linea,
        linea.featured_images_data or detalle.featured_images_data,
        max_imagenes=4,
        mostrar_urls=True,
    )
    itinerario = _render_itinerario(
        linea, linea.itinerary_items_data or detalle.itinerary_items_data
    )
    resumen = [
        f"<span class='story-kicker'>Tour {indice}</span>",
        f"<h2>{escape(texto(linea.nombre))}</h2>",
        f"<div class='story-meta'>{escape(texto(linea.tipo_tour or detalle.tipo_tour or 'Tour'))} · {escape(fecha(linea.fecha))}{f' · {escape(texto(linea.horario))}' if tiene_contenido(getattr(linea, 'horario', False)) else ''}</div>",
        _parrafo_editorial(linea.hero_description or detalle.hero_description),
    ]
    cuerpo = [
        _bloque_highlights_intro(
            linea.highlights_question or detalle.highlights_question,
            linea.highlights_lead or detalle.highlights_lead,
        ),
        _seccion_editorial(
            linea.highlights_title
            or detalle.highlights_title
            or "Lo mejor de la experiencia",
            _render_lista_simple(highlights)
            or _parrafo_editorial(linea.highlights_lead or detalle.highlights_lead),
        ),
        _seccion_editorial(
            linea.itinerary_title or detalle.itinerary_title or "Itinerario", itinerario
        ),
        _seccion_editorial(
            linea.schedule_title or detalle.schedule_title or "Horarios",
            _render_lista_simple(horarios),
        ),
        _seccion_editorial(
            linea.included_title or detalle.included_title or "Incluye",
            _render_lista_simple(incluye),
        ),
        _seccion_editorial(
            linea.excluded_title or detalle.excluded_title or "No incluye",
            _render_lista_simple(no_incluye),
        ),
    ]
    return f"""
    <article class="story-card">
      <div class="story-cover">
        {"".join([item for item in resumen if item])}
      </div>
      {galeria}
      <div class="story-body">
        {"".join([seccion for seccion in cuerpo if seccion])}
      </div>
      {_detalle_precio_linea(linea)}
    </article>
    """


def _bloque_transporte_editorial(indice, linea, detalle):
    incluye = [
        _texto_json_detallado(item, ["text", "label", "title"], ["description", "body"])
        for item in _json_lista(
            linea.included_items_data or detalle.included_items_data
        )
    ]
    no_incluye = [
        _texto_json_detallado(item, ["text", "label", "title"], ["description", "body"])
        for item in _json_lista(
            linea.excluded_items_data or detalle.excluded_items_data
        )
    ]
    tipos = [
        _texto_json_detallado(
            item, ["nombre", "title", "name"], ["description", "text", "body"]
        )
        for item in _json_lista(
            linea.tipos_transporte_data or detalle.tipos_transporte_data
        )
    ]
    vehiculo = _vehiculo_record_linea_paquete(linea)
    galeria = _render_galeria(
        linea,
        vehiculo.imagen if vehiculo else False,
        linea.wallpaper_data or detalle.wallpaper_data,
        linea.image_data or detalle.image_data,
        max_imagenes=1,
        mostrar_urls=True,
    )
    resumen = [
        f"<span class='story-kicker'>Transporte {indice}</span>",
        f"<h2>{escape(texto(linea.nombre))}</h2>",
        f"<div class='story-meta'>{escape(texto((linea.estilo_transporte_id or detalle.estilo_transporte_id).display_name if (linea.estilo_transporte_id or detalle.estilo_transporte_id) else 'Transporte'))} · {escape(fecha(linea.fecha))}</div>",
        _parrafo_editorial(linea.descripcion or detalle.descripcion),
    ]
    ruta = _render_lista_simple(
        [
            vehiculo.nombre if vehiculo else "",
            _texto_json_lista(
                linea.destino_origen_data or detalle.destino_origen_data,
                ["title", "nombre", "name"],
            ),
            _texto_json_lista(
                linea.destino_llegada_data or detalle.destino_llegada_data,
                ["title", "nombre", "name"],
            ),
            linea.modelo_vehiculo or detalle.modelo_vehiculo,
            linea.duracion_viaje or detalle.duracion_viaje,
            linea.distancia or detalle.distancia,
        ]
    )
    cuerpo = [
        _seccion_editorial("Ruta y datos del servicio", ruta),
        _seccion_editorial(
            "Punto de origen",
            _parrafo_editorial(linea.descripcion_origen or detalle.descripcion_origen),
        ),
        _seccion_editorial(
            "Punto de llegada",
            _parrafo_editorial(
                linea.descripcion_llegada or detalle.descripcion_llegada
            ),
        ),
        _seccion_editorial(
            linea.included_title or detalle.included_title or "Incluye",
            _render_lista_simple(incluye),
        ),
        _seccion_editorial(
            linea.excluded_title or detalle.excluded_title or "No incluye",
            _render_lista_simple(no_incluye),
        ),
        _seccion_editorial("Tipos de transporte", _render_lista_simple(tipos)),
    ]
    return f"""
    <article class="story-card">
      <div class="story-cover">
        {"".join([item for item in resumen if item])}
      </div>
      {galeria}
      <div class="story-body">
        {"".join([seccion for seccion in cuerpo if seccion])}
      </div>
      {_detalle_precio_linea(linea)}
    </article>
    """


def _bloque_texto_largo(titulo, contenido):
    if not contenido:
        return ""
    return f"""
    <div class="section">
      <div class="section-title">{escape(titulo)}</div>
      <div class="text-block">{escape(texto(contenido))}</div>
    </div>
    """


def _bloque_servicio_paquete(indice, linea):
    detalle = _detalle_catalogo_linea(linea)
    if linea.tipo_servicio == "tour":
        return _bloque_tour_editorial(indice, linea, detalle)
    return _bloque_transporte_editorial(indice, linea, detalle)


def render_reserva_paquete_html(reserva):
    lineas = reserva.paquete_linea_ids.sorted(
        lambda linea: (linea.sequence, linea.id)
    )
    portada = f"""
    <section class="package-hero">
      <div class="package-hero-copy">
        <div class="package-eyebrow">Detalle informativo del paquete</div>
        <h1>{escape(texto(reserva.name))}</h1>
        <p>Cliente: {escape(texto(reserva.partner_id.display_name))}</p>
        <p>Fecha de viaje: {escape(fecha(reserva.fecha_viaje))}</p>
        <p>Items del paquete: {len(lineas)}</p>
        {f"<p>{escape(texto(reserva.observaciones))}</p>" if reserva.observaciones else ""}
      </div>
      <div class="package-hero-total">
        <div class="ticket-label">Monto total</div>
        <div class="ticket-value">{escape(monto(reserva.moneda, reserva.monto_total))}</div>
      </div>
    </section>
    """
    historias = "".join(
        _bloque_servicio_paquete(indice, linea)
        for indice, linea in enumerate(lineas, start=1)
    )
    cierre = f"""
    <section class="package-total">
      <div class="package-total-label">Monto total del paquete</div>
      <div class="package-total-value">{escape(monto(reserva.moneda, reserva.monto_total))}</div>
    </section>
    """
    return f"""
    <html>
      <head>
        <meta charset="utf-8"/>
        <style>
          body {{
            font-family: Arial, sans-serif;
            color: #16302c;
            background: #f6f1e8;
            font-size: 13px;
            margin: 26px;
            line-height: 1.6;
          }}
          .package-hero {{
            background: #e8f4f2;
            color: #16302c;
            padding: 28px;
            border: 1px solid #1aa093;
            margin-bottom: 24px;
          }}
          .package-eyebrow {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.6px;
            color: #1aa093;
            margin-bottom: 10px;
            font-weight: 700;
          }}
          .package-hero h1 {{
            font-size: 30px;
            margin: 0 0 14px 0;
            color: #153530;
          }}
          .package-hero p {{
            margin: 0 0 6px 0;
            color: #304744;
          }}
          .package-hero-total {{
            margin-top: 18px;
            background: #ffffff;
            border: 1px solid #1aa093;
            padding: 18px 20px;
            width: 240px;
          }}
          .ticket-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            opacity: 0.8;
            margin-bottom: 8px;
          }}
          .ticket-value {{
            font-size: 28px;
            font-weight: 700;
            color: #153530;
          }}
          .story-card {{
            background: #ffffff;
            overflow: hidden;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(22, 48, 44, 0.08);
            border: 1px solid #e8ddd0;
          }}
          .story-cover {{
            padding: 24px 26px 12px 26px;
          }}
          .story-kicker {{
            display: inline-block;
            color: #1aa093;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1.4px;
            margin-bottom: 8px;
          }}
          .story-cover h2 {{
            font-size: 26px;
            margin: 0 0 8px 0;
            color: #153530;
          }}
          .story-meta {{
            color: #5b6e6a;
            font-size: 12px;
            margin-bottom: 10px;
          }}
          .editorial-copy {{
            margin: 0;
            color: #304744;
          }}
          .editorial-gallery {{
            padding: 0 20px 10px 20px;
            font-size: 0;
          }}
          .editorial-image {{
            display: inline-block;
            width: 48%;
            margin: 0 1% 12px 1%;
            vertical-align: top;
          }}
          .editorial-image img {{
            width: 100%;
            height: 215px;
            object-fit: cover;
            border: 1px solid #e8ddd0;
            display: block;
          }}
          .image-url-fallback {{
            border: 1px solid #d6c7b7;
            background: #fcfaf7;
            padding: 12px;
            color: #304744;
            font-size: 11px;
            line-height: 1.5;
          }}
          .image-url-title {{
            color: #1aa093;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 6px;
          }}
          .image-url-item {{
            word-break: break-all;
            margin-bottom: 4px;
          }}
          .story-body {{
            padding: 4px 26px 10px 26px;
          }}
          .editorial-section {{
            margin-bottom: 18px;
          }}
          .editorial-section h3 {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #1aa093;
            margin: 0 0 8px 0;
          }}
          .story-question {{
            font-size: 18px;
            font-weight: 700;
            color: #1aa093;
            margin: 0 0 8px 0;
          }}
          .editorial-list {{
            margin: 0;
            padding-left: 18px;
          }}
          .editorial-list li {{
            margin-bottom: 6px;
          }}
          .timeline-item {{
            border-top: 1px solid #e8ddd0;
            padding: 10px 0;
          }}
          .timeline-item:first-child {{
            border-top: 0;
            padding-top: 0;
          }}
          .timeline-title {{
            font-weight: 700;
            color: #153530;
            margin-bottom: 4px;
          }}
          .timeline-meta {{
            color: #1aa093;
            font-size: 12px;
            margin-bottom: 4px;
          }}
          .timeline-gallery {{
            font-size: 0;
            margin: 10px 0 8px 0;
          }}
          .timeline-gallery img {{
            width: 48%;
            height: 160px;
            object-fit: cover;
            border: 1px solid #e8ddd0;
            margin-right: 2%;
            display: inline-block;
          }}
          .timeline-text {{
            color: #304744;
          }}
          .timeline-note {{
            margin-top: 8px;
            color: #5b6e6a;
            font-size: 12px;
          }}
          .price-card {{
            background: #fcfaf7;
            border-top: 1px solid #eee3d6;
            padding: 18px 26px 24px 26px;
          }}
          .price-title {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #1aa093;
            font-weight: 700;
            margin-bottom: 10px;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
          }}
          .price-table td {{
            border-bottom: 1px solid #eadfce;
            padding: 9px 6px;
            vertical-align: top;
          }}
          .price-table th {{
            border-bottom: 1px solid #eadfce;
            padding: 9px 6px;
            vertical-align: top;
            text-align: left;
            color: #1aa093;
            font-weight: 700;
          }}
          .price-table tr:last-child td {{
            border-bottom: 0;
          }}
          .label {{
            color: #64706d;
            font-weight: 700;
            width: 42%;
          }}
          .package-total {{
            background: #153530;
            color: #ffffff;
            padding: 22px 26px;
            text-align: right;
            margin-top: 12px;
          }}
          .package-summary {{
            margin-top: 10px;
            margin-bottom: 18px;
          }}
          .package-summary .package-summary-meta-table {{
            margin-bottom: 12px;
          }}
          .package-total-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1.4px;
            opacity: 0.82;
            margin-bottom: 8px;
          }}
          .package-total-value {{
            font-size: 30px;
            font-weight: 700;
          }}
        </style>
      </head>
      <body>
        {portada}
        <section class="package-summary">
          {_tabla_datos_resumen_paquete(reserva)}
          {_tabla_resumen_paquete(reserva)}
        </section>
        {historias}
        {cierre}
      </body>
    </html>
    """


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
    return (
        "https://api-m.paypal.com"
        if os.getenv("PAYPAL_MODE") == "live"
        else "https://api-m.sandbox.paypal.com"
    )


def get_paypal_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    secret = os.getenv("PAYPAL_SECRET", "")
    if not client_id or not secret:
        raise ValueError("PAYPAL_CLIENT_ID y PAYPAL_SECRET son requeridos")
    credenciales = base64.b64encode(f"{client_id}:{secret}".encode("utf-8")).decode(
        "ascii"
    )
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
    capture = (((payload.get("purchase_units") or [{}])[0]).get("payments") or {}).get(
        "captures"
    ) or [{}]
    capture_data = capture[0]
    return {
        "estado": "pagado" if capture_data.get("status") == "COMPLETED" else "fallido",
        "transaccion_id": capture_data.get("id") or "",
    }


def enviar_correo_resend(
    api_key, from_email, to_email, subject, html, pdf_bytes, ticket
):
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
        raise ValueError(
            f"Resend respondió {error.code}: {error_http_text(error)}"
        ) from error


def html_correo_reserva(reserva, titulo, mensaje):
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background: #f3f7f6; padding: 24px;">
      <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4e2; border-radius: 12px; padding: 28px;">
        <div style="font-size: 12px; letter-spacing: 1.6px; font-weight: 700; color: #1aa093;">INCA'S PARADISE</div>
        <div style="font-size: 28px; line-height: 1.2; font-weight: 700; color: #1f2937; margin-top: 2px;">{escape(titulo)}</div>
        <p style="margin: 12px 0 24px 0; color: #374151;">{escape(mensaje)}</p>
        <div style="padding: 16px 18px; border: 1px solid #dbe4e2; border-radius: 10px; background: #f8fbfa; color: #374151;">
          Ticket: <strong>{escape(texto(reserva.ticket))}</strong><br/>
          Servicio: <strong>{escape(texto(reserva.servicio_nombre))}</strong><br/>
          Fecha de viaje: <strong>{escape(fecha(reserva.fecha_inicio or reserva.fecha_viaje))}</strong>
        </div>
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
