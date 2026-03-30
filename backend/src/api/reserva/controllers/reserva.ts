/**
 * reserva controller
 */

import { factories } from '@strapi/strapi';

/**
 * Genera un ticket único para la reserva
 * Formato: TICKET-YYYYMMDD-XXXXX
 */
function generarTicket(): string {
  const fecha = new Date();
  const año = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  const aleatorio = Math.floor(Math.random() * 100000);
  const numeroAleatorio = String(aleatorio).padStart(5, '0');
  return `TICKET-${año}${mes}${dia}-${numeroAleatorio}`;
}

/**
 * Calcula monto_subtotal y monto_final (incluye IGV)
 * Jala los precios unitarios del tour-detalle relacionado
 */
/**
 * Extrae el documentId desde un campo de relación con formato { connect: [id] }
 */
function extraerDocumentId(campo: any): string | null {
  if (!campo) return null;
  const conectar = campo?.connect;
  if (!Array.isArray(conectar) || conectar.length === 0) return null;
  const primero = conectar[0];
  return typeof primero === 'string' ? primero : primero?.id ?? null;
}

/**
 * Calcula monto_subtotal y monto_final en USD
 * Los precios se obtienen directamente del tour-detalle o transporte relacionado
 */
async function calcularMontos(data: any, strapi: any): Promise<void> {
  try {
    let precioUnitarioAdulto = 0;
    let precioUnitarioNino = 0;

    let descuento = 0;

    if (data.tour) {
      const documentId = extraerDocumentId(data.tour);
      if (!documentId) { console.warn('No se pudo extraer documentId del tour'); return; }

      const [tour] = await strapi.documents('api::tour-detalle.tour-detalle').findMany({
        filters: { documentId },
        fields: ['adultUnitPrice', 'childUnitPrice', 'discount'],
        limit: 1,
      });
      if (!tour) { console.warn(`Tour con documentId ${documentId} no encontrado`); return; }
      precioUnitarioAdulto = parseFloat(tour.adultUnitPrice) || 0;
      precioUnitarioNino = parseFloat(tour.childUnitPrice) || 0;
      descuento = parseFloat(tour.discount) || 0;

    } else if (data.transportes) {
      const documentId = extraerDocumentId(data.transportes);
      if (!documentId) { console.warn('No se pudo extraer documentId del transporte'); return; }

      const transporte = await strapi.documents('api::transporte.transporte').findOne({
        documentId,
        fields: ['adultUnitPrice', 'childUnitPrice', 'discount'],
      });
      if (!transporte) { console.warn(`Transporte con documentId ${documentId} no encontrado`); return; }
      precioUnitarioAdulto = parseFloat(transporte.adultUnitPrice) || 0;
      precioUnitarioNino = parseFloat(transporte.childUnitPrice) || 0;
      descuento = parseFloat(transporte.discount) || 0;

    } else {
      return;
    }

    const cantidadAdultos = parseFloat(data.cantidad_adultos) || 0;
    const cantidadNinos = parseFloat(data.cantidad_ninos) || 0;

    // Cálculo en USD — sin IGV, descuento obtenido del tour/transporte
    const montoBase = (cantidadAdultos * precioUnitarioAdulto) + (cantidadNinos * precioUnitarioNino);
    const montoFinal = montoBase - descuento;

    data.descuento = Math.round(descuento * 100) / 100;
    data.monto_subtotal = Math.round(montoBase * 100) / 100;
    data.monto_final = Math.round(montoFinal * 100) / 100;

    console.log('Montos calculados (USD):', { monto_subtotal: data.monto_subtotal, descuento, monto_final: data.monto_final });
  } catch (error) {
    console.error('Error calculando montos:', error);
  }
}

export default factories.createCoreController('api::reserva.reserva', ({ strapi }) => {
  return {
    // Sincroniza las últimas 50 reservas con Google Sheets (reset completo del sheet)
    async syncSheets(ctx) {
      const url = 'https://script.google.com/macros/s/AKfycbyB82Zr3xKLnBfQgTA9-8xlCHdN7PfYOxG9k7X4l71FRJsa1xUBb5nLrw8qLQxH_uPN5g/exec';

      // Trae las últimas 50 ordenadas de más nueva a más antigua
      const reservas = await strapi.documents('api::reserva.reserva').findMany({
        populate: ['tour', 'transportes'],
        sort: { createdAt: 'desc' },
        limit: 50,
      }) as any[];

      // Construye cada entry con el mismo formato que el lifecycle
      const entries = reservas.map((reserva) => {
        const esTour = !!reserva.tour;
        const servicio = esTour ? reserva.tour : (reserva.transportes?.length ? reserva.transportes[0] : null);

        const nombreReserva = esTour ? (servicio?.title ?? '') : (servicio?.nombre ?? '');
        const precioAdulto  = parseFloat(servicio?.adultUnitPrice) || 0;
        const precioNino    = parseFloat(servicio?.childUnitPrice) || 0;
        const pagoTotal     = parseFloat(reserva.monto_final) || 0;
        const descuento     = parseFloat(reserva.descuento) || 0;
        const mitad         = parseFloat((pagoTotal / 2).toFixed(2));

        return {
          fecha:            reserva.createdAt ?? new Date().toISOString(),
          nombre_pax:       reserva.nombre ?? '',
          cantidad_adultos: reserva.cantidad_adultos ?? 0,
          cantidad_ninos:   reserva.cantidad_ninos ?? 0,
          hora_recojo:      '',
          nombre_reserva:   nombreReserva,
          tipo_ss:          servicio?.tourType ?? '',
          hotel:            '',
          estado:           reserva.estado ?? 'pendiente',
          precio_adulto:    precioAdulto,
          precio_nino:      precioNino,
          adelanto:         mitad,
          saldo:            mitad,
          porcentaje:       '',
          descuento:        descuento,
          pago_total:       pagoTotal,
          email:            reserva.email,
          telefono:         reserva.telefono,
          canal_venta:      'Web',
          notas:            reserva.notas ?? '',
          id:               reserva.ticket ?? reserva.id,
          tipo_servicio:    esTour ? 'tour' : 'transporte',
        };
      });

      try {
        await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ entries }),
          redirect: 'follow',
        });
        strapi.log.info(`[Sheets] Sync masivo: ${entries.length} reservas enviadas`);
        return ctx.send({ ok: true, total: entries.length });
      } catch (e) {
        strapi.log.error('[Sheets] Error en sync masivo:', e);
        return ctx.internalServerError('Error al sincronizar con Sheets');
      }
    },

    async create(ctx) {
      const { data } = ctx.request.body;
      if (data) {
        // Generar ticket único
        data.ticket = generarTicket();
        await calcularMontos(data, strapi);
      }
      return await super.create(ctx);
    },

    async update(ctx) {
      const { data } = ctx.request.body;
      if (data) {
        await calcularMontos(data, strapi);
      }
      return await super.update(ctx);
    },
  };
});

