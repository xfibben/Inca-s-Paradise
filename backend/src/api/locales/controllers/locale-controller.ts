import type { Core } from '@strapi/strapi';

const localeController = ({ strapi }: { strapi: Core.Strapi }) => ({
  async getLocales(ctx) {
    try {
      // Obtener todos los locales disponibles del plugin i18n de Strapi
      const locales = await strapi.query('plugin::i18n.locale').findMany();
      
      // Mapear a un formato más simple y limpiar el nombre
      const formattedLocales = locales.map((locale: { code: string; name: string }) => ({
        code: locale.code,
        // Remover la parte entre paréntesis del nombre (ej: "English (en)" -> "English")
        name: locale.name.replace(/\s*\([^)]*\)\s*/g, '').trim(),
      }));

      ctx.body = {
        success: true,
        data: formattedLocales,
      };
    } catch (error) {
      ctx.throw(500, {
        error: 'Failed to fetch locales',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  },
});

export default localeController;
