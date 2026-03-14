/**
 * tour-detalle router
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreRouter(
  'api::tour-detalle.tour-detalle',
  {
    config: {
      find: {
        auth: false
      },
      findOne: {
        auth: false
      }
    }
  }
);
