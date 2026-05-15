// File: src/pages/sitemap.xml.ts
// Genera un sitemap dinámico con todas las rutas del sitio

const baseUrl = "https://incasparadise.com";
const STRAPI_URL = import.meta.env.STRAPI_URL || "http://localhost:1337";
const ODOO_URL = (import.meta.env.PUBLIC_ODOO_URL || "").replace(/\/$/, "");
const langs = ["es", "en", "pt", "fr", "it"];

// Mapeo de lang a locale de Strapi
const langToLocale: Record<string, string> = {
  es: "es",
  en: "en",
  pt: "pt",
};

// Páginas estáticas por idioma
const staticPages = [
  { path: "/",                              changefreq: "weekly",  priority: "1.0" },
  { path: "/nosotros",                      changefreq: "monthly", priority: "0.7" },
  { path: "/destinos",                      changefreq: "monthly", priority: "0.8" },
  { path: "/tipo-transporte",               changefreq: "monthly", priority: "0.7" },
  { path: "/transporte",                    changefreq: "monthly", priority: "0.7" },
  { path: "/ofertas",                       changefreq: "weekly",  priority: "0.8" },
  { path: "/preguntas-frecuentes",          changefreq: "monthly", priority: "0.6" },
  { path: "/cancelaciones",                 changefreq: "yearly",  priority: "0.4" },
  { path: "/politicas",                     changefreq: "yearly",  priority: "0.4" },
  { path: "/claims",                        changefreq: "yearly",  priority: "0.4" },
  { path: "/terminos",                      changefreq: "yearly",  priority: "0.3" },
];

// Obtiene slugs de un endpoint filtrando por locale
async function fetchSlugsByLocale(endpoint: string, locale: string): Promise<string[]> {
  const slugs: string[] = [];
  let page = 1;
  const pageSize = 100;

  // Para español, probar es-PE primero y luego es como fallback
  const localeCandidates = locale === "es" ? ["es-PE", "es"] : [locale];

  for (const loc of localeCandidates) {
    const candidateSlugs: string[] = [];
    page = 1;

    while (true) {
      try {
        const res = await fetch(
          `${STRAPI_URL}/api/${endpoint}?locale=${encodeURIComponent(loc)}&fields[0]=slug&fields[1]=locale&pagination[page]=${page}&pagination[pageSize]=${pageSize}&status=published`
        );
        if (!res.ok) break;
        const json = await res.json();
        const items: any[] = json?.data ?? [];
        if (items.length === 0) break;

        for (const item of items) {
          const attrs = item?.attributes ?? item;
          const slug = attrs?.slug;
          const itemLocale = String(attrs?.locale ?? "").toLowerCase();
          const itemLangBase = itemLocale.split("-")[0];

          // Solo incluir si el locale del item coincide con el lang pedido
          if (slug && itemLangBase === locale) {
            candidateSlugs.push(slug);
          }
        }

        const total = json?.meta?.pagination?.total ?? 0;
        if (page * pageSize >= total) break;
        page++;
      } catch {
        break;
      }
    }

    if (candidateSlugs.length > 0) {
      slugs.push(...candidateSlugs);
      break; // Encontramos con este locale candidate, no seguir
    }
  }

  return slugs;
}

async function fetchOdooSlugs(path: string, lang: string): Promise<string[]> {
  if (!ODOO_URL) return [];
  try {
    const res = await fetch(`${ODOO_URL}${path}?lang=${encodeURIComponent(lang)}`);
    if (!res.ok) return [];
    const json = await res.json();
    const rows: any[] = json?.data ?? [];
    return rows
      .map((item: any) => item?.slug)
      .filter((slug: any): slug is string => typeof slug === "string" && Boolean(slug));
  } catch {
    return [];
  }
}

export async function GET() {
  // Obtener slugs por idioma en paralelo
  const endpoints = [
    { key: "tours",          path: "tour-detalles",    urlPath: "tours"          },
    { key: "destinos",       path: "destinos",          urlPath: "destinos"       },
    { key: "styleTrips",     path: "style-trips",       urlPath: "style-trips"    },
  ];

  // Obtener slugs por lang y endpoint
  const slugsByLangAndEndpoint: Record<string, Record<string, string[]>> = {};

  await Promise.all(
    langs.flatMap((lang) =>
      endpoints.map(async ({ key, path }) => {
        const locale = langToLocale[lang] ?? lang;
        const slugs = await fetchSlugsByLocale(path, locale);
        if (!slugsByLangAndEndpoint[lang]) slugsByLangAndEndpoint[lang] = {};
        slugsByLangAndEndpoint[lang][key] = slugs;
      })
    )
  );

  await Promise.all(
    langs.map(async (lang) => {
      if (!slugsByLangAndEndpoint[lang]) slugsByLangAndEndpoint[lang] = {};
      const [tipoTransporte, transporte] = await Promise.all([
        fetchOdooSlugs("/incas/api/web/tipo-transportes", lang),
        fetchOdooSlugs("/incas/api/web/transportes", lang),
      ]);
      slugsByLangAndEndpoint[lang].tipoTransporte = tipoTransporte;
      slugsByLangAndEndpoint[lang].transporte = transporte;
    })
  );

  const entries: string[] = [];
  const today = new Date().toISOString().split("T")[0];

  const addUrl = (loc: string, changefreq: string, priority: string) => {
    entries.push(`  <url>
    <loc>${loc}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
    <lastmod>${today}</lastmod>
  </url>`);
  };

  // Páginas estáticas por idioma
  for (const lang of langs) {
    for (const { path, changefreq, priority } of staticPages) {
      const loc = path === "/" ? `${baseUrl}/${lang}/` : `${baseUrl}/${lang}${path}`;
      addUrl(loc, changefreq, priority);
    }
  }

  // Páginas dinámicas: solo URLs donde el contenido existe en ese idioma
  for (const lang of langs) {
    const langSlugs = slugsByLangAndEndpoint[lang] ?? {};

    for (const slug of (langSlugs.tours ?? [])) {
      addUrl(`${baseUrl}/${lang}/tours/${slug}`, "weekly", "0.9");
    }
    for (const slug of (langSlugs.destinos ?? [])) {
      addUrl(`${baseUrl}/${lang}/destinos/${slug}`, "monthly", "0.8");
    }
    for (const slug of (langSlugs.styleTrips ?? [])) {
      addUrl(`${baseUrl}/${lang}/style-trips/${slug}`, "monthly", "0.7");
    }
    for (const slug of (langSlugs.tipoTransporte ?? [])) {
      addUrl(`${baseUrl}/${lang}/tipo-transporte/${slug}`, "monthly", "0.7");
    }
    for (const slug of (langSlugs.transporte ?? [])) {
      addUrl(`${baseUrl}/${lang}/transporte/${slug}`, "monthly", "0.7");
    }
  }

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
${entries.join("\n")}
</urlset>`;

  return new Response(sitemap, {
    headers: {
      "Content-Type": "application/xml",
      "Cache-Control": "max-age=3600",
    },
  });
}
