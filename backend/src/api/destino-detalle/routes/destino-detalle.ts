/**
 * destino-detalle router
 */

import { factories } from "@strapi/strapi";

export default factories.createCoreRouter(
  "api::destino-detalle.destino-detalle",
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
