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

export default factories.createCoreController(
  "api::destino-detalle.destino-detalle",
  () => ({
    async find(ctx) {
      ctx.query = {
        ...ctx.query,
        sort: ctx.query?.sort ?? ["displayOrder:asc", "title:asc"]
      };

      const response = await super.find(ctx);
      if (!response) return response;
      return {
        ...response,
        data: decorateResponseData((response as any).data)
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