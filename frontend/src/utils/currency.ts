// Configuración de divisas por idioma
// Los precios base en Strapi están en USD
const CURRENCY_CONFIG: Record<string, { symbol: string; code: string; rate: number }> = {
  es: { symbol: 'S/', code: 'PEN', rate: 3.70 },
  en: { symbol: '$',  code: 'USD', rate: 1.00 },
  pt: { symbol: '$',  code: 'USD', rate: 1.00 },
  fr: { symbol: '€',  code: 'EUR', rate: 0.92 },
  it: { symbol: '€',  code: 'EUR', rate: 0.92 },
};

const DEFAULT = CURRENCY_CONFIG['en'];

// Devuelve símbolo, código y tasa de conversión para el idioma dado
export function getCurrencyConfig(lang: string) {
  return CURRENCY_CONFIG[lang] ?? DEFAULT;
}

// Convierte un monto USD al idioma dado y lo formatea
export function formatPrice(usdAmount: number, lang: string): string {
  const cfg = getCurrencyConfig(lang);
  const converted = usdAmount * cfg.rate;
  // Sin decimales para PEN, con 2 para el resto
  const formatted = cfg.code === 'PEN'
    ? converted.toFixed(0)
    : converted.toFixed(2);
  return `${cfg.symbol} ${formatted}`;
}
