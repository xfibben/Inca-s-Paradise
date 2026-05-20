/**
 * destino-detalle controller
 */

import { factories } from "@strapi/strapi";

type GenericRecord = Record<string, any>;
const SUBCATEGORIA_TOUR_UID = "api::subcategoria-tour.subcategoria-tour" as any;
const DESTINO_UID = "api::destino-detalle.destino-detalle";
const DEFAULT_STATUS = "published";
const ODOO_LOCALE_CODES = {
  es: ["es-PE", "es"],
  en: ["en-US", "en"],
  pt: ["pt-BR", "pt"],
};

function toMediaObject(value: any): GenericRecord | null {
  if (!value) return null;

  if (Array.isArray(value)) {
    const first = value[0];
    if (!first) return null;
    const firstCandidate = first?.attributes ?? first;
    return firstCandidate?.url || firstCandidate?.formats ? firstCandidate : null;
  }

  const candidate = value?.attributes ?? value;
  if (candidate?.url || candidate?.formats) return candidate;

  const relationData = value?.data;
  if (Array.isArray(relationData)) {
    const first = relationData[0];
    if (!first) return null;
    const firstCandidate = first?.attributes ?? first;
    return firstCandidate?.url || firstCandidate?.formats ? firstCandidate : null;
  }

  if (relationData) {
    const relationCandidate = relationData?.attributes ?? relationData;
    return relationCandidate?.url || relationCandidate?.formats
      ? relationCandidate
      : null;
  }

  return null;
}

function decorateItemWithGalleryImage(item: GenericRecord): GenericRecord {
  if (!item || typeof item !== "object") return item;

  const heroImagesRaw = Array.isArray(item.heroSlideImages)
    ? item.heroSlideImages
    : Array.isArray(item.heroSlideImages?.data)
      ? item.heroSlideImages.data
      : [];
  const heroImages = heroImagesRaw
    .map((entry: any) => toMediaObject(entry))
    .filter(Boolean);

  const existingSlides = Array.isArray(item.heroSlides) ? item.heroSlides : [];
  const fixedSlides = [1, 2, 3]
    .map((index) => {
      const title = item[`heroTitle${index}`];
      const description = item[`heroDescription${index}`];
      const image = heroImages[index - 1] ?? null;
      if (!title && !description && !image) return null;
      return {
        title: title ?? item.title ?? "",
        description: description ?? item.description ?? "",
        image: image ?? null
      };
    })
    .filter(Boolean) as GenericRecord[];

  const fallbackMedia =
    toMediaObject(item.galleryThumbnail) ??
    heroImages[0] ??
    toMediaObject(item.heroSlideImages);

  const baseSlides = fixedSlides.length > 0 ? fixedSlides : existingSlides;
  if (baseSlides.length === 0) {
    if (!fallbackMedia) return item;
    return {
      ...item,
      heroSlides: [
        {
          title: item.title ?? "",
          description: item.description ?? "",
          image: fallbackMedia
        }
      ]
    };
  }

  const normalizedSlides = baseSlides.map((slide: any, index: number) => {
    const hasImageObject =
      slide?.image &&
      typeof slide.image === "object" &&
      (slide.image.url || slide.image.formats);
    if (hasImageObject || !fallbackMedia || index !== 0) return slide;
    return {
      ...slide,
      image: fallbackMedia
    };
  });

  return {
    ...item,
    heroSlides: normalizedSlides
  };
}

function decorateResponseData(input: any) {
  if (Array.isArray(input)) {
    return input.map((item) => decorateItemWithGalleryImage(item));
  }
  if (input && typeof input === "object") {
    return decorateItemWithGalleryImage(input);
  }
  return input;
}

function normalizeTourItem(tour: any) {
  if (!tour || typeof tour !== "object") return null;
  return {
    documentId: tour.documentId ?? null,
    title: tour.title ?? "",
    slug: tour.slug ?? "",
    heroSlideImages: Array.isArray(tour.heroSlideImages) ? tour.heroSlideImages : []
  };
}

const escapeCsvValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }

  const text = String(value).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  return `"${text.replace(/"/g, '""')}"`;
};

const normalizeStatus = (status: unknown): "draft" | "published" => {
  return status === "draft" ? "draft" : "published";
};

const getPreferredLocale = (availableLocales: string[], candidates: string[]) => {
  for (const candidate of candidates) {
    if (availableLocales.includes(candidate)) {
      return candidate;
    }
  }

  return null;
};

const buildIconosJson = (items: any[]) =>
  JSON.stringify(
    items.map((item, index) => ({
      orden: index + 1,
      titulo: item?.label ?? "",
    }))
  );

export default factories.createCoreController(
  DESTINO_UID,
  ({ strapi }) => ({
    async find(ctx) {
      ctx.query = {
        ...ctx.query,
        sort: ctx.query?.sort ?? ["displayOrder:asc", "title:asc"]
      };

      const response = await super.find(ctx);
      if (!response) return response;

      const data: any[] = Array.isArray((response as any).data) ? (response as any).data : [];

      if (data.length > 0) {
        const locale = (ctx.query as any)?.locale ?? undefined;
        const destinoDocumentIds = data.map((d: any) => d.documentId).filter(Boolean);

        const tours = await strapi.documents("api::tour-detalle.tour-detalle").findMany({
          filters: { destinos: { documentId: { $in: destinoDocumentIds } } } as any,
          fields: ["title", "slug"],
          populate: {
            heroSlideImages: { fields: ["url", "alternativeText"] },
            destinos: { fields: ["documentId"] }
          } as any,
          status: "published",
          ...(locale ? { locale } : {})
        });

        const toursByDestino: Record<string, any[]> = {};
        for (const tour of (tours as any[])) {
          const destinos: any[] = Array.isArray(tour.destinos) ? tour.destinos : [];
          for (const d of destinos) {
            const did = d.documentId;
            if (!toursByDestino[did]) toursByDestino[did] = [];
            toursByDestino[did].push(normalizeTourItem(tour));
          }
        }

        const subcategorias = await (strapi as any).documents(SUBCATEGORIA_TOUR_UID).findMany({
          filters: { destino: { documentId: { $in: destinoDocumentIds } } } as any,
          fields: ["nombre"] as any,
          populate: {
            destino: { fields: ["documentId"] },
            tours: {
              fields: ["title", "slug"],
              populate: {
                heroSlideImages: { fields: ["url", "alternativeText"] }
              }
            }
          } as any,
          status: "published",
          ...(locale ? { locale } : {})
        });

        const subcategoriasByDestino: Record<string, any[]> = {};
        const groupedTourKeysByDestino: Record<string, Set<string>> = {};

        for (const subcategoria of (subcategorias as any[])) {
          const destino = subcategoria?.destino;
          const destinoDocumentId = destino?.documentId;
          if (!destinoDocumentId) continue;

          const toursRelacionados = Array.isArray(subcategoria?.tours)
            ? subcategoria.tours.map(normalizeTourItem).filter(Boolean)
            : [];

          if (!subcategoriasByDestino[destinoDocumentId]) {
            subcategoriasByDestino[destinoDocumentId] = [];
          }

          if (!groupedTourKeysByDestino[destinoDocumentId]) {
            groupedTourKeysByDestino[destinoDocumentId] = new Set<string>();
          }

          toursRelacionados.forEach((tour: any) => {
            const key = tour.documentId || tour.slug || tour.title;
            if (key) groupedTourKeysByDestino[destinoDocumentId].add(key);
          });

          subcategoriasByDestino[destinoDocumentId].push({
            nombre: subcategoria?.nombre ?? "",
            tours: toursRelacionados
          });
        }

        const decorated = decorateResponseData(data).map((item: any) => ({
          ...item,
          tours: (toursByDestino[item.documentId] ?? []).filter((tour: any) => {
            const key = tour.documentId || tour.slug || tour.title;
            return !groupedTourKeysByDestino[item.documentId]?.has(key);
          }),
          subcategorias_tour: subcategoriasByDestino[item.documentId] ?? []
        }));

        return { ...response, data: decorated };
      }

      return {
        ...response,
        data: decorateResponseData(data)
      };
    },

    async findOne(ctx) {
      const response = await super.findOne(ctx);
      if (!response) return response;
      return {
        ...response,
        data: decorateResponseData((response as any).data)
      };
    },

    async exportCsv(ctx) {
      const status = normalizeStatus(ctx.query?.status ?? DEFAULT_STATUS);
      const locales = await strapi.query("plugin::i18n.locale").findMany({
        orderBy: { id: "asc" },
      } as any);
      const availableLocaleCodes = locales.map((item: { code: string }) => item.code);
      const localeCodes = {
        es: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.es),
        en: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.en),
        pt: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.pt),
      };
      const localesToExport = Array.from(
        new Set(Object.values(localeCodes).filter((value): value is string => Boolean(value)))
      );
      const destinosByDocument = new Map<string, Record<string, any>>();

      for (const localeCode of localesToExport) {
        const destinos = await strapi.documents(DESTINO_UID).findMany({
          locale: localeCode,
          status,
          sort: ["displayOrder:asc", "title:asc"],
          fields: [
            "documentId",
            "publishedAt",
            "title",
            "displayOrder",
            "slug",
            "description",
            "seoTitle",
            "seoDescription",
            "introTitle",
            "introContent",
            "primaryRibbon",
            "catalogInitialVisibleCount",
          ] as any,
          populate: {
            iconItems: {
              fields: ["label"] as any,
            },
          } as any,
        });

        for (const destino of Array.isArray(destinos) ? destinos : []) {
          const documentId = destino?.documentId;
          if (!documentId) {
            continue;
          }

          const current = destinosByDocument.get(documentId) ?? {};
          current[localeCode] = destino;
          destinosByDocument.set(documentId, current);
        }
      }

      const headers = [
        "nombre",
        "orden_visual",
        "slug",
        "slug_en",
        "slug_pt",
        "descripcion",
        "descripcion_en",
        "descripcion_pt",
        "seo_titulo",
        "seo_titulo_en",
        "seo_titulo_pt",
        "seo_descripcion",
        "seo_descripcion_en",
        "seo_descripcion_pt",
        "titulo_intro",
        "titulo_intro_en",
        "titulo_intro_pt",
        "contenido_intro",
        "contenido_intro_en",
        "contenido_intro_pt",
        "cinta_principal",
        "cinta_principal_en",
        "cinta_principal_pt",
        "cantidad_inicial_catalogo",
        "iconos_import_json",
        "iconos_import_json_en",
        "iconos_import_json_pt",
        "active",
      ];

      const rows = Array.from(destinosByDocument.values())
        .sort((left, right) => {
          const leftDestino = (localeCodes.es && left[localeCodes.es]) || (localeCodes.en && left[localeCodes.en]) || {};
          const rightDestino = (localeCodes.es && right[localeCodes.es]) || (localeCodes.en && right[localeCodes.en]) || {};
          return String(leftDestino?.title ?? "").localeCompare(String(rightDestino?.title ?? ""));
        })
        .map((destinoByLocale) => {
          const destinoEs = localeCodes.es ? destinoByLocale[localeCodes.es] ?? null : null;
          const destinoEn = localeCodes.en ? destinoByLocale[localeCodes.en] ?? null : null;
          const destinoPt = localeCodes.pt ? destinoByLocale[localeCodes.pt] ?? null : null;
          const baseDestino = destinoEs ?? destinoEn ?? destinoPt ?? {};

          return [
            destinoEs?.title ?? "",
            baseDestino?.displayOrder ?? "",
            destinoEs?.slug ?? "",
            destinoEn?.slug ?? "",
            destinoPt?.slug ?? "",
            destinoEs?.description ?? "",
            destinoEn?.description ?? "",
            destinoPt?.description ?? "",
            destinoEs?.seoTitle ?? "",
            destinoEn?.seoTitle ?? "",
            destinoPt?.seoTitle ?? "",
            destinoEs?.seoDescription ?? "",
            destinoEn?.seoDescription ?? "",
            destinoPt?.seoDescription ?? "",
            destinoEs?.introTitle ?? "",
            destinoEn?.introTitle ?? "",
            destinoPt?.introTitle ?? "",
            destinoEs?.introContent ?? "",
            destinoEn?.introContent ?? "",
            destinoPt?.introContent ?? "",
            destinoEs?.primaryRibbon ?? "",
            destinoEn?.primaryRibbon ?? "",
            destinoPt?.primaryRibbon ?? "",
            baseDestino?.catalogInitialVisibleCount ?? "",
            buildIconosJson(Array.isArray(destinoEs?.iconItems) ? destinoEs.iconItems : []),
            buildIconosJson(Array.isArray(destinoEn?.iconItems) ? destinoEn.iconItems : []),
            buildIconosJson(Array.isArray(destinoPt?.iconItems) ? destinoPt.iconItems : []),
            baseDestino?.publishedAt ? "True" : "False",
          ];
        });

      const csv = [
        headers.map(escapeCsvValue).join(","),
        ...rows.map((row) => row.map(escapeCsvValue).join(",")),
      ].join("\n");

      ctx.set("Content-Type", "text/csv; charset=utf-8");
      ctx.set("Content-Disposition", `attachment; filename="destinos-odoo-${status}.csv"`);
      ctx.body = `\uFEFF${csv}`;
    }
  })
);
