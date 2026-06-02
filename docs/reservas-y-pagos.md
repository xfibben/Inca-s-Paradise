# Reservas y pagos

## 1. Resumen

El flujo actual de venta vive en `frontend + Odoo`.

Frontend:

- captura datos
- muestra precios
- inicia pago

Odoo:

- valida servicio
- crea reserva
- registra pago
- genera ticket
- genera voucher
- dispara correo y sincronización

## 2. Archivos críticos

### Frontend

- `frontend/src/components/tours/BookingCard.astro`
- `frontend/src/components/tours/BookingModal.astro`
- `frontend/src/components/tours/voucher-pdf.ts`

### Odoo

- `odoo/addons/incas_reservas/controllers/api.py`
- `odoo/addons/incas_reservas/models/incas_reserva.py`
- `odoo/addons/incas_reservas/models/incas_pago.py`
- `odoo/addons/incas_reservas/controllers/main.py`

## 3. Endpoints

- `GET /incas/api/pagos/tipo-cambio`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`
- `POST /incas/api/reservas`
- `GET /incas/public/reserva/<id>/pdf/<token>`

## 4. Flujo de reserva directa

Caso:

- tarjeta/directo sin popup PayPal

Secuencia:

1. usuario llena modal.
2. frontend arma `window.__pendingBooking`.
3. frontend manda `POST /incas/api/reservas`.
4. Odoo ejecuta `crear_reserva_web`.
5. Odoo devuelve `ticket`, `reserva_id`, `voucher_url`.
6. frontend abre el comprobante.

## 5. Flujo PayPal

Secuencia:

1. frontend calcula monto a cobrar.
2. llama `POST /incas/api/pagos/iniciar`.
3. Odoo crea orden PayPal.
4. usuario aprueba en PayPal.
5. frontend llama `POST /incas/api/pagos/confirmar`.
6. Odoo captura orden.
7. Odoo crea reserva y pago.
8. Odoo devuelve `ticket`, `voucher_url`.

## 6. Payload funcional mínimo

### Desde frontend a Odoo

Reserva:

- `serviceId`
- `tourSlug` o `transporteSlug`
- `tipo_servicio`
- `nombre`
- `email`
- `telefono`
- `tipo_documento`
- `numero_documento`
- `nacionalidad`
- `fecha_inicio`
- `fecha_fin`
- `turno`
- `cantidad_adultos`
- `cantidad_ninos`
- `moneda`
- `descuento`
- `vehiculo_seleccionado` si aplica

Pago:

- `proveedor`
- `metodo`
- `moneda`
- `monto`
- `estado`
- `orden_id` o `transaccion_id`

## 7. Reglas de precios

- precios base de catálogo en `USD`
- descuento porcentual
- Odoo convierte a moneda elegida
- para transporte la tarifa depende del vehículo
- frontend muestra conversión visual
- Odoo define el dato persistido final

## 8. `incas.reserva`

### Qué guarda

- cliente
- servicio
- idioma
- moneda
- precios
- descuento
- fechas
- turno
- vehículo
- pagos
- pasajeros
- estado comercial
- estado de reserva
- estado de pago

### Qué calcula

- `precio_tour`
- `monto_total`
- `monto_pagado`
- `saldo_pendiente`
- `monto_web`
- `monto_final`
- `estado_pago`

## 9. `incas.pago`

Registra:

- `reserva_id`
- `proveedor`
- `metodo`
- `moneda`
- `monto`
- `estado`
- `transaccion_id`
- `orden_id`
- `fecha_pago`

## 10. Resultado después de reservar

Odoo hace:

1. crea reserva
2. crea pago
3. genera voucher PDF
4. expone `voucher_url`
5. sincroniza Sheets
6. envía correo
7. actualiza parte operativa

## 11. Voucher

### Rutas

- privada: `/incas/reserva/<id>/pdf`
- pública: `/incas/public/reserva/<id>/pdf/<token>`

### Uso del frontend

`BookingModal.astro`:

- abre `voucher_url` si Odoo lo devolvió
- si no, puede generar PDF local de respaldo

## 12. Correo

Se dispara desde Odoo.

Variables:

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_NOTIFY_EMAIL`

Adjunta:

- `comprobante-<ticket>.pdf`

## 13. Google Sheets

Se dispara desde Odoo con `GOOGLE_APPS_SCRIPT_URL`.

La reserva no depende de que Sheets responda bien para existir.

## 14. Riesgos

- el booking depende de estado global en `window`
- el payload frontend y la API Odoo están muy acoplados
- si cambia la estructura del catálogo, el booking puede romperse
- si falta `PUBLIC_ODOO_URL`, no hay flujo transaccional
- si falta `PUBLIC_ODOO_DB` en producción, Odoo puede no resolver la base correcta

## 15. Pruebas mínimas después de tocar este flujo

1. abrir un tour
2. abrir un transporte
3. cambiar moneda
4. reservar tour
5. reservar transporte con vehículo
6. validar ticket
7. validar `voucher_url`
8. validar creación de `incas.reserva`
9. validar creación de `incas.pago`
