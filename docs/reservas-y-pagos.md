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
- `descuento`
- `vehiculo_seleccionado`
- `estado`
- `estado_pago`
- `ticket`
- relacion con `tour` o `transportes`
- relacion `oneToMany` con `pago`

Semantica actual:

- `descuento` en `reserva` se guarda como porcentaje
- `vehiculo_seleccionado` se guarda cuando la reserva es de transporte
- `precio_tour` guarda el total estimado del servicio ya con descuento aplicado
- `precio_adulto_web` y `precio_nino_web` guardan el adelanto web por tipo de pasajero
- `monto_web` se recalcula desde `precio_adulto_web + precio_nino_web`
- `monto_final` se recalcula desde `monto_web + pago_restante`

Estados relevantes:

- `estado`: `pendiente`, `confirmada`, `cancelada`
- `estado_pago`: `pendiente`, `pagado`, `fallido`, `pago_completo`

### Pago

Archivo:

- [backend/src/api/pago/content-types/pago/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/content-types/pago/schema.json)

Registra proveedor, metodo, moneda, monto, transaccion, orden y fecha de pago.

Semantica actual:

- `pago` no guarda descuento
- `pago.monto` guarda el monto efectivamente cobrado en la pasarela
- el descuento queda persistido en `reserva`, no en `pago`

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

Detalle importante:

- tours y transporte usan ahora `discount/descuento` como porcentaje
- el frontend calcula el total final aplicando ese porcentaje
- el valor porcentual tambien se persiste en `reserva.descuento`

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
- en el flujo de pago tambien se envia `descuento` hacia `reserva`
- en reservas de transporte tambien se persiste `vehiculo_seleccionado`

## Lifecycles de reserva

Archivo:

- [backend/src/api/reserva/content-types/reserva/lifecycles.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/content-types/reserva/lifecycles.ts)

Responsabilidades:

- calcular `monto_web`
- calcular `monto_final`
- mover `estado_pago` a `pago_completo` cuando corresponde
- sincronizar la reserva a Google Sheets en `afterCreate` y `afterUpdate`
- disparar envio de correos de reserva en `afterCreate`

Comportamiento actual del backend:

- si el frontend ya envia `precio_tour`, `precio_adulto_web`, `precio_nino_web` o `monto_estimado`, el controlador de `reserva` respeta esos valores
- esto evita recalculos incorrectos en transporte, donde el precio real depende del vehiculo elegido
- si esos valores no llegan, el backend usa fallback contra el modelo relacionado

## Correos de reserva

Archivo:

- [backend/src/utils/reserva-email.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/utils/reserva-email.ts)

Comportamiento:

- al crear una `reserva`, el backend envia 2 correos
- un correo va a `RESEND_NOTIFY_EMAIL`
- el otro va al `email` del cliente guardado en la reserva
- ambos correos adjuntan el PDF `comprobante-{ticket}.pdf`
- el envio corre desde el `afterCreate` de `reserva`, asi cubre reserva directa y reserva creada desde pago

Contenido actual del correo:

- encabezado con branding `INCA'S PARADISE`
- logo cargado desde `frontend/public/favicon.svg`
- secciones en tabla: datos del pasajero, datos de la reserva y resumen de pago
- `Tipo de servicio` usa:
  - `tourType` del `tour-detalle`: `Tour`, `Small Trip` o `Paquete`
  - `tipos_transporte[].nombre` del `transporte` cuando la reserva es de transporte
- el nombre del servicio es dinamico:
  - `Nombre del tour`
  - `Nombre del transporte`
- si la reserva es de transporte, el correo muestra `Vehículo seleccionado`

Datos usados:

- pasajero: nombre, email, telefono, tipo_documento, numero_documento, nacionalidad
- reserva: ticket, tipo de servicio, nombre del servicio, vehiculo, fechas, horario, cantidades, notas, estados
- pago: moneda, descuento, precio total, monto estimado, monto pagado en web, precio web por adulto y niño, saldo pendiente, monto final

Dependencias de datos:

- para transporte el lifecycle debe popular `transportes.tipos_transporte`
- para tours el campo usado es `tour.tourType`
- el PDF adjunto se genera en backend con `jspdf`

Variables de entorno:

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_NOTIFY_EMAIL`

Gotchas:

- `RESEND_FROM_EMAIL` debe usar un dominio verificado en Resend
- si el dominio verificado es `incasparadise.com`, usar por ejemplo `reservas@incasparadise.com`
- no usar `onboarding@resend.dev` fuera de pruebas iniciales
- en Docker, las variables de Resend deben estar declaradas en `docker-compose.yaml` y `docker-compose.prod.yaml`

## Descuentos

Estado actual:

- `tour-detalle.discount` se interpreta como porcentaje
- `transporte.precios[].descuento` se interpreta como porcentaje
- `reserva.descuento` se interpreta como porcentaje
- `pago` no tiene campo de descuento

Ejemplo:

- `adultUnitPrice = 10`
- `discount = 10`
- total unitario con descuento = `9`

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

Ajuste importante:

- la sincronizacion ya no intenta leer precios unitarios inexistentes desde `transporte`
- ahora deriva `precio_adulto` y `precio_nino` desde los montos web guardados en la reserva
- si la reserva es de transporte, tambien envia `vehiculo` a Google Sheets

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

## Riesgo residual

- si una reserva de transporte antigua fue creada antes de persistir `vehiculo_seleccionado`, el backend seguira usando el primer item de `transporte.precios` como fallback si necesita recomponer montos
