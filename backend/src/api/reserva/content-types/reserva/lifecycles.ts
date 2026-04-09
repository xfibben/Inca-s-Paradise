// Sincroniza reservas con Google Sheets vía Apps Script (gratis, sin Google Cloud)
async function sincronizarConSheets(id: number) {
  const url = process.env.GOOGLE_APPS_SCRIPT_URL;
  if (!url) {
    strapi.log.warn('[Sheets] GOOGLE_APPS_SCRIPT_URL no configurada — sincronización omitida');
    return;
  }
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

  const pagoTotal        = parseFloat(reserva.monto_final)       || 0;
  const descuento        = parseFloat(reserva.descuento)         || 0;
  const montoWeb         = parseFloat(reserva.monto_web)         || 0;
  const montoAgencia     = parseFloat(reserva.monto_agencia)     || 0;
  const precioAdultoWeb  = parseFloat(reserva.precio_adulto_web) || 0;
  const precioNinoWeb    = parseFloat(reserva.precio_nino_web)   || 0;

  const entry = {
    fecha:             reserva.createdAt ?? new Date().toISOString(),
    id:                reserva.ticket ?? id,
    nombre_pax:        reserva.nombre ?? '',
    email:             reserva.email ?? '',
    telefono:          reserva.telefono ?? '',
    tipo_documento:    reserva.tipo_documento ?? '',
    numero_documento:  reserva.numero_documento ?? '',
    nacionalidad:      reserva.nacionalidad ?? '',
    cantidad_adultos:  reserva.cantidad_adultos ?? 0,
    cantidad_ninos:    reserva.cantidad_ninos ?? 0,
    precio_adulto:     precioAdulto,
    precio_nino:       precioNino,
    precio_adulto_web: precioAdultoWeb,
    precio_nino_web:   precioNinoWeb,
    fecha_inicio:      reserva.fecha_inicio ?? '',
    fecha_fin:         reserva.fecha_fin ?? '',
    hora_recojo:       reserva.turno ?? '',
    nombre_reserva:    nombreReserva,
    tipo_servicio:     esTour ? 'tour' : 'transporte',
    descuento:         descuento,
    precio_tour:       parseFloat(reserva.precio_tour) || 0,
    adelanto:          montoWeb,
    saldo:             montoAgencia,
    pago_total:        pagoTotal,
    estado:            reserva.estado ?? 'pendiente',
    estado_pago:       reserva.estado_pago ?? '',
    moneda:            reserva.moneda_usuario ?? 'USD',
    canal_venta:       'Web',
    notas:             reserva.notas ?? '',
    prepend:           true,
  };

  try {
    const body = JSON.stringify({ entry });
    const headers = { 'Content-Type': 'application/json' };

    // Apps Script devuelve 302 — Node.js convierte POST→GET al seguirlo,
    // por eso se obtiene el URL redirigido y se re-hace el POST manualmente
    const firstRes = await fetch(url, { method: 'POST', headers, body, redirect: 'manual' });
    const redirectUrl = firstRes.headers.get('location') ?? url;

    await fetch(redirectUrl, { method: 'POST', headers, body });

    strapi.log.info(`[Sheets] Reserva ${entry.id} sincronizada`);
  } catch (error) {
    strapi.log.error('[Sheets] Error al sincronizar:', error);
  }
}

// Recalcula monto_web y monto_final antes de guardar
// monto_agencia NO se calcula — se llena manualmente en el admin
function calcularMontos(data: any) {
  // monto_web = precio_adulto_web + precio_nino_web (ya incluyen las cantidades)
  const precioAdultoWeb = parseFloat(data.precio_adulto_web) || 0;
  const precioNinoWeb   = parseFloat(data.precio_nino_web)   || 0;

  if (precioAdultoWeb > 0 || precioNinoWeb > 0) {
    data.monto_web = parseFloat((precioAdultoWeb + precioNinoWeb).toFixed(2));
  }

  // monto_final = monto_web + monto_agencia
  const web     = parseFloat(data.monto_web)     || 0;
  const agencia = parseFloat(data.monto_agencia) || 0;
  if (web > 0 || agencia > 0) {
    data.monto_final = parseFloat((web + agencia).toFixed(2));
  }
}

export default {
  beforeCreate(event: any) {
    calcularMontos(event.params.data);
  },

  beforeUpdate(event: any) {
    const data = event.params.data;
    // En update el admin envía todos los campos — nunca recalcular monto_agencia
    // para no pisar ediciones manuales. Solo actualizar monto_final.
    const web     = parseFloat(data.monto_web)     || 0;
    const agencia = parseFloat(data.monto_agencia) || 0;
    if (web > 0 || agencia > 0) {
      data.monto_final = parseFloat((web + agencia).toFixed(2));
    }

    // Pasar a pago_completo automáticamente si monto_final >= precio_tour
    // Solo si el usuario no lo está cambiando manualmente a otro estado
    const precioTour = parseFloat(data.precio_tour) || 0;
    const montoFinal = parseFloat(data.monto_final) || 0;
    const estadoPagoManual = data.estado_pago;
    if (precioTour > 0 && montoFinal >= precioTour && estadoPagoManual !== 'pendiente' && estadoPagoManual !== 'fallido') {
      data.estado_pago = 'pago_completo';
    }
  },

  afterCreate(event: any) {
    // setImmediate garantiza que corre fuera de la transacción de Strapi
    const id = event.result.id;
    setImmediate(() => {
      sincronizarConSheets(id).catch((err) =>
        strapi.log.error('[Sheets] Error en afterCreate:', err)
      );
    });
  },

  afterUpdate(event: any) {
    const id = event.result.id;
    setImmediate(() => {
      sincronizarConSheets(id).catch((err) =>
        strapi.log.error('[Sheets] Error en afterUpdate:', err)
      );
    });
  },
};
