// File: src/pages/sitemap.xml.ts
// Genera un sitemap dinámico con todas las rutas del sitio

const baseUrl = "https://incasparadise.com";
const STRAPI_URL = import.meta.env.STRAPI_URL || "http://localhost:1337";
const langs = ["es", "en", "pt", "fr", "it"];

// Páginas estáticas por idioma
const staticPages = [
  { path: "/",                              changefreq: "weekly",  priority: "1.0" },
  { path: "/destinos",                      changefreq: "monthly", priority: "0.8" },
  { path: "/tipo-transporte",               changefreq: "monthly", priority: "0.7" },
  { path: "/transporte",                    changefreq: "monthly", priority: "0.7" },
  { path: "/ofertas",                       changefreq: "weekly",  priority: "0.8" },
  { path: "/claims",                        changefreq: "yearly",  priority: "0.4" },
  { path: "/terminos/terminos-condiciones", changefreq: "yearly",  priority: "0.3" },
];

// Obtiene slugs desde Strapi con paginación completa
async function fetchAllSlugs(endpoint: string, field = "slug"): Promise<string[]> {
  const slugs: string[] = [];
  let page = 1;
  const pageSize = 100;

  while (true) {
    try {
      const res = await fetch(
        `${STRAPI_URL}/api/${endpoint}?fields[0]=${field}&pagination[page]=${page}&pagination[pageSize]=${pageSize}&status=published`
      );
      if (!res.ok) break;
      const json = await res.json();
      const items: any[] = json?.data ?? [];
      if (items.length === 0) break;
      for (const item of items) {
        const slug = item?.[field] ?? item?.attributes?.[field];
        if (slug) slugs.push(slug);
      }
      const total = json?.meta?.pagination?.total ?? 0;
      if (page * pageSize >= total) break;
      page++;
    } catch {
      break;
    }
  }
  return slugs;
}

export async function GET() {
  // Obtener slugs dinámicos en paralelo
  const [tourSlugs, destinoSlugs, styleTripSlugs, tipoTransporteSlugs, transporteSlugs] =
    await Promise.all([
      fetchAllSlugs("tour-detalles"),
      fetchAllSlugs("destinos"),
      fetchAllSlugs("style-trips"),
      fetchAllSlugs("tipo-transportes"),
      fetchAllSlugs("transportes"),
    ]);

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

  // Tours
  for (const lang of langs) {
    for (const slug of tourSlugs) {
      addUrl(`${baseUrl}/${lang}/tours/${slug}`, "weekly", "0.9");
    }
  }

  // Destinos
  for (const lang of langs) {
    for (const slug of destinoSlugs) {
      addUrl(`${baseUrl}/${lang}/destinos/${slug}`, "monthly", "0.8");
    }
  }

  // Style trips
  for (const lang of langs) {
    for (const slug of styleTripSlugs) {
      addUrl(`${baseUrl}/${lang}/style-trips/${slug}`, "monthly", "0.7");
    }
  }

  // Tipo transporte
  for (const lang of langs) {
    for (const slug of tipoTransporteSlugs) {
      addUrl(`${baseUrl}/${lang}/tipo-transporte/${slug}`, "monthly", "0.7");
    }
  }

  // Transporte
  for (const lang of langs) {
    for (const slug of transporteSlugs) {
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
