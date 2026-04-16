import type { APIRoute } from 'astro';

const GOOGLE_FORM_URL = import.meta.env.PUBLIC_GOOGLE_CLAIMS_FORM_URL;
const RECAPTCHA_SECRET_KEY = import.meta.env.RECAPTCHA_SECRET_KEY;

const json = (status: number, payload: Record<string, unknown>) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });

const asText = (value: unknown) => (typeof value === 'string' ? value.trim() : '');

const requiredFields = [
  'doc_type',
  'doc_number',
  'nombres',
  'apellido_paterno',
  'address',
  'departamento_name',
  'provincia_name',
  'distrito_name',
  'email',
  'product_type',
  'product_desc',
  'complaint_type',
  'complaint_detail',
  'complaint_request',
] as const;

const getClientIp = (request: Request) => {
  const forwardedFor = request.headers.get('x-forwarded-for');
  if (forwardedFor) {
    return forwardedFor.split(',')[0]?.trim();
  }
  return request.headers.get('x-real-ip')?.trim() || '';
};

export const POST: APIRoute = async ({ request }) => {
  if (!GOOGLE_FORM_URL) {
    return json(500, { ok: false, message: 'Claims form destination is not configured.' });
  }
  if (!RECAPTCHA_SECRET_KEY) {
    return json(500, { ok: false, message: 'reCAPTCHA secret is not configured.' });
  }

  let payload: Record<string, unknown>;
  try {
    payload = (await request.json()) as Record<string, unknown>;
  } catch {
    return json(400, { ok: false, message: 'Invalid request payload.' });
  }

  const missing = requiredFields.filter((field) => !asText(payload[field]));
  if (missing.length > 0) {
    return json(400, { ok: false, message: 'Missing required fields.' });
  }

  const recaptchaToken = asText(payload.recaptchaToken);
  if (!recaptchaToken) {
    return json(400, { ok: false, message: 'reCAPTCHA token is required.' });
  }

  const verifyParams = new URLSearchParams({
    secret: RECAPTCHA_SECRET_KEY,
    response: recaptchaToken,
  });

  const clientIp = getClientIp(request);
  if (clientIp) {
    verifyParams.set('remoteip', clientIp);
  }

  try {
    const recaptchaResponse = await fetch('https://www.google.com/recaptcha/api/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: verifyParams.toString(),
    });

    if (!recaptchaResponse.ok) {
      return json(502, { ok: false, message: 'Unable to verify reCAPTCHA.' });
    }

    const recaptchaResult = (await recaptchaResponse.json()) as {
      success?: boolean;
      'error-codes'?: string[];
    };

    if (!recaptchaResult.success) {
      return json(403, { ok: false, message: 'reCAPTCHA verification failed.' });
    }

    const params = new URLSearchParams({
      'entry.34363557': `${asText(payload.doc_type)} ${asText(payload.doc_number)}`.trim(),
      'entry.1700475525': asText(payload.nombres),
      'entry.823207103': asText(payload.apellido_paterno),
      'entry.508125324': asText(payload.apellido_materno),
      'entry.978743635': asText(payload.address),
      'entry.904037755': asText(payload.departamento_name),
      'entry.25894838': asText(payload.provincia_name),
      'entry.54830945': asText(payload.distrito_name),
      'entry.1649899907': asText(payload.email),
      'entry.1312334274': asText(payload.phone),
      'entry.125927942': asText(payload.product_type) === 'producto' ? 'Producto' : 'Servicio',
      'entry.965895874': asText(payload.product_desc),
      'entry.1563953750': asText(payload.product_amount),
      'entry.1797108586': asText(payload.ticket),
      'entry.21788407': asText(payload.complaint_type) === 'reclamo' ? 'Reclamo' : 'Queja',
      'entry.494423353': asText(payload.complaint_detail),
      'entry.1705114830': asText(payload.complaint_request),
    });

    const submitResponse = await fetch(GOOGLE_FORM_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });

    if (!submitResponse.ok) {
      return json(502, { ok: false, message: 'Unable to submit the claim form.' });
    }

    return json(200, { ok: true });
  } catch {
    return json(500, { ok: false, message: 'Unexpected error while processing the claim form.' });
  }
};
