/**
 * subcategoria-tour router
 */

import { factories } from '@strapi/strapi';

export default (factories as any).createCoreRouter(
  'api::subcategoria-tour.subcategoria-tour',
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
