/**
 * Controlador de tipo-transporte
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::tipo-transporte.tipo-transporte', ({ strapi }) => ({
  async find(ctx) {
    const { locale } = ctx.query;

    const entries = await strapi.documents('api::tipo-transporte.tipo-transporte').findMany({
      locale: (locale as string) || 'es-PE',
      sort: ['nombre:asc'],
      populate: {
        image: true,
        wallpaper: true,
        transportes: true,
      } as any,
    });

    return { data: entries };
  },
}));
