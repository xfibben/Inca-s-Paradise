import { factories } from '@strapi/strapi';
export default factories.createCoreRouter('api::preguntas-frecuentes.preguntas-frecuentes', {
  config: {
    find: { auth: false },
    findOne: { auth: false }
  }
});
