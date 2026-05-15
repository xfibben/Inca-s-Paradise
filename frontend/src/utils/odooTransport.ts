export type OdooTransportLang = "es" | "en" | "pt" | "fr" | "it";

export function getOdooTransportBaseUrl(): string {
  const internalUrl = import.meta.env.SSR ? import.meta.env.ODOO_URL : "";
  const publicUrl = import.meta.env.PUBLIC_ODOO_URL || "";
  return (internalUrl || publicUrl || "http://localhost:8069").replace(/\/$/, "");
}

export function getOdooDatabaseName(): string {
  return (import.meta.env.PUBLIC_ODOO_DB || import.meta.env.ODOO_DB_NAME || "").trim();
}

export function getOdooTransportLang(lang: string): OdooTransportLang {
  if (lang === "en" || lang === "pt" || lang === "fr" || lang === "it") return lang;
  return "es";
}

export function buildLocalizedSlugs(slug: string): Record<OdooTransportLang, string> {
  return {
    es: slug,
    en: slug,
    pt: slug,
    fr: slug,
    it: slug,
  };
}

export async function fetchOdooTransportJson(path: string) {
  const baseUrl = getOdooTransportBaseUrl();
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
