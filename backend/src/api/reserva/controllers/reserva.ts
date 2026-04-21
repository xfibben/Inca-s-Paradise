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
 * Calcula monto_estimado, monto_web (30%) y pago_restante (70%) en USD
 * Los precios se obtienen directamente del tour-detalle o transporte relacionado
 */
async function calcularMontos(data: any, strapi: any): Promise<void> {
  try {
    const precioTourRecibido = parseFloat(data.precio_tour) || parseFloat(data.monto_estimado) || 0;
    const precioAdultoWebRecibido = parseFloat(data.precio_adulto_web) || 0;
    const precioNinoWebRecibido = parseFloat(data.precio_nino_web) || 0;
    const descuentoRecibido = parseFloat(data.descuento) || 0;

    if (precioTourRecibido > 0 || precioAdultoWebRecibido > 0 || precioNinoWebRecibido > 0) {
      data.descuento = Math.round(descuentoRecibido * 100) / 100;
      if (precioTourRecibido > 0) {
        data.monto_estimado = Math.round(precioTourRecibido * 100) / 100;
      }
      if (precioAdultoWebRecibido > 0 || precioNinoWebRecibido > 0) {
        data.monto_web = Math.round((precioAdultoWebRecibido + precioNinoWebRecibido) * 100) / 100;
      }
      if ((parseFloat(data.monto_estimado) || 0) > 0 && (parseFloat(data.monto_web) || 0) >= 0) {
        data.pago_restante = Math.round(((parseFloat(data.monto_estimado) || 0) - (parseFloat(data.monto_web) || 0)) * 100) / 100;
      }
      return;
    }

    let precioUnitarioAdulto = 0;
    let precioUnitarioNino = 0;
    let descuentoPorcentaje = 0;

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
      descuentoPorcentaje = parseFloat(tour.discount) || 0;

    } else if (data.transportes) {
      const documentId = extraerDocumentId(data.transportes);
      if (!documentId) { console.warn('No se pudo extraer documentId del transporte'); return; }

      const transporte = await strapi.documents('api::transporte.transporte').findOne({
        documentId,
        populate: {
          precios: {
            populate: ['vehiculo'],
          },
        },
      });
      if (!transporte) { console.warn(`Transporte con documentId ${documentId} no encontrado`); return; }
      const vehiculoSeleccionado = String(data.vehiculo_seleccionado ?? '').trim().toLowerCase();
      const precios = Array.isArray(transporte.precios) ? transporte.precios : [];
      const precioTransporte = precios.find((precio: any) =>
        Array.isArray(precio?.vehiculo) &&
        precio.vehiculo.some((veh: any) => String(veh?.nombre ?? '').trim().toLowerCase() === vehiculoSeleccionado)
      ) ?? precios[0] ?? null;
      precioUnitarioAdulto = parseFloat(precioTransporte?.precioAdulto) || 0;
      precioUnitarioNino = parseFloat(precioTransporte?.precioNino) || 0;
      descuentoPorcentaje = parseFloat(precioTransporte?.descuento) || 0;

    } else {
      return;
    }

    const cantidadAdultos = parseFloat(data.cantidad_adultos) || 0;
    const cantidadNinos = parseFloat(data.cantidad_ninos) || 0;

    // Cálculo base usando descuento porcentual
    const montoBase = (cantidadAdultos * precioUnitarioAdulto) + (cantidadNinos * precioUnitarioNino);
    const montoFinal = montoBase - (montoBase * Math.max(0, descuentoPorcentaje)) / 100;

    const montoWeb     = Math.round(montoFinal * 0.3 * 100) / 100;
    const montoAgencia = Math.round((montoFinal - montoWeb) * 100) / 100;

    data.descuento      = Math.round(descuentoPorcentaje * 100) / 100;
    data.monto_estimado = Math.round(montoFinal * 100) / 100;
    data.monto_web      = montoWeb;
    data.pago_restante  = montoAgencia;
    // monto_final lo calcula el lifecycle beforeCreate/beforeUpdate

    console.log('Montos calculados (USD):', { monto_estimado: data.monto_estimado, monto_web: montoWeb, pago_restante: montoAgencia });
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
