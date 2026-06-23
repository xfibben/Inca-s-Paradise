from html import escape

def _texto(valor):
    if valor in (None, False):
        return "-"
    limpio = str(valor).strip()
    return limpio or "-"


def _fecha_corta(valor):
    if not valor:
        return "-"
    if isinstance(valor, str):
        partes = valor.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
        return valor
    return valor.strftime("%d/%m/%Y") if hasattr(valor, "strftime") else str(valor)


def _tabla_pasajeros(reserva):
    pasajeros = reserva.pasajero_ids.sorted(lambda item: (item.apellidos or "", item.nombres or "", item.id))
    if not pasajeros:
        return ""
    filas = []
    for pasajero in pasajeros:
        filas.append(
            f"""
            <tr>
                <td>{escape(_texto(pasajero.name))}</td>
                <td>{escape(_texto(pasajero.tipo_documento).upper() if pasajero.tipo_documento else "-")}</td>
                <td>{escape(_texto(pasajero.numero_documento))}</td>
                <td>{escape(_texto(pasajero.nacionalidad))}</td>
                <td>{escape(_texto(pasajero.telefono or pasajero.email))}</td>
            </tr>
            """
        )
    return f"""
    <div class="section">
        <div class="section-title">Pasajeros</div>
        <table class="detail-table">
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Documento</th>
                    <th>Nro</th>
                    <th>Nacionalidad</th>
                    <th>Contacto</th>
                </tr>
            </thead>
            <tbody>
                {''.join(filas)}
            </tbody>
        </table>
    </div>
    """


def _tabla_hoteles(reserva):
    lineas = reserva.hotel_linea_ids.sorted(lambda item: (item.fecha_check_in or reserva.fecha_inicio or reserva.fecha_viaje, item.sequence, item.id))
    if not lineas:
        return ""
    filas = []
    for linea in lineas:
        filas.append(
            f"""
            <tr>
                <td>{escape(_fecha_corta(linea.fecha_check_in))}</td>
                <td>{escape(_fecha_corta(linea.fecha_check_out))}</td>
                <td>{escape(_texto(linea.hotel_nombre or linea.hotel_id.name))}</td>
                <td>{escape(_texto(linea.cantidad_noches))}</td>
                <td>{escape(_texto(linea.cantidad_habitaciones))}</td>
            </tr>
            """
        )
    return f"""
    <div class="section">
        <div class="section-title">Hoteles</div>
        <table class="detail-table">
            <thead>
                <tr>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Hotel</th>
                    <th>Noches</th>
                    <th>Habitaciones</th>
                </tr>
            </thead>
            <tbody>
                {''.join(filas)}
            </tbody>
        </table>
    </div>
    """


def _tabla_extras(reserva):
    lineas = reserva.extra_linea_ids.sorted(lambda item: (item.sequence, item.id))
    if not lineas:
        return ""
    filas = []
    for linea in lineas:
        filas.append(
            f"""
            <tr>
                <td>{escape(_texto(linea.extra_nombre or linea.extra_id.name))}</td>
                <td>{escape(_texto(linea.cantidad_extra))}</td>
                <td>{escape(_texto(linea.extra_unidad))}</td>
            </tr>
            """
        )
    return f"""
    <div class="section">
        <div class="section-title">Extras</div>
        <table class="detail-table">
            <thead>
                <tr>
                    <th>Extra</th>
                    <th>Cantidad</th>
                    <th>Unidad</th>
                </tr>
            </thead>
            <tbody>
                {''.join(filas)}
            </tbody>
        </table>
    </div>
    """


def _tabla_cronograma(reserva):
    lineas = reserva.operacion_linea_ids.sorted(lambda item: (item.fecha, item.sequence, item.id))
    filas = []
    for linea in lineas:
        filas.append(
            f"""
            <tr>
                <td>{escape(_fecha_corta(linea.fecha))}</td>
                <td>{escape(_texto(linea.horario))}</td>
                <td>{escape(_texto(linea.lugar_recojo))}</td>
                <td>{escape(_texto(linea.servicio))}</td>
                <td>{escape(_texto(linea.hotel_nombre))}</td>
                <td>{escape(_texto(linea.extras))}</td>
                <td>{escape(_texto(linea.guia))}</td>
                <td>{escape(_texto(linea.observacion))}</td>
            </tr>
            """
        )
    return f"""
    <div class="section">
        <div class="section-title">Cronograma operativo</div>
        <table class="detail-table">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Horario</th>
                    <th>Lugar de recojo</th>
                    <th>Servicio</th>
                    <th>Hotel</th>
                    <th>Extras</th>
                    <th>Guia</th>
                    <th>Observacion</th>
                </tr>
            </thead>
            <tbody>
                {''.join(filas)}
            </tbody>
        </table>
    </div>
    """


def render_pase_operativo_html(reserva):
    return f"""
    <html>
        <head>
            <meta charset="utf-8"/>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    color: #1f2937;
                    margin: 24px;
                }}
                h1 {{
                    margin: 0 0 6px 0;
                    font-size: 24px;
                    color: #0f766e;
                }}
                .subtitle {{
                    margin-bottom: 18px;
                    color: #4b5563;
                }}
                .summary {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 18px;
                }}
                .summary td {{
                    border: 1px solid #d1d5db;
                    padding: 8px;
                }}
                .summary .label {{
                    width: 180px;
                    font-weight: 700;
                    background: #f3f4f6;
                }}
                .section {{
                    margin-top: 18px;
                }}
                .section-title {{
                    padding: 8px 10px;
                    background: #0f766e;
                    color: white;
                    font-weight: 700;
                }}
                .detail-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .detail-table th,
                .detail-table td {{
                    border: 1px solid #d1d5db;
                    padding: 6px 8px;
                    vertical-align: top;
                    text-align: left;
                }}
                .detail-table th {{
                    background: #ecfeff;
                }}
            </style>
        </head>
        <body>
            <h1>Pase operativo</h1>
            <div class="subtitle">{escape(_texto(reserva.ticket))} - {escape(_texto(reserva.servicio_nombre))}</div>

            <table class="summary">
                <tr><td class="label">Cliente</td><td>{escape(_texto(reserva.nombre or reserva.partner_id.name))}</td></tr>
                <tr><td class="label">Pasajeros</td><td>{escape(_texto(reserva.cantidad_pasajeros))}</td></tr>
                <tr><td class="label">Fecha inicio</td><td>{escape(_fecha_corta(reserva.fecha_inicio or reserva.fecha_viaje))}</td></tr>
                <tr><td class="label">Fecha fin</td><td>{escape(_fecha_corta(reserva.fecha_fin or reserva.fecha_viaje))}</td></tr>
                <tr><td class="label">Lugar de recojo</td><td>{escape(_texto(reserva.lugar_recojo))}</td></tr>
                <tr><td class="label">Observaciones</td><td>{escape(_texto(reserva.observaciones))}</td></tr>
            </table>

            {_tabla_cronograma(reserva)}
            {_tabla_hoteles(reserva)}
            {_tabla_extras(reserva)}
            {_tabla_pasajeros(reserva)}
        </body>
    </html>
    """
