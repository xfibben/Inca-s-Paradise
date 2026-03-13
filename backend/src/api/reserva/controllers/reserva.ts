/**
 * reserva controller
 */

import { factories } from '@strapi/strapi';

/**
 * Calcula monto_subtotal y monto_final (incluye IGV)
 */
function calcularMontos(data: any): void {
  const cantidadAdultos = parseFloat(data.cantidad_adultos) || 0;
  const cantidadNinos = parseFloat(data.cantidad_ninos) || 0;
  const montoUnitarioAdulto = parseFloat(data.monto_unitario_adulto) || 0;
  const montoUnitarioNino = parseFloat(data.monto_unitario_nino) || 0;
  const descuento = parseFloat(data.descuento) || 0;
  const igvPorcentaje = parseFloat(data.igv_porcentaje) || 18;
  
  // Calcular subtotal antes de IGV
  const montoBase = (cantidadAdultos * montoUnitarioAdulto) + (cantidadNinos * montoUnitarioNino);
  const montoSubtotal = montoBase - descuento;
  
  // Calcular monto final = subtotal + IGV
  const montoFinal = montoSubtotal + (montoSubtotal * (igvPorcentaje / 100));
  
  data.monto_subtotal = Math.round(montoSubtotal * 100) / 100;
  data.monto_final = Math.round(montoFinal * 100) / 100;
}

export default factories.createCoreController('api::reserva.reserva', ({ strapi }) => {
  // Registrar hooks globales
  strapi.db.lifecycles.subscribe({
    models: ['api::reserva.reserva'],
    async beforeCreate(event) {
      calcularMontos(event.params.data);
    },
    async beforeUpdate(event) {
      calcularMontos(event.params.data);
    }
  });

  return {
    async create(ctx) {
      const { data } = ctx.request.body;
      if (data) {
        calcularMontos(data);
      }
      return await super.create(ctx);
    },

    async update(ctx) {
      const { data } = ctx.request.body;
      if (data) {
        calcularMontos(data);
      }
      return await super.update(ctx);
    },
  };
});

