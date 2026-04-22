import { jsPDF } from 'jspdf';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

function texto(valor: unknown): string {
  if (valor === null || valor === undefined) return '-';
  const limpio = String(valor).trim();
  return limpio || '-';
}

function numero(valor: unknown): number {
  const n = Number(valor);
  return Number.isFinite(n) ? n : 0;
}

function formatearFecha(valor: unknown): string {
  if (!valor) return '-';
  const fecha = new Date(String(valor));
  if (Number.isNaN(fecha.getTime())) return texto(valor);
  return new Intl.DateTimeFormat('es-PE', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(fecha);
}

function escaparHtml(valor: unknown): string {
  return texto(valor)
    .split('&').join('&amp;')
    .split('<').join('&lt;')
    .split('>').join('&gt;')
    .split('"').join('&quot;')
    .split("'").join('&#39;');
}

function obtenerServicio(reserva: any) {
  const esTour = !!reserva?.tour;
  const servicio = esTour ? reserva.tour : (Array.isArray(reserva?.transportes) ? reserva.transportes[0] : null);
  const tipoServicio = esTour ? 'Tour' : 'Transporte';
  const nombreServicio = esTour
    ? texto(servicio?.title)
    : texto(servicio?.nombre);

  return { esTour, tipoServicio, nombreServicio };
}

function tipoTourLabel(valor: unknown): string {
  if (valor === 'small_trip') return 'Small Trip';
  if (valor === 'package') return 'Paquete';
  return 'Tour';
}

function tipoServicioDetalle(reserva: any): string {
  if (reserva?.tour) return tipoTourLabel(reserva.tour?.tourType);

  const transporte = Array.isArray(reserva?.transportes) ? reserva.transportes[0] : null;
  const tipos = Array.isArray(transporte?.tipos_transporte) ? transporte.tipos_transporte : [];
  const nombres = tipos
    .map((item: any) => texto(item?.nombre))
    .filter((item: string) => item !== '-');

  return nombres.length > 0 ? nombres.join(', ') : 'Transporte';
}

function simboloMoneda(moneda: unknown): string {
  if (moneda === 'PEN') return 'S/ ';
  if (moneda === 'EUR') return 'EUR ';
  return '$ ';
}

function monto(moneda: unknown, valor: unknown): string {
  return `${simboloMoneda(moneda)}${numero(valor).toFixed(2)} ${texto(moneda)}`;
}

function filaTabla(label: string, value: unknown): string {
  return `
    <tr>
      <td style="padding: 10px 12px; border: 1px solid #d1d5db; background: #f8fafc; color: #475569; font-weight: 600; width: 38%;">${escaparHtml(label)}</td>
      <td style="padding: 10px 12px; border: 1px solid #d1d5db; color: #111827;">${escaparHtml(value)}</td>
    </tr>
  `;
}

function bloqueTabla(titulo: string, filas: string): string {
  return `
    <div style="margin: 0 0 24px 0;">
      <div style="background: #1aa093; color: #ffffff; font-weight: 700; padding: 10px 14px; border-radius: 8px 8px 0 0;">
        ${escaparHtml(titulo)}
      </div>
      <table cellpadding="0" cellspacing="0" role="presentation" style="width: 100%; border-collapse: collapse; border: 1px solid #d1d5db; border-top: 0; background: #ffffff;">
        ${filas}
      </table>
    </div>
  `;
}

async function logoCorreoDataUrl(): Promise<string> {
  const filePath = path.resolve(process.cwd(), '..', 'frontend', 'public', 'favicon.svg');
  const svg = await readFile(filePath, 'utf8');
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`;
}

function encabezadoCorreo(logo: string, titulo: string, subtitulo: string): string {
  return `
    <div style="margin: 0 0 24px 0; padding: 0 0 20px 0; border-bottom: 1px solid #dbe4e2;">
      <table cellpadding="0" cellspacing="0" role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="width: 68px; vertical-align: middle;">
            ${logo ? `<img src="${logo}" alt="INCA'S PARADISE" width="52" height="52" style="display: block; width: 52px; height: 52px;" />` : ''}
          </td>
          <td style="vertical-align: middle;">
            <div style="font-size: 12px; letter-spacing: 1.6px; font-weight: 700; color: #1aa093;">INCA'S PARADISE</div>
            <div style="font-size: 28px; line-height: 1.2; font-weight: 700; color: #1f2937; margin-top: 2px;">${escaparHtml(titulo)}</div>
          </td>
        </tr>
      </table>
      <p style="margin: 12px 0 0 0; color: #374151;">${escaparHtml(subtitulo)}</p>
    </div>
  `;
}

function construirDetalleCorreo(reserva: any) {
  const { esTour, tipoServicio, nombreServicio } = obtenerServicio(reserva);
  const tipoServicioReal = tipoServicioDetalle(reserva);
  const moneda = reserva?.moneda_usuario ?? 'USD';
  const labelNombreServicio = esTour ? 'Nombre del tour' : 'Nombre del transporte';
  const filasPasajero = [
    filaTabla('Nombre completo', reserva?.nombre),
    filaTabla('Correo electrónico', reserva?.email),
    filaTabla('Teléfono', reserva?.telefono),
    filaTabla('Tipo de documento', texto(reserva?.tipo_documento).toUpperCase()),
    filaTabla('Número de documento', reserva?.numero_documento),
    filaTabla('Nacionalidad', reserva?.nacionalidad),
  ].join('');

  const filasReserva = [
    filaTabla('Ticket', reserva?.ticket),
    filaTabla('Tipo de servicio', tipoServicioReal),
    filaTabla(labelNombreServicio, nombreServicio),
    !esTour ? filaTabla('Vehículo seleccionado', reserva?.vehiculo_seleccionado) : '',
    filaTabla('Fecha de inicio', formatearFecha(reserva?.fecha_inicio)),
    filaTabla('Fecha de fin', formatearFecha(reserva?.fecha_fin)),
    filaTabla('Horario', reserva?.turno),
    filaTabla('Cantidad de adultos', numero(reserva?.cantidad_adultos)),
    filaTabla('Cantidad de niños', numero(reserva?.cantidad_ninos)),
    filaTabla('Notas', reserva?.notas),
    filaTabla('Estado de reserva', reserva?.estado),
    filaTabla('Estado de pago', reserva?.estado_pago),
  ].join('');

  const filasPago = [
    filaTabla('Moneda', moneda),
    filaTabla('Descuento', `${numero(reserva?.descuento).toFixed(2)}%`),
    filaTabla('Precio total del servicio', monto(moneda, reserva?.precio_tour || reserva?.monto_estimado || reserva?.monto_final)),
    filaTabla('Monto estimado', monto(moneda, reserva?.monto_estimado)),
    filaTabla('Monto pagado en web', monto(moneda, reserva?.monto_web)),
    filaTabla('Precio web adultos', monto(moneda, reserva?.precio_adulto_web)),
    filaTabla('Precio web niños', monto(moneda, reserva?.precio_nino_web)),
    filaTabla('Saldo pendiente', monto(moneda, reserva?.pago_restante)),
    filaTabla('Monto final registrado', monto(moneda, reserva?.monto_final)),
  ].join('');

  return {
    tipoServicio,
    tipoServicioReal,
    nombreServicio,
    pasajero: bloqueTabla('Datos del pasajero', filasPasajero),
    reserva: bloqueTabla('Datos de la reserva', filasReserva),
    pago: bloqueTabla('Resumen de pago', filasPago),
  };
}

function generarPdfReserva(reserva: any): Buffer {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const { tipoServicio, nombreServicio } = obtenerServicio(reserva);
  const simbolo = reserva?.moneda_usuario === 'EUR' ? 'EUR ' : reserva?.moneda_usuario === 'PEN' ? 'S/ ' : '$ ';
  const montoTotal = numero(reserva?.monto_estimado || reserva?.precio_tour || reserva?.monto_final);
  const montoPagado = numero(reserva?.monto_web);
  const saldo = numero(reserva?.pago_restante);
  let y = 18;

  const seccion = (titulo: string) => {
    doc.setFillColor(26, 160, 147);
    doc.rect(15, y, 180, 8, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text(titulo, 18, y + 5.4);
    y += 14;
  };

  const fila = (label: string, value: string) => {
    doc.setTextColor(90, 90, 90);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.text(label, 18, y);
    doc.setTextColor(20, 20, 20);
    doc.setFont('helvetica', 'bold');
    const lineas = doc.splitTextToSize(value || '-', 110) as string[];
    doc.text(lineas, 82, y);
    y += Math.max(7, lineas.length * 6);
  };

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(26, 160, 147);
  doc.text("Inca's Paradise", 15, y);
  y += 8;

  doc.setFontSize(12);
  doc.setTextColor(40, 40, 40);
  doc.text(`Comprobante de reserva de ${tipoServicio}`, 15, y);
  y += 10;

  doc.setFillColor(245, 248, 247);
  doc.roundedRect(15, y, 180, 18, 2, 2, 'F');
  doc.setDrawColor(26, 160, 147);
  doc.roundedRect(15, y, 180, 18, 2, 2, 'S');
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(100, 116, 139);
  doc.text('TICKET', 105, y + 6, { align: 'center' });
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15);
  doc.setTextColor(26, 160, 147);
  doc.text(texto(reserva?.ticket), 105, y + 13, { align: 'center' });
  y += 26;

  seccion('DATOS DEL PASAJERO');
  fila('Nombre completo:', texto(reserva?.nombre));
  fila('Correo electrónico:', texto(reserva?.email));
  fila('Teléfono:', texto(reserva?.telefono));
  fila('Tipo de documento:', texto(reserva?.tipo_documento).toUpperCase());
  fila('Número de documento:', texto(reserva?.numero_documento));
  fila('Nacionalidad:', texto(reserva?.nacionalidad));

  y += 4;
  seccion(`DETALLES DEL ${tipoServicio.toUpperCase()}`);
  fila(`${tipoServicio}:`, nombreServicio);
  if (!obtenerServicio(reserva).esTour && reserva?.vehiculo_seleccionado) {
    fila('Vehículo:', texto(reserva.vehiculo_seleccionado));
  }
  fila('Fecha de inicio:', formatearFecha(reserva?.fecha_inicio));
  fila('Fecha de fin:', formatearFecha(reserva?.fecha_fin));
  if (reserva?.turno) fila('Horario:', texto(reserva.turno));
  fila('Adultos:', String(numero(reserva?.cantidad_adultos)));
  fila('Niños:', String(numero(reserva?.cantidad_ninos)));
  if (reserva?.notas) fila('Notas:', texto(reserva.notas));

  y += 4;
  seccion('RESUMEN DE PAGO');
  fila(`Monto total del ${tipoServicio.toLowerCase()}:`, `${simbolo}${montoTotal.toFixed(2)} ${texto(reserva?.moneda_usuario)}`);
  fila('Pagado:', `${simbolo}${montoPagado.toFixed(2)} ${texto(reserva?.moneda_usuario)}`);
  fila('Saldo pendiente:', `${simbolo}${saldo.toFixed(2)} ${texto(reserva?.moneda_usuario)}`);
  fila('Estado de reserva:', texto(reserva?.estado));
  fila('Estado de pago:', texto(reserva?.estado_pago));

  y += 8;
  doc.setFont('helvetica', 'italic');
  doc.setFontSize(9);
  doc.setTextColor(90, 90, 90);
  doc.text('Adjunto encontrarás este comprobante en PDF para tu control.', 15, y);
  doc.text('Contacto: incasparadise@gmail.com', 15, y + 6);

  return Buffer.from(doc.output('arraybuffer'));
}

function htmlCliente(reserva: any, logo: string): string {
  const detalle = construirDetalleCorreo(reserva);

  return `
    <div style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background: #f3f7f6; padding: 24px;">
      <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4e2; border-radius: 12px; padding: 28px;">
        ${encabezadoCorreo(logo, 'Confirmación de reserva', `Hola ${texto(reserva?.nombre)}, tu reserva fue registrada correctamente. Adjuntamos el comprobante PDF.`)}
        ${detalle.pasajero}
        ${detalle.reserva}
        ${detalle.pago}
      </div>
    </div>
  `;
}

function htmlAdmin(reserva: any, logo: string): string {
  const detalle = construirDetalleCorreo(reserva);

  return `
    <div style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background: #f3f7f6; padding: 24px;">
      <div style="max-width: 760px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4e2; border-radius: 12px; padding: 28px;">
        ${encabezadoCorreo(logo, 'Nueva reserva recibida', 'Se registró una nueva reserva y el comprobante PDF va adjunto.')}
        ${detalle.pasajero}
        ${detalle.reserva}
        ${detalle.pago}
      </div>
    </div>
  `;
}

async function enviarCorreo(payload: {
  apiKey: string;
  from: string;
  to: string;
  subject: string;
  html: string;
  pdfBase64: string;
  ticket: string;
}) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${payload.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: payload.from,
      to: [payload.to],
      subject: payload.subject,
      html: payload.html,
      attachments: [
        {
          filename: `comprobante-${payload.ticket}.pdf`,
          content: payload.pdfBase64,
        },
      ],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Resend respondió ${res.status}: ${body}`);
  }
}

export async function enviarCorreosReserva(strapi: any, id: number) {
  const apiKey = process.env.RESEND_API_KEY ?? '';
  const fromEmail = process.env.RESEND_FROM_EMAIL ?? '';
  const fromName = (process.env.RESEND_FROM_NAME ?? "INCA'S PARADISE").toUpperCase();
  const notifyEmail = process.env.RESEND_NOTIFY_EMAIL ?? 'incasparadise@gmail.com';

  if (!apiKey || !fromEmail) {
    strapi.log.warn('[Correo] RESEND_API_KEY o RESEND_FROM_EMAIL no configurados - envío omitido');
    return;
  }

  const reserva = await strapi.documents('api::reserva.reserva').findFirst({
    filters: { id: { $eq: id } },
    populate: {
      tour: true,
      transportes: {
        populate: ['tipos_transporte'],
      },
    },
  }) as any;

  if (!reserva) return;

  const pdfBuffer = generarPdfReserva(reserva);
  const pdfBase64 = pdfBuffer.toString('base64');
  const from = `${fromName} <${fromEmail}>`;
  const logo = await logoCorreoDataUrl().catch(() => '');

  await enviarCorreo({
    apiKey,
    from,
    to: notifyEmail,
    subject: `INCA'S PARADISE - Nueva reserva ${texto(reserva.ticket)}`,
    html: htmlAdmin(reserva, logo),
    pdfBase64,
    ticket: texto(reserva.ticket),
  });

  if (reserva.email) {
    await enviarCorreo({
      apiKey,
      from,
      to: String(reserva.email),
      subject: `INCA'S PARADISE - Confirmación de reserva ${texto(reserva.ticket)}`,
      html: htmlCliente(reserva, logo),
      pdfBase64,
      ticket: texto(reserva.ticket),
    });
  }
}
