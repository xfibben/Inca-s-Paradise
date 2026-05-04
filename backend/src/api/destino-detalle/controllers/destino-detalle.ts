/**
 * destino-detalle controller
 */

import { factories } from "@strapi/strapi";

type GenericRecord = Record<string, any>;

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

export default factories.createCoreController(
  "api::destino-detalle.destino-detalle",
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

        const subcategorias = await strapi.documents("api::subcategoria-tour.subcategoria-tour").findMany({
          filters: { destino: { documentId: { $in: destinoDocumentIds } } } as any,
          fields: ["nombre"],
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
    }
  })
);
