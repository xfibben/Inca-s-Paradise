# Auditoria de modelos

## Alcance

Revision funcional de:

- `tour-detalle`
- `transporte`
- `reserva`
- `pago`

Archivos base revisados:

- [backend/src/api/tour-detalle/content-types/tour-detalle/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/tour-detalle/content-types/tour-detalle/schema.json)
- [backend/src/api/transporte/content-types/transporte/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/transporte/content-types/transporte/schema.json)
- [backend/src/api/reserva/content-types/reserva/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/content-types/reserva/schema.json)
- [backend/src/api/pago/content-types/pago/schema.json](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/content-types/pago/schema.json)
- [frontend/src/components/tours/BookingCard.astro](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/components/tours/BookingCard.astro)
- [frontend/src/components/tours/BookingModal.astro](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/components/tours/BookingModal.astro)
- [backend/src/api/reserva/controllers/reserva.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/controllers/reserva.ts)
- [backend/src/api/reserva/content-types/reserva/lifecycles.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/reserva/content-types/reserva/lifecycles.ts)
- [backend/src/api/pago/controllers/pago.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/pago/controllers/pago.ts)

## Estado actual

### Tour

- `adultUnitPrice` y `childUnitPrice` existen en el modelo
- `discount` existe en el modelo
- el frontend ahora interpreta `discount` como porcentaje
- el precio visible y el total de reserva usan esa semantica

### Transporte

- el precio no vive en campos planos del modelo
- el precio vive en `precios[]` mediante el componente `transporte.precio-vehiculo`
- cada item contiene `precioAdulto`, `precioNino` y `descuento`
- el frontend ahora interpreta `descuento` como porcentaje

### Reserva

- `descuento` se usa como porcentaje
- `vehiculo_seleccionado` se persiste para reservas de transporte
- `precio_tour` representa el total estimado del servicio con descuento aplicado
- `precio_adulto_web` y `precio_nino_web` representan el adelanto web por tipo de pasajero
- `monto_web`, `pago_restante` y `monto_final` se recalculan en backend

### Pago

- registra el monto efectivamente cobrado
- no tiene campo de descuento
- no requiere guardar porcentaje de descuento mientras `reserva` conserve ese dato

## Cambios aplicados

### Descuento porcentual

Se homogeneizo la semantica de descuento:

- tours: porcentaje
- transporte: porcentaje
- reserva: porcentaje
- pago: sin campo de descuento

### Flujo de pago

- el flujo `POST /api/pagos/confirmar` ahora tambien persiste `reserva.descuento`
- en transporte, el flujo tambien persiste `reserva.vehiculo_seleccionado`
- esto deja consistente la reserva creada por pago con la creada por ruta directa

### Controlador de reserva

Se corrigio `backend/src/api/reserva/controllers/reserva.ts`:

- antes intentaba leer `adultUnitPrice`, `childUnitPrice` y `discount` desde `transporte`, pero esos campos no existen ahi
- ahora, si el frontend ya envia montos calculados, el backend respeta esos valores
- si no llegan montos calculados:
  - en tours usa el modelo `tour-detalle`
  - en transporte busca el item correcto de `precios[]` usando `vehiculo_seleccionado`
  - si no existe ese dato, usa el primer item como fallback
- el calculo de descuento backend ahora usa porcentaje y no resta fija

### Sincronizacion con Sheets

Se corrigio `backend/src/api/reserva/content-types/reserva/lifecycles.ts`:

- antes intentaba leer precios unitarios desde el servicio relacionado, lo cual era incorrecto para transporte
- ahora deriva `precio_adulto` y `precio_nino` desde `precio_adulto_web` y `precio_nino_web` guardados en la propia reserva
- tambien envia `vehiculo` a Google Sheets cuando la reserva es de transporte

## Hallazgos

### Correcto

- `pago` y `reserva` siguen separados con responsabilidades claras
- el flujo custom de pago crea reserva y luego pago
- `reserva` usa `publishedAt` en el flujo de pago para evitar draft
- `pago.monto` sigue guardando el monto realmente cobrado

### Riesgo residual

- las reservas de transporte antiguas no tendran `vehiculo_seleccionado`
- si una de esas reservas necesita recomputo backend sin montos precalculados, se usara el primer item de `precios[]` como fallback

## Verificacion hecha

- se revisaron schemas, controladores, lifecycles y puntos de uso del frontend
- se verifico consistencia de semantica entre UI, reserva y pago
- no se pudo ejecutar build completo del frontend porque el entorno sigue fallando por la dependencia faltante de Rollup
