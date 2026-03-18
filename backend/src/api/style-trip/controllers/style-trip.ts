/**
 * style-trip controller
 */

import { factories } from "@strapi/strapi";

export default factories.createCoreController('api::style-trip.style-trip', ({ strapi }) => ({
  async find(ctx) {
    const { locale } = ctx.query;

    const entries = await strapi.documents('api::style-trip.style-trip').findMany({
      locale: (locale as string) || 'es-PE',
      sort: ['displayOrder:asc', 'name:asc'],
      populate: {
        image: true,
        tours: true
      } as any,
    });

    return { data: entries };
  },
}));