/**
 * destino router
 */

import { factories } from "@strapi/strapi";

export default factories.createCoreRouter("api::destino.destino", {
  config: {
    find: {
      auth: false
    },
    findOne: {
      auth: false
    }
  }
});
