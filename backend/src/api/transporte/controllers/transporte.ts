/**
 * Controlador de transporte
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::transporte.transporte', ({ strapi }) => ({
  async find(ctx) {
    const { locale, filters, sort } = ctx.query;

    const entries = await strapi.documents('api::transporte.transporte').findMany({
      locale: (locale as string) || 'es-PE',
      filters: filters as any,
      sort: (sort as any) ?? ['nombre:asc'],
      fields: ['nombre', 'slug', 'modelo_vehiculo', 'duracion_viaje', 'distancia', 'descripcion_origen', 'descripcion_llegada', 'descripcion', 'includedTitle', 'excludedTitle'] as any,
      populate: {
        image: true,
        wallpaper: true,
        destino_origen: { fields: ['title'] },
        destino_llegada: { fields: ['title'] },
        tipos_transporte: { fields: ['nombre', 'slug'] },
        includedItems: true,
        excludedItems: true,
        precios: {
          populate: {
            vehiculo: {
              populate: { imagen: true },
            },
          },
        },
      } as any,
    });

    return { data: entries };
  },
}));
