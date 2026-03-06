import es from './es.json';
import en from './en.json';
import pt from './pt.json';

export const languages = {
  es: 'Español',
  en: 'English',
  pt: 'Português'
};

export const defaultLanguage = 'es';

const translations = {
  es,
  en,
  pt
};

export function getTranslation(lang: string) {
  return translations[lang as keyof typeof translations] || translations.es;
}

export type Language = keyof typeof translations;
