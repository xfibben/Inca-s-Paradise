function computeEndDate(data: Record<string, any>) {
  const { startDate, durationDays } = data;
  if (startDate && durationDays && durationDays >= 1) {
    const start = new Date(startDate);
    start.setDate(start.getDate() + durationDays - 1);
    data.endDate = start.toISOString().split('T')[0];
  }
}

function toSingleMediaId(value: any): number | null {
  if (!value) return null;
  if (typeof value === 'number') return value;
  if (value?.id && typeof value.id === 'number') return value.id;
  if (value?.data?.id && typeof value.data.id === 'number') return value.data.id;
  return null;
}

function toManyMediaIds(value: any): number[] {
  if (!value) return [];

  const rows = Array.isArray(value)
    ? value
    : Array.isArray(value?.data)
      ? value.data
      : [];

  return rows
    .map((item) => {
      if (typeof item === 'number') return item;
      if (item?.id && typeof item.id === 'number') return item.id;
      if (item?.data?.id && typeof item.data.id === 'number') return item.data.id;
      return null;
    })
    .filter((id): id is number => typeof id === 'number');
}

function isExplicitlyEmptyMedia(value: any, multiple: boolean): boolean {
  if (value === null) return true;

  if (multiple) {
    if (Array.isArray(value)) return value.length === 0;
    if (Array.isArray(value?.set)) return value.set.length === 0;
    if (Array.isArray(value?.connect)) return value.connect.length === 0;
  } else {
    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value?.connect) && value.connect.length === 0) return true;
      if (Array.isArray(value?.set) && value.set.length === 0) return true;
      if (Array.isArray(value?.disconnect) && value.disconnect.length > 0 && !value.connect && !value.set) {
        return true;
      }
      if (Object.keys(value).length === 0) return true;
    }
  }

  return false;
}

function hasMediaAssigned(value: any, multiple: boolean): boolean {
  if (multiple) return toManyMediaIds(value).length > 0;
  return toSingleMediaId(value) !== null;
}

function hasAnySharedImage(row: any): boolean {
  if (!row || typeof row !== 'object') return false;

  if (hasMediaAssigned(row.heroSlideImages, true)) return true;
  if (hasMediaAssigned(row.ogImage, false)) return true;
  if (hasMediaAssigned(row.twitterImage, false)) return true;

  if (Array.isArray(row.featuredImages)) {
    const hasFeatured = row.featuredImages.some((item) => hasMediaAssigned(item?.image, false));
    if (hasFeatured) return true;
  }

  if (Array.isArray(row.itineraryItems)) {
    const hasItinerary = row.itineraryItems.some((item) => hasMediaAssigned(item?.image, false));
    if (hasItinerary) return true;
  }

  return false;
}

function setDirectSharedMedia(
  data: Record<string, any>,
  key: string,
  sourceValue: any,
  options: { multiple: boolean; isCreate: boolean }
) {
  const current = data[key];
  const missingOnCreate = options.isCreate && current === undefined;
  const explicitlyEmpty = isExplicitlyEmptyMedia(current, options.multiple);

  if (!missingOnCreate && !explicitlyEmpty) return;

  if (options.multiple) {
    const ids = toManyMediaIds(sourceValue);
    if (ids.length > 0) data[key] = ids;
    return;
  }

  const id = toSingleMediaId(sourceValue);
  if (id !== null) data[key] = id;
}

function preserveComponentImagesByIndex(
  data: Record<string, any>,
  key: string,
  sourceRows: any[],
  imageField: string
) {
  const targetRows = data[key];
  if (!Array.isArray(targetRows) || !Array.isArray(sourceRows)) return;

  targetRows.forEach((row, index) => {
    if (!row || typeof row !== 'object') return;

    const currentImage = row[imageField];
    if (hasMediaAssigned(currentImage, false)) return;
    if (!isExplicitlyEmptyMedia(currentImage, false) && currentImage !== undefined) return;

    const sourceImage = sourceRows[index]?.[imageField];
    const sourceImageId = toSingleMediaId(sourceImage);
    if (sourceImageId !== null) row[imageField] = sourceImageId;
  });
}

async function resolveContext(
  event: any
): Promise<{ locale: string | null; documentId: string | null }> {
  const data = event?.params?.data ?? {};
  const where = event?.params?.where ?? {};

  let locale: string | null = data.locale ?? where.locale ?? null;
  let documentId: string | null = data.documentId ?? where.documentId ?? null;

  if ((!locale || !documentId) && where?.id) {
    const current = await strapi.db.query('api::tour-detalle.tour-detalle').findOne({
      where: { id: where.id },
      select: ['locale', 'documentId'],
    });

    locale = locale ?? current?.locale ?? null;
    documentId = documentId ?? current?.documentId ?? null;
  }

  return { locale, documentId };
}

async function preserveSharedImages(event: any, isCreate: boolean) {
  const data = event?.params?.data;
  if (!data || typeof data !== 'object') return;

  const { locale, documentId } = await resolveContext(event);
  if (!locale || !documentId) return;

  const siblingRows = await strapi.db.query('api::tour-detalle.tour-detalle').findMany({
    where: {
      documentId,
      locale: { $ne: locale },
    },
    populate: {
      heroSlideImages: true,
      ogImage: true,
      twitterImage: true,
      featuredImages: {
        populate: { image: true },
      },
      itineraryItems: {
        populate: { image: true },
      },
    },
  });

  const source = Array.isArray(siblingRows)
    ? siblingRows.find((row) => hasAnySharedImage(row)) ?? siblingRows[0]
    : null;
  if (!source) return;

  setDirectSharedMedia(data, 'heroSlideImages', source.heroSlideImages, {
    multiple: true,
    isCreate,
  });
  setDirectSharedMedia(data, 'ogImage', source.ogImage, {
    multiple: false,
    isCreate,
  });
  setDirectSharedMedia(data, 'twitterImage', source.twitterImage, {
    multiple: false,
    isCreate,
  });

  preserveComponentImagesByIndex(
    data,
    'featuredImages',
    Array.isArray(source.featuredImages) ? source.featuredImages : [],
    'image'
  );
  preserveComponentImagesByIndex(
    data,
    'itineraryItems',
    Array.isArray(source.itineraryItems) ? source.itineraryItems : [],
    'image'
  );
}

export default {
  async beforeCreate(event: any) {
    computeEndDate(event.params.data);
    await preserveSharedImages(event, true);
  },
  async beforeUpdate(event: any) {
    computeEndDate(event.params.data);
    await preserveSharedImages(event, false);
  },
};
