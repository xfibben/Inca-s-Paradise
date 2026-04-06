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
    // Sincroniza todas las reservas existentes con Google Sheets
    async syncSheets(ctx) {
      const url = process.env.GOOGLE_APPS_SCRIPT_URL;
      if (!url) {
        return ctx.badRequest('GOOGLE_APPS_SCRIPT_URL no configurado en .env');
      }

      const reservas = await strapi.entityService.findMany('api::reserva.reserva', {
        populate: ['tour', 'transportes'],
        limit: -1, // todas
      });

      let enviadas = 0;
      let errores = 0;

      for (const reserva of reservas as any[]) {
        try {
          await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry: reserva }),
            redirect: 'follow',
          });
          enviadas++;
        } catch (e) {
          errores++;
          strapi.log.error(`[Sheets] Error sincronizando reserva ID ${reserva.id}:`, e);
        }
      }

      return ctx.send({ ok: true, enviadas, errores, total: (reservas as any[]).length });
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

