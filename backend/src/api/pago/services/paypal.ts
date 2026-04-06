/**
 * Adaptador PayPal REST API v2
 * Documentación: https://developer.paypal.com/api/rest/
 */

// URL base según entorno
const BASE_URL =
  process.env.PAYPAL_MODE === 'live'
    ? 'https://api-m.paypal.com'
    : 'https://api-m.sandbox.paypal.com';

/**
 * Obtiene un access token de PayPal usando Client Credentials
 */
async function getAccessToken(): Promise<string> {
  const clientId = process.env.PAYPAL_CLIENT_ID;
  const secret = process.env.PAYPAL_SECRET;

  if (!clientId || !secret) {
    throw new Error('PAYPAL_CLIENT_ID y PAYPAL_SECRET son requeridos en .env');
  }

  const credenciales = Buffer.from(`${clientId}:${secret}`).toString('base64');

  const res = await fetch(`${BASE_URL}/v1/oauth2/token`, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${credenciales}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'grant_type=client_credentials',
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Error obteniendo token PayPal: ${err}`);
  }

  const json = await res.json() as any;
  return json.access_token;
}

/**
 * Crea una orden de pago en PayPal
 * Retorna el orderID que el SDK del frontend necesita para abrir el popup
 */
export async function crearOrden(monto: number, moneda: string): Promise<{ orderID: string }> {
  const token = await getAccessToken();

  const res = await fetch(`${BASE_URL}/v2/checkout/orders`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      intent: 'CAPTURE',
      purchase_units: [
        {
          amount: {
            currency_code: moneda,
            value: monto.toFixed(2),
          },
        },
      ],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Error creando orden PayPal: ${err}`);
  }

  const json = await res.json() as any;
  return { orderID: json.id };
}

/**
 * Captura el pago de una orden aprobada por el usuario
 * Debe llamarse después de que el usuario aprueba en el popup de PayPal
 */
export async function capturarOrden(orderID: string): Promise<{ estado: string; transaccionId: string }> {
  const token = await getAccessToken();

  const res = await fetch(`${BASE_URL}/v2/checkout/orders/${orderID}/capture`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Error capturando orden PayPal: ${err}`);
  }

  const json = await res.json() as any;
  const capture = json.purchase_units?.[0]?.payments?.captures?.[0];

  return {
    estado: capture?.status === 'COMPLETED' ? 'pagado' : 'fallido',
    transaccionId: capture?.id ?? '',
  };
}

/**
 * Verifica la firma de un webhook de PayPal
 * Necesario para validar que la notificación realmente viene de PayPal
 * TODO: implementar verificación completa con PAYPAL-TRANSMISSION-SIG
 */
export async function verificarWebhook(headers: Record<string, string>, body: string): Promise<boolean> {
  const token = await getAccessToken();

  const res = await fetch(`${BASE_URL}/v1/notifications/verify-webhook-signature`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      auth_algo: headers['paypal-auth-algo'],
      cert_url: headers['paypal-cert-url'],
      transmission_id: headers['paypal-transmission-id'],
      transmission_sig: headers['paypal-transmission-sig'],
      transmission_time: headers['paypal-transmission-time'],
      webhook_id: process.env.PAYPAL_WEBHOOK_ID ?? '',
      webhook_event: JSON.parse(body),
    }),
  });

  if (!res.ok) return false;
  const json = await res.json() as any;
  return json.verification_status === 'SUCCESS';
}
