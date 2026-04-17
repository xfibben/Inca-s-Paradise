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

const STATIC_EXT_RE = /\.(?:css|js|mjs|map|png|jpg|jpeg|webp|avif|gif|svg|ico|woff|woff2|ttf|eot|mp4|webm)$/i;

function applyCacheHeaders(pathname: string, response: Response): void {
  if (response.headers.has('Cache-Control')) return;

  if (pathname.startsWith('/_astro/')) {
    response.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    return;
  }

  if (STATIC_EXT_RE.test(pathname)) {
    response.headers.set('Cache-Control', 'public, max-age=2592000, stale-while-revalidate=604800');
    return;
  }

  const isLandingPage =
    pathname === '/' ||
    /^\/(?:es|en|pt|fr|it)\/?$/.test(pathname);

  if (isLandingPage) {
    response.headers.set('Cache-Control', 'no-store');
    return;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('text/html')) {
    // CDN/shared cache corto para HTML, con stale para evitar picos de latencia.
    response.headers.set('Cache-Control', 'public, max-age=0, s-maxage=300, stale-while-revalidate=86400');
  }
}

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url;

  // Obtener el primer segmento de la ruta (ej: "es-PE" de "/es-PE/style-trips/...")
  const segments = pathname.split('/').filter(Boolean);
  const firstSegment = segments[0]?.toLowerCase();

  if (firstSegment) {
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
  }

  const response = await next();

  if (context.request.method === 'GET' || context.request.method === 'HEAD') {
    applyCacheHeaders(pathname, response);
  }

  return response;
});
