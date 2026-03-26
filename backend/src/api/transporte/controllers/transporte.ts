/**
 * Controlador de transporte
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::transporte.transporte', ({ strapi }) => ({
  async find(ctx) {
    const { locale } = ctx.query;

    const entries = await strapi.documents('api::transporte.transporte').findMany({
      locale: (locale as string) || 'es-PE',
      sort: ['nombre:asc'],
      populate: {
        image: true,
        wallpaper: true,
        destino_origen: true,
        destino_llegada: true,
      } as any,
    });

    return { data: entries };
  },
}));
