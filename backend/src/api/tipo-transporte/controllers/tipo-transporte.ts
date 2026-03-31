/**
 * Controlador de tipo-transporte
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::tipo-transporte.tipo-transporte', ({ strapi }) => ({
  async find(ctx) {
    const { locale, filters, sort } = ctx.query;

    const entries = await strapi.documents('api::tipo-transporte.tipo-transporte').findMany({
      locale: (locale as string) || 'es-PE',
      filters: filters as any,
      sort: (sort as any) ?? ['nombre:asc'],
      populate: {
        image: true,
        wallpaper: true,
        transportes: {
          populate: {
            image: true,
            destino_origen: { fields: ['title'] },
            destino_llegada: { fields: ['title'] },
            precios: {
              populate: {
                vehiculo: {
                  populate: {
                    imagen: true,
                    features: true,
                  },
                },
              },
            },
          },
        },
      } as any,
    });

    return { data: entries };
  },
}));
