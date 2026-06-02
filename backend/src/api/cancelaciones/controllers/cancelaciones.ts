import { factories } from '@strapi/strapi';

const UID = 'api::cancelaciones.cancelaciones';
const DEFAULT_STATUS = 'published';
const ODOO_LOCALE_CODES = {
  es: ['es-PE', 'es'],
  en: ['en-US', 'en'],
  pt: ['pt-BR', 'pt'],
};

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

const getPreferredLocale = (availableLocales: string[], candidates: string[]) => {
  for (const candidate of candidates) {
    if (availableLocales.includes(candidate)) {
      return candidate;
    }
  }

  return null;
};

const buildSectionsJson = (items: any[]) =>
  JSON.stringify(
    items.map((item, index) => ({
      orden: index + 1,
      titulo: item?.titulo ?? '',
      contenido: item?.contenido ?? '',
    }))
  );

export default factories.createCoreController(UID, ({ strapi }) => ({
  async exportCsv(ctx) {
    const status = normalizeStatus(ctx.query?.status ?? DEFAULT_STATUS);
    const locales = await strapi.query('plugin::i18n.locale').findMany({
      orderBy: { id: 'asc' },
    } as any);
    const availableLocaleCodes = locales.map((item: { code: string }) => item.code);
    const localeCodes = {
      es: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.es),
      en: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.en),
      pt: getPreferredLocale(availableLocaleCodes, ODOO_LOCALE_CODES.pt),
    };

    const getEntry = async (localeCode: string | null): Promise<any> => {
      if (!localeCode) {
        return null;
      }
      return await strapi.documents(UID).findFirst({
        locale: localeCode,
        status,
        fields: ['titulo', 'descripcion', 'metaTitle', 'metaDescription', 'publishedAt'] as any,
        populate: {
          secciones: true as any,
        } as any,
      });
    };

    const es: any = await getEntry(localeCodes.es);
    const en: any = await getEntry(localeCodes.en);
    const pt: any = await getEntry(localeCodes.pt);

    const headers = [
      'titulo',
      'titulo_en',
      'titulo_pt',
      'descripcion',
      'descripcion_en',
      'descripcion_pt',
      'meta_titulo',
      'meta_titulo_en',
      'meta_titulo_pt',
      'meta_descripcion',
      'meta_descripcion_en',
      'meta_descripcion_pt',
      'secciones_json',
      'secciones_json_en',
      'secciones_json_pt',
      'activo',
    ];

    const row = [
      es?.titulo ?? '',
      en?.titulo ?? '',
      pt?.titulo ?? '',
      JSON.stringify(es?.descripcion ?? ''),
      JSON.stringify(en?.descripcion ?? ''),
      JSON.stringify(pt?.descripcion ?? ''),
      es?.metaTitle ?? '',
      en?.metaTitle ?? '',
      pt?.metaTitle ?? '',
      es?.metaDescription ?? '',
      en?.metaDescription ?? '',
      pt?.metaDescription ?? '',
      buildSectionsJson(Array.isArray(es?.secciones) ? es.secciones : []),
      buildSectionsJson(Array.isArray(en?.secciones) ? en.secciones : []),
      buildSectionsJson(Array.isArray(pt?.secciones) ? pt.secciones : []),
      es?.publishedAt ? 'True' : 'False',
    ];

    const csv = [headers.map(escapeCsvValue).join(','), row.map(escapeCsvValue).join(',')].join('\n');
    ctx.set('Content-Type', 'text/csv; charset=utf-8');
    ctx.set('Content-Disposition', `attachment; filename="cancelaciones-odoo-${status}.csv"`);
    ctx.body = csv;
  },
}));
