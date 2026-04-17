import { factories } from '@strapi/strapi';
export default factories.createCoreRouter('api::politicas.politicas', {
  config: {
    find: { auth: false },
    findOne: { auth: false }
  }
});
