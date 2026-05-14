import type { APIRoute } from "astro";
import http from "node:http";
import https from "node:https";

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

const requestText = (target: URL, publicHost?: string) =>
  new Promise<{ status: number; body: string; contentType: string }>((resolve, reject) => {
    const transport = target.protocol === "https:" ? https : http;
    const req = transport.request(
      target,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...(publicHost
            ? {
                Host: publicHost,
                "X-Forwarded-Host": publicHost,
                "X-Forwarded-Proto": "https",
              }
            : {}),
        },
      },
      (res) => {
        let body = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          resolve({
            status: res.statusCode || 500,
            body,
            contentType: res.headers["content-type"] || "application/json; charset=utf-8",
          });
        });
      },
    );
    req.on("error", reject);
    req.end();
  });

export const GET: APIRoute = async () => {
  const odooUrl = getOdooUrl();
  const publicOdooUrl = (import.meta.env.PUBLIC_ODOO_URL || "").replace(/\/$/, "");

  if (!odooUrl) {
    return json(500, { error: { message: "ODOO_URL no esta configurada" } });
  }

  try {
    const target = new URL(`${odooUrl}/incas/api/pagos/tipo-cambio`);
    const publicHost = publicOdooUrl ? new URL(publicOdooUrl).host : undefined;
    const response = await requestText(target, publicHost);

    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": response.contentType,
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
