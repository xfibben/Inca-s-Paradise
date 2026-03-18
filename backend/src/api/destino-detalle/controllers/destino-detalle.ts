import { factories } from "@strapi/strapi";

type GenericRecord = Record<string, any>;

// --- FUNCIONES DE UTILIDAD (Las mismas que usas en destino-detalle) ---

function toMediaObject(value: any): GenericRecord | null {
  if (!value) return null;
  const candidate = value?.attributes ?? value;
  if (candidate?.url || candidate?.formats) return candidate;
  const relationData = value?.data;
  if (relationData) {
    const relationCandidate = relationData?.attributes ?? relationData;
    return relationCandidate?.url || relationCandidate?.formats ? relationCandidate : null;
  }
  return null;
}

function decorateItemWithGalleryImage(item: GenericRecord): GenericRecord {
  if (!item || typeof item !== "object") return item;

  // Extraemos las imágenes del tour (heroSlideImages)
  const heroImagesRaw = Array.isArray(item.heroSlideImages) 
    ? item.heroSlideImages 
    : [];
    
  const heroImages = heroImagesRaw
    .map((entry: any) => toMediaObject(entry))
    .filter(Boolean);

  // Generamos los slides dinámicos (heroSlides) basados en tus campos heroTitle1, etc.
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
    .filter(Boolean);

  return {
    ...item,
    heroSlides: fixedSlides.length > 0 ? fixedSlides : [],
    // Limpiamos campos internos de Strapi por seguridad
    createdBy: undefined,
    updatedBy: undefined
  };
}

function decorateResponseData(input: any) {
  if (Array.isArray(input)) {
    return input.map((item) => decorateItemWithGalleryImage(item));
  }
  return decorateItemWithGalleryImage(input);
}

// --- CONTROLADOR PRINCIPAL ---

export default factories.createCoreController('api::destino-detalle.destino-detalle', ({ strapi }) => ({
  async find(ctx) {
    const { locale } = ctx.query;

    const entries = await strapi.documents('api::destino-detalle.destino-detalle').findMany({
      locale: (locale as string) || 'es-PE',
      populate: {
        // Traemos Estilos sin datos sensibles
        // Traemos Destinos sin datos sensibles
        ogImage:true,
        tours: {
          fields: ['title', 'slug'],
          populate: {
            heroSlideImages: true
          }
        },
        // Campos de imagen del Tour mismo
      } as any,
    });

    // Aplicamos la decoración para generar heroSlides y limpiar autores/passwords
    const decoratedData = decorateResponseData(entries);

    return { data: decoratedData };
  },
}));