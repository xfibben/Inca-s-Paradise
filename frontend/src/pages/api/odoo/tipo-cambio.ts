import type { APIRoute } from "astro";

const getOdooUrl = () => {
  const value = import.meta.env.ODOO_URL || import.meta.env.PUBLIC_ODOO_URL || "";
  return value.replace(/\/$/, "");
};

const json = (status: number, payload: Record<string, unknown>) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });

export const GET: APIRoute = async () => {
  const odooUrl = getOdooUrl();

  if (!odooUrl) {
    return json(500, { error: { message: "ODOO_URL no esta configurada" } });
  }

  try {
    const response = await fetch(`${odooUrl}/incas/api/pagos/tipo-cambio`, {
      headers: {
        Accept: "application/json",
      },
    });

    const text = await response.text();

    return new Response(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return json(502, {
      error: {
        message: error instanceof Error ? error.message : "No se pudo consultar Odoo",
      },
    });
  }
};
