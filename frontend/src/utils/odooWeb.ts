export type OdooWebLang = "es" | "en" | "pt" | "fr" | "it";

export function getOdooWebBaseUrl(): string {
  const internalUrl = import.meta.env.SSR ? import.meta.env.ODOO_URL : "";
  const publicUrl = import.meta.env.PUBLIC_ODOO_URL || "";
  return (internalUrl || publicUrl || "http://localhost:8069").replace(/\/$/, "");
}

export function getOdooDatabaseName(): string {
  return (import.meta.env.PUBLIC_ODOO_DB || import.meta.env.ODOO_DB_NAME || "").trim();
}

export function getOdooWebLang(lang: string): OdooWebLang {
  if (lang === "en" || lang === "pt" || lang === "fr" || lang === "it") return lang;
  return "es";
}

export function buildLocalizedSlugs(slug: string): Record<OdooWebLang, string> {
  return {
    es: slug,
    en: slug,
    pt: slug,
    fr: slug,
    it: slug,
  };
}

export async function fetchOdooWebJson(path: string) {
  const baseUrl = getOdooWebBaseUrl();
  if (!baseUrl) {
    throw new Error("ODOO_URL no esta configurada");
  }
  const databaseName = getOdooDatabaseName();
  const headers: Record<string, string> = {};
  if (databaseName) {
    headers["X-Odoo-Database"] = databaseName;
  }
  const response = await fetch(`${baseUrl}${path}`, { headers });
  if (!response.ok) {
    throw new Error(`Error Odoo ${response.status}`);
  }
  return response.json();
}

export function getOdooMediaUrl(media: any): string | null {
  const url = typeof media === "string" ? media : media?.url;
  if (!url || typeof url !== "string") return null;
  const databaseName = getOdooDatabaseName();
  if (!databaseName) return url;
  try {
    const parsedUrl = new URL(url);
    if (parsedUrl.pathname === "/web/image" && !parsedUrl.searchParams.has("db")) {
      parsedUrl.searchParams.set("db", databaseName);
      return parsedUrl.toString();
    }
  } catch {
    return url;
  }
  return url;
}
