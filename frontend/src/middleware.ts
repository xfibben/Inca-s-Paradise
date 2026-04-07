import { defineMiddleware } from 'astro:middleware';

// Idiomas válidos del sitio
const VALID_LANGS = ['es', 'en', 'pt', 'fr', 'it'];

// Mapeo de locales de Strapi/browser a idiomas del sitio
const LANG_REDIRECTS: Record<string, string> = {
  'es-pe': 'es',
  'es-ar': 'es',
  'es-mx': 'es',
  'en-us': 'en',
  'en-gb': 'en',
  'pt-br': 'pt',
  'fr-fr': 'fr',
  'it-it': 'it',
};

// URLs antiguas que cambiaron de ruta → nueva ruta (sin el prefijo de idioma)
const PATH_REDIRECTS: Record<string, string> = {
  'terminos/terminos-condiciones': 'terminos',
};

export const onRequest = defineMiddleware((context, next) => {
  const { pathname } = context.url;

  // Obtener el primer segmento de la ruta (ej: "es-PE" de "/es-PE/style-trips/...")
  const segments = pathname.split('/').filter(Boolean);
  const firstSegment = segments[0]?.toLowerCase();

  if (!firstSegment) return next();

  // Redirigir URLs antiguas que cambiaron de ruta
  if (VALID_LANGS.includes(firstSegment)) {
    const restPath = segments.slice(1).join('/');
    const newRestPath = PATH_REDIRECTS[restPath];
    if (newRestPath) {
      return context.redirect(`/${firstSegment}/${newRestPath}`, 301);
    }
  }

  // Si el primer segmento es un locale inválido que tiene mapeo, redirigir
  const mapped = LANG_REDIRECTS[firstSegment];
  if (mapped) {
    const rest = segments.slice(1).join('/');
    const newPath = rest ? `/${mapped}/${rest}` : `/${mapped}/`;
    return context.redirect(newPath, 301);
  }

  // Si el primer segmento parece un lang pero no es válido, devolver 404
  // (solo si tiene formato de idioma: 2-5 letras)
  if (/^[a-z]{2}(-[a-z]{2,4})?$/.test(firstSegment) && !VALID_LANGS.includes(firstSegment)) {
    return new Response('Not found', { status: 404 });
  }

  return next();
});
