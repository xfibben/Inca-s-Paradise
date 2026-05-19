const baseUrl = "https://incasparadise.com";
const ODOO_URL = (import.meta.env.PUBLIC_ODOO_URL || "").replace(/\/$/, "");
const langs = ["es", "en", "pt", "fr", "it"];

const staticPages = [
  { path: "/", changefreq: "weekly", priority: "1.0" },
  { path: "/nosotros", changefreq: "monthly", priority: "0.7" },
  { path: "/destinos", changefreq: "monthly", priority: "0.8" },
  { path: "/tipo-transporte", changefreq: "monthly", priority: "0.7" },
  { path: "/transporte", changefreq: "monthly", priority: "0.7" },
  { path: "/ofertas", changefreq: "weekly", priority: "0.8" },
  { path: "/preguntas-frecuentes", changefreq: "monthly", priority: "0.6" },
  { path: "/cancelaciones", changefreq: "yearly", priority: "0.4" },
  { path: "/politicas", changefreq: "yearly", priority: "0.4" },
  { path: "/claims", changefreq: "yearly", priority: "0.4" },
  { path: "/terminos", changefreq: "yearly", priority: "0.3" },
];

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
  const slugsByLangAndEndpoint: Record<string, Record<string, string[]>> = {};

  await Promise.all(
    langs.map(async (lang) => {
      if (!slugsByLangAndEndpoint[lang]) slugsByLangAndEndpoint[lang] = {};
      const [tours, destinos, styleTrips, tipoTransporte, transporte] = await Promise.all([
        fetchOdooSlugs("/incas/api/web/tours", lang),
        fetchOdooSlugs("/incas/api/web/destinos", lang),
        fetchOdooSlugs("/incas/api/web/estilos-viaje", lang),
        fetchOdooSlugs("/incas/api/web/tipo-transportes", lang),
        fetchOdooSlugs("/incas/api/web/transportes", lang),
      ]);
      slugsByLangAndEndpoint[lang].tours = tours;
      slugsByLangAndEndpoint[lang].destinos = destinos;
      slugsByLangAndEndpoint[lang].styleTrips = styleTrips;
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

  for (const lang of langs) {
    for (const { path, changefreq, priority } of staticPages) {
      const loc = path === "/" ? `${baseUrl}/${lang}/` : `${baseUrl}/${lang}${path}`;
      addUrl(loc, changefreq, priority);
    }
  }

  for (const lang of langs) {
    const langSlugs = slugsByLangAndEndpoint[lang] ?? {};
    for (const slug of langSlugs.tours ?? []) addUrl(`${baseUrl}/${lang}/tours/${slug}`, "weekly", "0.9");
    for (const slug of langSlugs.destinos ?? []) addUrl(`${baseUrl}/${lang}/destinos/${slug}`, "monthly", "0.8");
    for (const slug of langSlugs.styleTrips ?? []) addUrl(`${baseUrl}/${lang}/style-trips/${slug}`, "monthly", "0.7");
    for (const slug of langSlugs.tipoTransporte ?? []) addUrl(`${baseUrl}/${lang}/tipo-transporte/${slug}`, "monthly", "0.7");
    for (const slug of langSlugs.transporte ?? []) addUrl(`${baseUrl}/${lang}/transporte/${slug}`, "monthly", "0.7");
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
