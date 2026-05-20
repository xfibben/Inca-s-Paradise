/**
 * tour-detalle controller
 */

import { factories } from '@strapi/strapi';

const TOUR_UID = 'api::tour-detalle.tour-detalle';
const DEFAULT_LOCALE = 'es-PE';
const DEFAULT_STATUS = 'published';
const EXPORT_FIELDS = [
  'title',
  'slug',
  'metaTitle',
  'metaDescription',
  'highlightsTitle',
  'highlightsLead',
  'tourType',
  'adultUnitPrice',
  'childUnitPrice',
  'discount',
  'durationDays',
  'publishedAt',
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

export default factories.createCoreController(TOUR_UID, ({ strapi }) => ({
  async exportCsv(ctx) {
    const locale =
      typeof ctx.query?.locale === 'string' && ctx.query.locale.trim()
        ? ctx.query.locale.trim()
        : DEFAULT_LOCALE;
    const status = normalizeStatus(ctx.query?.status ?? DEFAULT_STATUS);

    const tours = await strapi.documents(TOUR_UID).findMany({
      locale,
      status,
      sort: ['title:asc'],
      fields: EXPORT_FIELDS as any,
    });

    const headers = [
      'nombre',
      'slug',
      'tipo_tour',
      'precio_adulto',
      'precio_nino',
      'descuento',
      'dias',
      'ip',
      'meta_titulo',
      'meta_descripcion',
      'destacados_titulo',
      'destacados_lead',
      'active',
    ];

    const rows = (Array.isArray(tours) ? tours : []).map((tour: any) => [
      tour?.title ?? '',
      tour?.slug ?? '',
      tour?.tourType ?? 'tour',
      tour?.adultUnitPrice ?? '',
      tour?.childUnitPrice ?? '',
      tour?.discount ?? '',
      tour?.durationDays ?? '',
      'ip3',
      tour?.metaTitle ?? '',
      tour?.metaDescription ?? '',
      tour?.highlightsTitle ?? '',
      tour?.highlightsLead ?? '',
      tour?.publishedAt ? 'True' : 'False',
    ]);

    const csv = [
      headers.map(escapeCsvValue).join(','),
      ...rows.map((row) => row.map(escapeCsvValue).join(',')),
    ].join('\n');

    const safeLocale = locale.replace(/[^a-zA-Z0-9_-]/g, '_');
    const filename = `tours-odoo-${safeLocale}-${status}.csv`;

    ctx.set('Content-Type', 'text/csv; charset=utf-8');
    ctx.set('Content-Disposition', `attachment; filename="${filename}"`);
    ctx.body = `\uFEFF${csv}`;
  },
}));

