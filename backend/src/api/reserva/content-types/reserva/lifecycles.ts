// Sincroniza reservas con Google Sheets vía Apps Script (gratis, sin Google Cloud)
async function sincronizarConSheets(id: number) {
  const url = 'https://script.google.com/macros/s/AKfycbzolk8iNVCTv435deCW9cA9nceXUhxyX5Gev6E73FnhmRsbl_1cfAzGeLLAoBp272zm_A/exec';
  // Fetch con relaciones populadas para obtener nombre y precios del tour/transporte
  const reserva = await strapi.documents('api::reserva.reserva').findFirst({
    filters: { id: { $eq: id } },
    populate: ['tour', 'transportes'],
  }) as any;

  if (!reserva) return;

  // Determina si es tour o transporte y extrae nombre y precios
  const esTour = !!reserva.tour;
  const servicio = esTour ? reserva.tour : (reserva.transportes?.length ? reserva.transportes[0] : null);

  const nombreReserva: string = esTour
    ? (servicio?.title ?? '')
    : (servicio?.nombre ?? '');

  const precioAdulto = parseFloat(servicio?.adultUnitPrice) || 0;
  const precioNino   = parseFloat(servicio?.childUnitPrice) || 0;

  const pagoTotal  = parseFloat(reserva.monto_final) || 0;
  const descuento  = parseFloat(reserva.descuento) || 0;
  const mitad      = parseFloat((pagoTotal / 2).toFixed(2));

  const entry = {
    fecha:             reserva.createdAt ?? new Date().toISOString(),
    nombre_pax:        reserva.nombre ?? '',
    cantidad_adultos:  reserva.cantidad_adultos ?? 0,
    cantidad_ninos:    reserva.cantidad_ninos ?? 0,
    hora_recojo:       '',
    nombre_reserva:    nombreReserva,
    tipo_ss:           servicio?.tourType ?? '',
    hotel:             '',
    estado:            reserva.estado ?? 'pendiente',
    precio_adulto:     precioAdulto,
    precio_nino:       precioNino,
    adelanto:          mitad,
    saldo:             mitad,
    porcentaje:        '',
    descuento:         descuento,
    pago_total:        pagoTotal,
    email:             reserva.email,
    telefono:          reserva.telefono,
    canal_venta:       'Web',
    notas:             reserva.notas ?? '',
    id:                reserva.ticket ?? id,
    tipo_servicio:     esTour ? 'tour' : 'transporte',
    prepend:           true,
  };

  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry }),
      redirect: 'follow',
    });

    strapi.log.info(`[Sheets] Reserva ${entry.id} sincronizada`);
  } catch (error) {
    strapi.log.error('[Sheets] Error al sincronizar:', error);
  }
}

export default {
  async afterCreate(event: any) {
    await sincronizarConSheets(event.result.id);
  },

  async afterUpdate(event: any) {
    await sincronizarConSheets(event.result.id);
  },
};
