import es from './es.json';
import en from './en.json';
import pt from './pt.json';
import fr from './fr.json';
import it from './it.json';

// Fallback translations if backend request fails
const fallbackTranslations = {
  es,
  en,
  pt,
  fr,
  it
};

// Fallback languages configuration - used for static build and sync access
// NOTA: Actualiza esto para coincidir con los idiomas configurados en tu Strapi
const fallbackLanguages = {
  es: 'Spanish',
  en: 'English',
  pt: 'Portuguese',
  fr: 'French',
  it: 'Italian'
};

// Export for Astro static paths and sync access
export const languages = fallbackLanguages;
export const defaultLanguage = 'es';

// Cache for languages fetched from backend
let cachedLanguages: Record<string, string> | null = null;
let languagesPromise: Promise<Record<string, string>> | null = null;

/**
 * Fetch available languages from backend
 * Falls back to hardcoded languages if backend is unavailable
 */
export async function fetchLanguagesFromBackend(): Promise<Record<string, string>> {
  // Return cached result if available
  if (cachedLanguages) {
    return cachedLanguages;
  }

  // Return existing promise if one is already in flight
  if (languagesPromise) {
    return languagesPromise;
  }

  languagesPromise = (async () => {
    try {
      const backendUrl = import.meta.env.PUBLIC_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/locales`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}`);
      }

      const data = await response.json();

      if (data.success && Array.isArray(data.data)) {
        // Transform backend response to our format
        // Map locale codes to short codes (es-PE -> es, en-US -> en, etc.)
        cachedLanguages = data.data.reduce((acc: Record<string, string>, locale: { code: string; name: string }) => {
          // Get the short code (first part before hyphen)
          const shortCode = locale.code.split('-')[0];
          acc[shortCode] = locale.name;
          return acc;
        }, {});

        return cachedLanguages;
      }

      throw new Error('Invalid response format from backend');
    } catch (error) {
      console.warn('Failed to fetch languages from backend, using fallback:', error);
      // Use fallback languages if backend fails
      cachedLanguages = fallbackLanguages;
      return cachedLanguages;
    }
  })();

  return languagesPromise;
}

/**
 * Get languages synchronously (uses fallback if async fetch hasn't completed)
 */
export function getLanguagesSync(): Record<string, string> {
  return cachedLanguages || fallbackLanguages;
}

/**
 * Get all available languages
 */
export async function getLanguages(): Promise<Record<string, string>> {
  return fetchLanguagesFromBackend();
}

export const translations = fallbackTranslations;

export function getTranslation(lang: string) {
  // Map short language codes to their corresponding translations
  const translationMap: Record<string, any> = {
    es,
    en,
    pt,
    fr,
    it
  };
  
  // Get the short code (first part before hyphen)
  const shortCode = lang.split('-')[0];
  const translation = translationMap[shortCode];
  
  return translation || es; // Fallback to Spanish
}

export type Language = keyof typeof fallbackTranslations;
