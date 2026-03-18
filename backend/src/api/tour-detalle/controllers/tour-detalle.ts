import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::tour-detalle.tour-detalle', ({ strapi }) => ({
  async find(ctx) {
    const { locale } = ctx.query;

    const entries = await strapi.documents('api::tour-detalle.tour-detalle').findMany({
      locale: (locale as string) || 'es-PE',
      populate: {
        // Seleccionamos campos específicos para evitar traer autores o contraseñas
        estilos: {
          fields: ['name', 'description', 'middle_tittle', 'middle_description'],
          populate: {
            image: true,
            wallpaper: true
          }
        },
        destinos: {
          fields: ['title', 'slug', 'description', 'heroTitle1', 'heroDescription1'],
          populate: {
            ogImage: true,
            heroSlideImages: true
          }
        },
        // Imágenes del tour principal
        heroSlideImages: true,
        highlightsImage: true
      } as any,
    });

    return { data: entries };
  },
}));