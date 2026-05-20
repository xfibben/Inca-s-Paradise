/**
 * tour-detalle controller
 */

import { factories } from '@strapi/strapi';

const TOUR_UID = 'api::tour-detalle.tour-detalle';
const DEFAULT_STATUS = 'published';
const DEFAULT_EXPORT_FORMAT = 'odoo';
const ODOO_LOCALE_CODES = {
  es: ['es-PE', 'es'],
  en: ['en-US', 'en'],
  pt: ['pt-BR', 'pt'],
};
const TOUR_BASE_FIELDS = [
  'documentId',
  'locale',
  'publishedAt',
  'tourType',
  'adultUnitPrice',
  'childUnitPrice',
  'discount',
  'durationDays',
  'title',
  'slug',
  'metaTitle',
  'metaDescription',
  'highlightsTitle',
  'highlightsLead',
];

const escapeCsvValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return '';
  }

  const text = String(value).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  return `"${text.replace(/"/g, '""')}"`;
};

const normalizeStatus = (status: unknown): 'draft' | 'published' => {
  return status === 'draft' ? 'draft' : 'published';
};

const normalizeFormat = (format: unknown): 'odoo' => {
  return format === 'odoo' ? 'odoo' : 'odoo';
};

const normalizeListJson = (items: unknown[]) => JSON.stringify(items);

const buildItineraryJson = (items: any[]) =>
  normalizeListJson(
    items.map((item, index) => ({
      orden: index + 1,
      titulo: item?.title ?? '',
      descripcion: item?.description ?? '',
    }))
  );

const buildHighlightsJson = (items: any[]) =>
  normalizeListJson(
    items.map((item, index) => ({
      orden: index + 1,
      titulo: item?.title ?? '',
      contenido: item?.description ?? '',
    }))
  );

const buildSimpleListJson = (items: any[]) =>
  normalizeListJson(
    items.map((item, index) => ({
      orden: index + 1,
      texto: item?.text ?? '',
    }))
  );

const getSafeFilename = (status: string) => `tours-odoo-${DEFAULT_EXPORT_FORMAT}-${status}.csv`;

const getPreferredLocale = (availableLocales: string[], candidates: string[]) => {
  for (const candidate of candidates) {
    if (availableLocales.includes(candidate)) {
      return candidate;
    }
  }

  return null;
};

const getLocalizedTourValue = (tourByLocale: Record<string, any>, localeCode: string | null) => {
  if (!localeCode) {
    return null;
  }

  return tourByLocale[localeCode] ?? null;
};

const getTourRow = (tourByLocale: Record<string, any>, localeCodes: Record<'es' | 'en' | 'pt', string | null>) => {
  const tourEs = getLocalizedTourValue(tourByLocale, localeCodes.es);
  const tourEn = getLocalizedTourValue(tourByLocale, localeCodes.en);
  const tourPt = getLocalizedTourValue(tourByLocale, localeCodes.pt);
  const baseTour = tourEs ?? tourEn ?? tourPt ?? {};
  const fallbackName = tourEs?.title ?? tourEn?.title ?? tourPt?.title ?? '';
  const fallbackSlug = tourEs?.slug ?? tourEn?.slug ?? tourPt?.slug ?? '';
  const fallbackMetaTitle = tourEs?.metaTitle ?? tourEn?.metaTitle ?? tourPt?.metaTitle ?? '';
  const fallbackMetaDescription = tourEs?.metaDescription ?? tourEn?.metaDescription ?? tourPt?.metaDescription ?? '';
  const fallbackHighlightsTitle =
    tourEs?.highlightsTitle ?? tourEn?.highlightsTitle ?? tourPt?.highlightsTitle ?? '';
  const fallbackHighlightsLead =
    tourEs?.highlightsLead ?? tourEn?.highlightsLead ?? tourPt?.highlightsLead ?? '';
  const fallbackHighlightsItems = Array.isArray(tourEs?.highlightsItems)
    ? tourEs.highlightsItems
    : Array.isArray(tourEn?.highlightsItems)
      ? tourEn.highlightsItems
      : Array.isArray(tourPt?.highlightsItems)
        ? tourPt.highlightsItems
        : [];
  const fallbackItinerary = Array.isArray(tourEs?.itineraryItems)
    ? tourEs.itineraryItems
    : Array.isArray(tourEn?.itineraryItems)
      ? tourEn.itineraryItems
      : Array.isArray(tourPt?.itineraryItems)
        ? tourPt.itineraryItems
        : [];
  const fallbackIncluded = Array.isArray(tourEs?.includedItems)
    ? tourEs.includedItems
    : Array.isArray(tourEn?.includedItems)
      ? tourEn.includedItems
      : Array.isArray(tourPt?.includedItems)
        ? tourPt.includedItems
        : [];
  const fallbackExcluded = Array.isArray(tourEs?.excludedItems)
    ? tourEs.excludedItems
    : Array.isArray(tourEn?.excludedItems)
      ? tourEn.excludedItems
      : Array.isArray(tourPt?.excludedItems)
        ? tourPt.excludedItems
        : [];

  return [
    fallbackName,
    tourEn?.title ?? '',
    tourPt?.title ?? '',
    baseTour?.tourType ?? 'tour',
    baseTour?.adultUnitPrice ?? '',
    baseTour?.childUnitPrice ?? '',
    baseTour?.discount ?? '',
    baseTour?.durationDays ?? '',
    'ip3',
    fallbackSlug,
    tourEn?.slug ?? '',
    tourPt?.slug ?? '',
    fallbackMetaTitle,
    tourEn?.metaTitle ?? '',
    tourPt?.metaTitle ?? '',
    fallbackMetaDescription,
    tourEn?.metaDescription ?? '',
    tourPt?.metaDescription ?? '',
    fallbackHighlightsTitle,
    tourEn?.highlightsTitle ?? '',
    tourPt?.highlightsTitle ?? '',
    fallbackHighlightsLead,
    tourEn?.highlightsLead ?? '',
    tourPt?.highlightsLead ?? '',
    buildHighlightsJson(fallbackHighlightsItems),
    buildHighlightsJson(Array.isArray(tourEn?.highlightsItems) ? tourEn.highlightsItems : []),
    buildHighlightsJson(Array.isArray(tourPt?.highlightsItems) ? tourPt.highlightsItems : []),
    buildItineraryJson(fallbackItinerary),
    buildItineraryJson(Array.isArray(tourEn?.itineraryItems) ? tourEn.itineraryItems : []),
    buildItineraryJson(Array.isArray(tourPt?.itineraryItems) ? tourPt.itineraryItems : []),
    buildSimpleListJson(fallbackIncluded),
    buildSimpleListJson(Array.isArray(tourEn?.includedItems) ? tourEn.includedItems : []),
    buildSimpleListJson(Array.isArray(tourPt?.includedItems) ? tourPt.includedItems : []),
    buildSimpleListJson(fallbackExcluded),
    buildSimpleListJson(Array.isArray(tourEn?.excludedItems) ? tourEn.excludedItems : []),
    buildSimpleListJson(Array.isArray(tourPt?.excludedItems) ? tourPt.excludedItems : []),
    baseTour?.publishedAt ? 'True' : 'False',
  ];
};

export default factories.createCoreController(TOUR_UID, ({ strapi }) => ({
  async exportCsv(ctx) {
    const status = normalizeStatus(ctx.query?.status ?? DEFAULT_STATUS);
    const format = normalizeFormat(ctx.query?.format ?? DEFAULT_EXPORT_FORMAT);

    if (format !== 'odoo') {
      ctx.throw(400, 'Formato de exportación no soportado');
      return;
    }

    const locales = await strapi.query('plugin::i18n.locale').findMany({
      orderBy: { id: 'asc' },
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
    const toursByDocument = new Map<string, Record<string, any>>();

    for (const localeCode of localesToExport) {
      const tours = await strapi.documents(TOUR_UID).findMany({
        locale: localeCode,
        status,
        sort: ['title:asc'],
        fields: TOUR_BASE_FIELDS as any,
        populate: {
          itineraryItems: {
            fields: ['title', 'description'] as any,
          },
          includedItems: {
            fields: ['text'] as any,
          },
          excludedItems: {
            fields: ['text'] as any,
          },
          highlightsItems: {
            fields: ['title', 'description'] as any,
          },
        } as any,
      });

      for (const tour of Array.isArray(tours) ? tours : []) {
        const documentId = tour?.documentId;
        if (!documentId) {
          continue;
        }

        const current = toursByDocument.get(documentId) ?? {};
        current[localeCode] = tour;
        toursByDocument.set(documentId, current);
      }
    }

    const headers = [
      'nombre',
      'nombre_en',
      'nombre_pt',
      'tipo_tour',
      'precio_adulto',
      'precio_nino',
      'descuento',
      'dias',
      'ip',
      'slug',
      'slug_en',
      'slug_pt',
      'meta_titulo',
      'meta_titulo_en',
      'meta_titulo_pt',
      'meta_descripcion',
      'meta_descripcion_en',
      'meta_descripcion_pt',
      'destacados_titulo',
      'destacados_titulo_en',
      'destacados_titulo_pt',
      'destacados_lead',
      'destacados_lead_en',
      'destacados_lead_pt',
      'destacados_items_import_json',
      'destacados_items_import_json_en',
      'destacados_items_import_json_pt',
      'itinerario_import_json',
      'itinerario_import_json_en',
      'itinerario_import_json_pt',
      'incluye_import_json',
      'incluye_import_json_en',
      'incluye_import_json_pt',
      'no_incluye_import_json',
      'no_incluye_import_json_en',
      'no_incluye_import_json_pt',
      'active',
    ];

    const rows = Array.from(toursByDocument.values())
      .sort((left, right) => {
        const leftTour = getLocalizedTourValue(left, localeCodes.es) ?? getLocalizedTourValue(left, localeCodes.en) ?? {};
        const rightTour = getLocalizedTourValue(right, localeCodes.es) ?? getLocalizedTourValue(right, localeCodes.en) ?? {};
        return String(leftTour?.title ?? '').localeCompare(String(rightTour?.title ?? ''));
      })
      .map((tourByLocale) => getTourRow(tourByLocale, localeCodes));

    const csv = [
      headers.map(escapeCsvValue).join(','),
      ...rows.map((row) => row.map(escapeCsvValue).join(',')),
    ].join('\n');

    ctx.set('Content-Type', 'text/csv; charset=utf-8');
    ctx.set('Content-Disposition', `attachment; filename="${getSafeFilename(status)}"`);
    ctx.body = `\uFEFF${csv}`;
  },
}));
