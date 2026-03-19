/**
 * destino controller
 */

import { factories } from "@strapi/strapi";

function emptyDestino(locale?: string | null) {
  return {
    data: {
      id: 0,
      title: "",
      description: "",
      ribbonText: "",
      contactBandText: "",
      contactBandPhone: "",
      contactBandButtonLabel: "",
      contactBandButtonUrl: "#",
      locale: locale ?? null
    }
  };
}

export default factories.createCoreController(
  "api::destino.destino",
  ({ strapi }) => ({
    async find(ctx) {
      const locale = (ctx.query as any)?.locale ?? null;
      const status =
        (ctx.query as any)?.status === "draft" ? "draft" : "published";

      const entry = await strapi.documents("api::destino.destino").findFirst({
        locale: locale ?? undefined,
        status,
        fields: [
          "title",
          "description",
          "ribbonText",
          "contactBandText",
          "contactBandPhone",
          "contactBandButtonLabel",
          "contactBandButtonUrl"
        ]
      });

      if (!entry) {
        return emptyDestino(locale);
      }

      return { data: entry };
    }
  })
);
