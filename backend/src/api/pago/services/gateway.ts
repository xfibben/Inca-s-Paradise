/**
 * Gateway de pagos unificado
 * Enruta las operaciones al adaptador correcto según el proveedor.
 * Al agregar un nuevo proveedor, solo se agrega su adaptador y un case aquí.
 */

import * as paypal from './paypal';
import * as izipay from './izipay';

export type Proveedor = 'paypal' | 'izipay_tarjeta' | 'izipay_yape';

/**
 * Inicia una intención de pago.
 * - PayPal       → devuelve { orderID }
 * - IziPay tarj. → devuelve { token }
 * - IziPay Yape  → devuelve { token, qrUrl, expiracion }
 */
export async function iniciarPago(
  proveedor: Proveedor,
  monto: number,
  moneda: string
): Promise<Record<string, string>> {
  switch (proveedor) {
    case 'paypal':
      return paypal.crearOrden(monto, moneda);

    case 'izipay_tarjeta':
      return izipay.crearTokenTarjeta(monto, moneda);

    case 'izipay_yape':
      return izipay.crearQrYape(monto);

    default:
      throw new Error(`Proveedor no soportado: ${proveedor}`);
  }
}

/**
 * Confirma y captura un pago aprobado.
 * - PayPal       → token = orderID del SDK
 * - IziPay       → token = token de la transacción
 * Devuelve { estado: 'pagado' | 'fallido', transaccionId }
 */
export async function confirmarPago(
  proveedor: Proveedor,
  token: string
): Promise<{ estado: string; transaccionId: string }> {
  switch (proveedor) {
    case 'paypal':
      return paypal.capturarOrden(token);

    case 'izipay_tarjeta':
    case 'izipay_yape':
      return izipay.verificarPago(token);

    default:
      throw new Error(`Proveedor no soportado: ${proveedor}`);
  }
}
