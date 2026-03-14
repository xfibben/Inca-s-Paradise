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
async function calcularMontos(data: any, strapi: any): Promise<void> {
  if (!data.tour) {
    return; // No puede calcular sin tour
  }

  try {
    // Obtener el tour para jalar los precios
    // En Strapi 5, usar entityService es más seguro
    const tour = await strapi.entityService.findOne('api::tour-detalle.tour-detalle', data.tour, {
      fields: ['precio_unitario_adulto', 'precio_unitario_nino']
    });

    if (!tour) {
      console.warn(`Tour con ID ${data.tour} no encontrado`);
      return; // Tour no encontrado
    }

    const cantidadAdultos = parseFloat(data.cantidad_adultos) || 0;
    const cantidadNinos = parseFloat(data.cantidad_ninos) || 0;
    const precioUnitarioAdulto = parseFloat(tour.precio_unitario_adulto) || 0;
    const precioUnitarioNino = parseFloat(tour.precio_unitario_nino) || 0;
    const descuento = parseFloat(data.descuento) || 0;
    const igvPorcentaje = parseFloat(data.igv_porcentaje) || 18;
    
    // Calcular subtotal antes de IGV
    const montoBase = (cantidadAdultos * precioUnitarioAdulto) + (cantidadNinos * precioUnitarioNino);
    const montoSubtotal = montoBase - descuento;
    
    // Calcular monto final = subtotal + IGV
    const montoFinal = montoSubtotal + (montoSubtotal * (igvPorcentaje / 100));
    
    data.monto_subtotal = Math.round(montoSubtotal * 100) / 100;
    data.monto_final = Math.round(montoFinal * 100) / 100;

    console.log('Montos calculados:', { monto_subtotal: data.monto_subtotal, monto_final: data.monto_final });
  } catch (error) {
    console.error('Error calculando montos:', error);
  }
}

export default factories.createCoreController('api::reserva.reserva', ({ strapi }) => {
  return {
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

