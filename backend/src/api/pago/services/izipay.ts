/**
 * Adaptador IziPay Vpos (Perú)
 * Documentación: https://secure.micuentaweb.pe/doc/es-PE/
 *
 * Cubre dos métodos de pago:
 *   - Tarjeta de crédito/débito (hosted fields / tokenización)
 *   - Yape QR (genera QR, polling de estado)
 *
 * TODO: Implementar cuando se obtengan las credenciales IziPay
 *   Variables de entorno necesarias:
 *     IZIPAY_SHOP_ID=...
 *     IZIPAY_SECRET_KEY=...
 *     IZIPAY_MODE=TEST  (o PRODUCTION)
 */

export async function crearTokenTarjeta(
  _monto: number,
  _moneda: string
): Promise<{ token: string }> {
  throw new Error('IziPay tarjeta: integración pendiente — agrega IZIPAY_SHOP_ID y IZIPAY_SECRET_KEY en .env');
}

export async function crearQrYape(
  _monto: number
): Promise<{ qrUrl: string; token: string; expiracion: string }> {
  throw new Error('IziPay Yape QR: integración pendiente — agrega IZIPAY_SHOP_ID y IZIPAY_SECRET_KEY en .env');
}

export async function verificarPago(
  _token: string
): Promise<{ estado: string; transaccionId: string }> {
  throw new Error('IziPay: integración pendiente');
}
