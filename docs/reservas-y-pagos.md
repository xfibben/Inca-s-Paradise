# Reservas y pagos

## Resumen

El proyecto usa un flujo de reserva con pago previo parcial. El usuario completa sus datos en el frontend, elige metodo de pago y el backend crea la reserva confirmada cuando el cobro se valida.

## Modelos principales

### Reserva

Archivo:

- [backend/src/api/reserva/content-types/reserva/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/content-types/reserva/schema.json)

Campos clave:

- datos del pasajero
- fechas
- cantidades de pasajeros
- precios y montos
- `estado`
- `estado_pago`
- `ticket`
- relacion con `tour` o `transportes`
- relacion `oneToMany` con `pago`

Estados relevantes:

- `estado`: `pendiente`, `confirmada`, `cancelada`
- `estado_pago`: `pendiente`, `pagado`, `fallido`, `pago_completo`

### Pago

Archivo:

- [backend/src/api/pago/content-types/pago/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/content-types/pago/schema.json)

Registra proveedor, metodo, moneda, monto, transaccion, orden y fecha de pago.

## Flujo frontend

Archivo principal:

- [frontend/src/components/tours/BookingModal.astro](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/components/tours/BookingModal.astro)

Secuencia:

1. El usuario completa el formulario de reserva.
2. El frontend guarda la reserva pendiente en `window.__pendingBooking`.
3. El usuario pasa al paso de pago.
4. Se cobra actualmente el `30%` de adelanto.
5. Si usa PayPal:
   - el frontend llama `POST /api/pagos/iniciar`
   - PayPal devuelve `orderID`
   - al aprobar, el frontend llama `POST /api/pagos/confirmar`
6. El backend captura el pago, crea la reserva y registra el pago.
7. El frontend muestra el ticket y permite descargar comprobante.

## Rutas custom de pago

Archivo:

- [backend/src/api/pago/routes/pago-custom.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/routes/pago-custom.ts)

Endpoints:

- `POST /api/pagos/iniciar`
- `POST /api/pagos/confirmar`
- `POST /api/pagos/webhook`
- `GET /api/pagos/tipo-cambio`

## Gateway unificado

Archivo:

- [backend/src/api/pago/services/gateway.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/services/gateway.ts)

Proveedores:

- `paypal`
- `izipay_tarjeta`
- `izipay_yape`

## PayPal

Archivo:

- [backend/src/api/pago/services/paypal.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/services/paypal.ts)

Estado:

- Implementado
- Usa REST API v2
- Requiere `PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`, `PAYPAL_MODE`, `PAYPAL_WEBHOOK_ID`

Punto importante:

- PayPal no acepta `PEN` en este flujo del proyecto, por eso el backend y frontend trabajan con conversion a `USD`

## IziPay

Archivo:

- [backend/src/api/pago/services/izipay.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/services/izipay.ts)

Estado:

- Pendiente
- Solo existe skeleton
- Faltan credenciales y logica de integracion

Variables previstas:

- `IZIPAY_SHOP_ID`
- `IZIPAY_SECRET_KEY`
- `IZIPAY_MODE`

## Tipo de cambio

Archivo:

- [backend/src/api/pago/controllers/pago.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/controllers/pago.ts)

Comportamiento:

- `GET /api/pagos/tipo-cambio` devuelve tasas respecto a USD
- Usa cache en memoria por 1 hora
- Consulta `apis.net.pe`

## Creacion de reserva

Archivo:

- [backend/src/api/pago/controllers/pago.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/controllers/pago.ts)

Puntos clave:

- El ticket se genera en backend
- Se crea la `reserva` con `publishedAt` para evitar draft
- `estado` queda en `confirmada`
- `estado_pago` queda en `pagado`
- Luego se crea el registro en `pago`

## Lifecycles de reserva

Archivo:

- [backend/src/api/reserva/content-types/reserva/lifecycles.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/content-types/reserva/lifecycles.ts)

Responsabilidades:

- calcular `monto_web`
- calcular `monto_final`
- mover `estado_pago` a `pago_completo` cuando corresponde
- sincronizar la reserva a Google Sheets en `afterCreate` y `afterUpdate`

## Google Sheets

La sincronizacion depende de:

- `GOOGLE_APPS_SCRIPT_URL`

Archivo relacionado:

- [backend/src/api/reserva/controllers/reserva.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/controllers/reserva.ts)

Ruta auxiliar:

- `POST /api/reservas/sync-sheets`

Uso:

- Reenvia reservas existentes a Sheets
- Sirve para recuperacion operativa si hubo fallos de sincronizacion

## Operacion del negocio

### Si un cliente pago y no aparece en Sheets

1. Buscar la reserva en Strapi.
2. Validar `estado_pago` y `ticket`.
3. Ejecutar la sincronizacion manual si hace falta.

### Si el cliente no completo el pago

- No deberia existir una reserva confirmada por el flujo normal de pago.
- Revisar si el proveedor devolvio error o si el usuario abandono el popup.

### Si el pago fue total

- El lifecycle puede mover `estado_pago` a `pago_completo` cuando `monto_final >= precio_tour`.
