/**
 * Controlador de pagos
 * Orquesta el flujo: iniciar pago → confirmar pago → crear reserva → registrar pago
 */

import { factories } from '@strapi/strapi';
import { iniciarPago, confirmarPago, type Proveedor } from '../services/gateway';
import { verificarWebhook } from '../services/paypal';

// Caché en memoria del tipo de cambio — SBS actualiza una vez al día
let cacheTc: { PEN: number; EUR: number; cachedAt: number } | null = null;
const CACHE_TC_MS = 60 * 60 * 1000; // 1 hora

async function obtenerTipoCambio(): Promise<{ PEN: number; EUR: number }> {
  if (cacheTc && Date.now() - cacheTc.cachedAt < CACHE_TC_MS) {
    return { PEN: cacheTc.PEN, EUR: cacheTc.EUR };
  }

  const token = process.env.APIS_NET_PE_TOKEN ?? '';
  const hoy = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

  // USD/PEN desde SBS promedio
  let usdVenta = 3.75;
  try {
    const res = await fetch('https://apis.net.pe/v1/tipo-cambio/sbs/average', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json() as any;
      usdVenta = parseFloat(data.venta) || 3.75;
    }
  } catch {}

  // EUR/PEN desde SBS contable — divide para obtener EUR por USD
  let EUR = 0.92;
  try {
    const res = await fetch(
      `https://apis.net.pe/v1/tipo-cambio/sbs/accounting?date=${hoy}&currency=EUR`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (res.ok) {
      const data = await res.json() as any;
      const eurVenta = parseFloat(data.venta);
      if (eurVenta > 0) EUR = usdVenta / eurVenta; // cuántos EUR equivale 1 USD
    }
  } catch {}

  cacheTc = { PEN: usdVenta, EUR, cachedAt: Date.now() };
  return { PEN: usdVenta, EUR };
}

/**
 * Genera un ticket único para la reserva — mismo formato que en reserva.ts
 * Formato: TICKET-YYYYMMDD-XXXXX
 */
function generarTicket(): string {
  const fecha = new Date();
  const año = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  const aleatorio = String(Math.floor(Math.random() * 100000)).padStart(5, '0');
  return `TICKET-${año}${mes}${dia}-${aleatorio}`;
}

export default factories.createCoreController('api::pago.pago', ({ strapi }) => {
  return {

    /**
     * GET /api/pagos/tipo-cambio
     * Devuelve las tasas PEN y EUR respecto al USD.
     * PEN desde SBS vía apis.net.pe, EUR desde open.er-api.com.
     */
    async tipoCambio(ctx) {
      try {
        const rates = await obtenerTipoCambio();
        return ctx.send(rates);
      } catch (err: any) {
        strapi.log.error('[pago.tipoCambio]', err);
        return ctx.internalServerError('No se pudo obtener el tipo de cambio');
      }
    },

    /**
     * POST /api/pagos/iniciar
     * Crea la intención de pago con el proveedor.
     * Body: { proveedor, monto, moneda }
     * Response: { orderID } para PayPal | { token, qrUrl } para IziPay
     */
    async iniciar(ctx) {
      const { proveedor, monto, moneda } = ctx.request.body as {
        proveedor: Proveedor;
        monto: number;
        moneda: string;
      };

      strapi.log.info('[pago.iniciar] body recibido:', { proveedor, monto, moneda });
      if (!proveedor) return ctx.badRequest('Falta campo: proveedor');
      if (!monto || monto <= 0) return ctx.badRequest('Falta campo: monto (o es 0)');
      if (!moneda) return ctx.badRequest('Falta campo: moneda');

      try {
        const resultado = await iniciarPago(proveedor, Number(monto), moneda);
        return ctx.send(resultado);
      } catch (err: any) {
        strapi.log.error('[pago.iniciar]', err);
        return ctx.badRequest(err.message ?? 'Error al iniciar el pago');
      }
    },

    /**
     * POST /api/pagos/confirmar
     * Captura el pago aprobado, crea la reserva y registra el pago.
     * Body: { proveedor, token, reservaData: { ...campos de reserva, monto_total, moneda, metodo } }
     * Response: { ticket }
     */
    async confirmar(ctx) {
      const body = ctx.request.body as any;
      const { proveedor, token, reservaData } = body || {};

      if (!proveedor || !token || !reservaData) {
        strapi.log.error('[pago.confirmar] Falta campo:', { proveedor, token, reservaData });
        return ctx.badRequest('Se requieren: proveedor, token, reservaData');
      }

      try {
        // 1. Capturar el pago con el gateway
        const pagoResult = await confirmarPago(proveedor, token);

        if (pagoResult.estado !== 'pagado') {
          return ctx.badRequest('El pago no fue completado por el proveedor');
        }

        // 2. Extraer campos propios del pago antes de armar la reserva
        const { monto_total, monto_original, precio_tour, precio_adulto_web, precio_nino_web, moneda, metodo, ...datosReserva } = reservaData;

        // moneda_usuario = lo que eligió el usuario (PEN/USD/EUR)
        // moneda_cobro   = la moneda real cargada al proveedor (PayPal solo acepta USD)
        const monedaUsuario: string = moneda ?? 'USD';
        const monedaCobro: string = proveedor === 'paypal' ? 'USD' : monedaUsuario;

        // 3. Los montos web/agencia/final los calcula el lifecycle beforeCreate
        const montoEstimado = parseFloat(monto_original) || parseFloat(monto_total) / 0.3;

        // 4. Crear la reserva en Strapi con ticket ya generado
        //    publishedAt se incluye para que no quede en estado draft
        //    monto_final se calculará automáticamente en el lifecycle beforeCreate
        const ticket = generarTicket();
        // "as any" necesario: datosReserva viene de un payload dinámico del frontend
        const reserva = await (strapi.documents('api::reserva.reserva') as any).create({
          data: {
            ...datosReserva,
            ticket,
            moneda_usuario: monedaUsuario,
            precio_tour:       parseFloat(precio_tour)        || montoEstimado,
            precio_adulto_web: parseFloat(precio_adulto_web) || 0,
            precio_nino_web:   parseFloat(precio_nino_web)   || 0,
            monto_estimado:    montoEstimado,
            estado: 'confirmada',
            estado_pago: 'pagado',
            publishedAt: new Date().toISOString(),
          },
        });

        // Mapear proveedor interno al enum del schema de pago (izipay_tarjeta/yape → izipay)
        const proveedorSchema = proveedor === 'paypal' ? 'paypal' : 'izipay';

        // 4. Registrar el pago vinculado a la reserva
        // "as any" necesario: el tipo generado de Strapi no refleja la sintaxis set[] correctamente
        await (strapi.documents('api::pago.pago') as any).create({
          data: {
            reserva: { set: [{ documentId: reserva.documentId }] },
            proveedor: proveedorSchema,
            metodo: metodo ?? proveedor,
            moneda: monedaCobro,
            monto: monto_total ?? 0,
            estado: 'pagado',
            transaccion_id: pagoResult.transaccionId,
            orden_id: token,
            fecha_pago: new Date().toISOString(),
            ip_cliente: ctx.request.ip ?? null,
          },
        });

        strapi.log.info(`[pago.confirmar] Reserva creada: ${ticket} | Proveedor: ${proveedor} | Tx: ${pagoResult.transaccionId}`);

        return ctx.send({ ticket });

      } catch (err: any) {
        strapi.log.error('[pago.confirmar]', err);
        return ctx.internalServerError(err.message ?? 'Error al confirmar el pago');
      }
    },

    /**
     * POST /api/pagos/webhook
     * Recibe notificaciones asíncronas de PayPal / IziPay.
     * Útil para pagos QR donde la confirmación puede llegar después.
     */
    async webhook(ctx) {
      const body = JSON.stringify(ctx.request.body);
      const headers = ctx.request.headers as Record<string, string>;
      const proveedor = (ctx.request.body as any)?.proveedor
        ?? (headers['paypal-transmission-id'] ? 'paypal' : 'desconocido');

      strapi.log.info(`[pago.webhook] Notificación recibida de: ${proveedor}`);

      // Verificar firma de PayPal
      if (proveedor === 'paypal') {
        const valido = await verificarWebhook(headers, body).catch(() => false);
        if (!valido) {
          strapi.log.warn('[pago.webhook] Firma PayPal inválida — rechazando');
          return ctx.unauthorized('Firma de webhook inválida');
        }

        // Actualizar estado del pago si está registrado
        const evento = ctx.request.body as any;
        const orderID = evento?.resource?.id;

        if (orderID && evento?.event_type === 'CHECKOUT.ORDER.APPROVED') {
          const pagos = await strapi.documents('api::pago.pago').findMany({
            filters: { orden_id: { $eq: orderID } },
          }) as any[];

          for (const pago of pagos) {
            await strapi.documents('api::pago.pago').update({
              documentId: pago.documentId,
              data: { estado: 'pagado' } as any,
            });
          }
        }
      }

      // TODO: Agregar verificación y lógica para webhooks de IziPay aquí

      return ctx.send({ received: true });
    },
  };
});
