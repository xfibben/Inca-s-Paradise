// Generador de comprobante PDF para reservas de tours y transporte

interface PendingBooking {
  nombre?: string;
  email?: string;
  telefono?: string;
  tipo_documento?: string;
  numero_documento?: string;
  nacionalidad?: string;
  tourNombre?: string;
  vehiculo_seleccionado?: string | null;
  tourDocumentId?: string | null;
  transporteDocumentId?: string | null;
  fecha_inicio?: string;
  fecha_fin?: string;
  turno?: string | null;
  cantidad_adultos?: number;
  cantidad_ninos?: number;
  notas?: string | null;
  simbolo_moneda?: string;
  decimales_moneda?: number;
  monto_original?: number;
  monto_total?: number;
  porcentaje_pago?: number;
  moneda?: string;
}

async function cargarLogo(): Promise<string | null> {
  try {
    const svgResp = await fetch("/favicon.svg");
    const svgText = await svgResp.text();
    const blob = new Blob([svgText], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    return await new Promise<string | null>((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = 95;
        canvas.height = 95;
        const ctx = canvas.getContext("2d");
        ctx?.drawImage(img, 0, 0, 95, 95);
        const dataUrl = canvas.toDataURL("image/png");
        URL.revokeObjectURL(url);
        resolve(dataUrl);
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(null); };
      img.src = url;
    });
  } catch {
    return null;
  }
}

async function obtenerDestino(tourDocumentId: string, strapiBase: string): Promise<string> {
  try {
    const r = await fetch(`${strapiBase}/api/tour-detalles/${tourDocumentId}?populate[destinos][fields][0]=nombre`);
    if (!r.ok) return "";
    const tj = await r.json();
    const destinos = tj?.data?.destinos;
    if (Array.isArray(destinos) && destinos.length > 0) return destinos[0]?.nombre ?? "";
    if (destinos?.nombre) return destinos.nombre;
  } catch { /* continuar sin destino */ }
  return "";
}

export async function generarVoucherPDF(ticket: string, booking: PendingBooking | undefined): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "mm", format: "a4" });

  const logoDataUrl = await cargarLogo();

  // ── Encabezado verde ──
  doc.setFillColor(26, 160, 147);
  doc.rect(0, 0, 210, 42, "F");

  if (logoDataUrl) {
    doc.addImage(logoDataUrl, "PNG", 13, 6, 16, 16);
  }

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");
  doc.text("Inca's Paradise", logoDataUrl ? 32 : 15, 17);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  const esTransporte = !!booking?.transporteDocumentId;
  const tipoServicio = esTransporte ? "Transporte" : "Tour";
  doc.text(`Comprobante de Reserva de ${tipoServicio}`, logoDataUrl ? 32 : 15, 26);

  const fechaEmision = new Date().toLocaleDateString("es-PE", { day: "2-digit", month: "long", year: "numeric" });
  doc.setFontSize(8);
  doc.text(`Emitido: ${fechaEmision}`, 197, 36, { align: "right" });

  // ── Ticket destacado ──
  doc.setFillColor(245, 240, 233);
  doc.roundedRect(15, 50, 180, 22, 3, 3, "F");
  doc.setDrawColor(26, 160, 147);
  doc.setLineWidth(0.5);
  doc.roundedRect(15, 50, 180, 22, 3, 3, "S");
  doc.setTextColor(100, 116, 139);
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.text("NÚMERO DE TICKET", 105, 57, { align: "center" });
  doc.setTextColor(26, 160, 147);
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.text(ticket, 105, 67, { align: "center" });

  // ── Destino desde Strapi ──
  let destinoNombre = "";
  if (booking?.tourDocumentId) {
    const strapiBase = (window as any).__strapiUrl ?? "http://localhost:1337";
    destinoNombre = await obtenerDestino(booking.tourDocumentId, strapiBase);
  }

  // ── Helpers de layout ──
  let y = 84;
  const lineH = 8;

  const seccion = (titulo: string) => {
    doc.setFillColor(26, 160, 147);
    doc.rect(15, y, 180, 7, "F");
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text(titulo, 18, y + 5);
    y += 11;
  };

  const fila = (label: string, valor: string) => {
    doc.setTextColor(100, 116, 139);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.text(label, 18, y);
    doc.setTextColor(31, 41, 55);
    doc.setFont("helvetica", "bold");
    doc.text(valor || "—", 80, y);
    y += lineH;
  };

  // Fila con salto de línea para textos largos — máximo 2 líneas, resto con "..."
  const filaMultilinea = (label: string, valor: string) => {
    doc.setTextColor(100, 116, 139);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.text(label, 18, y);
    doc.setTextColor(31, 41, 55);
    doc.setFont("helvetica", "bold");
    const anchoMax = 115; // mm disponibles desde x=80 hasta x=195
    const lineas = doc.splitTextToSize(valor || "—", anchoMax) as string[];
    if (lineas.length <= 2) {
      doc.text(lineas, 80, y);
      y += lineH * lineas.length;
    } else {
      // Truncar en 2 líneas y agregar "..."
      const dosLineas = lineas.slice(0, 2);
      const ultima = dosLineas[1];
      dosLineas[1] = ultima.length > 3 ? ultima.slice(0, -3) + "..." : "...";
      doc.text(dosLineas, 80, y);
      y += lineH * 2;
    }
  };

  // ── Secciones ──
  seccion("DATOS DEL PASAJERO");
  fila("Nombre completo:", booking?.nombre || "—");
  fila("Correo electrónico:", booking?.email || "—");
  fila("Teléfono:", booking?.telefono || "—");
  fila("Tipo de documento:", booking?.tipo_documento?.toUpperCase() || "—");
  fila("Número de documento:", booking?.numero_documento || "—");
  fila("Nacionalidad:", booking?.nacionalidad || "—");

  y += 4;
  seccion(`DETALLES DEL ${tipoServicio.toUpperCase()}`);
  fila(`${tipoServicio}:`, booking?.tourNombre || "—");
  if (esTransporte && booking?.vehiculo_seleccionado) fila("Vehículo:", booking.vehiculo_seleccionado);
  if (destinoNombre) fila("Destino:", destinoNombre);
  fila("Fecha de inicio:", booking?.fecha_inicio || "—");
  fila("Fecha de fin:", booking?.fecha_fin || "—");
  if (booking?.turno) fila("Horario:", booking.turno);
  fila("Adultos:", String(booking?.cantidad_adultos ?? "—"));
  fila("Niños:", String(booking?.cantidad_ninos ?? 0));
  if (booking?.notas) filaMultilinea("Notas:", booking.notas ?? "");

  y += 4;
  seccion("RESUMEN DE PAGO");
  const simbolo = booking?.simbolo_moneda ?? "$";
  const dec = booking?.decimales_moneda ?? 2;
  const montoOriginal = booking?.monto_original ?? booking?.monto_total ?? 0;
  const montoPagado = booking?.monto_total ?? 0;
  const porcentaje = booking?.porcentaje_pago ?? 30;
  fila(`Monto total del ${tipoServicio.toLowerCase()}:`, `${simbolo}${montoOriginal.toFixed(dec)} ${booking?.moneda ?? "USD"}`);
  fila(`Pagado (${porcentaje}%):`, `${simbolo}${montoPagado.toFixed(dec)} ${booking?.moneda ?? "USD"}`);
  if (porcentaje < 100) {
    const resto = montoOriginal - montoPagado;
    fila("Saldo en agencia:", `${simbolo}${resto.toFixed(dec)} ${booking?.moneda ?? "USD"}`);
  }

  // ── Nota al pie ──
  y += 8;
  doc.setFillColor(245, 240, 233);
  doc.rect(15, y, 180, 20, "F");
  doc.setTextColor(100, 116, 139);
  doc.setFontSize(8);
  doc.setFont("helvetica", "italic");
  doc.text(`Este comprobante es válido como confirmación de reserva. Preséntelo el día del ${tipoServicio.toLowerCase()}.`, 105, y + 7, { align: "center" });
  doc.text("Para consultas: contacto@incasparadise.com", 105, y + 14, { align: "center" });

  // ── Pie de página ──
  doc.setTextColor(100, 116, 139);
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.text("www.incasparadise.com", 105, 285, { align: "center" });

  doc.save(`comprobante-${ticket}.pdf`);
}
