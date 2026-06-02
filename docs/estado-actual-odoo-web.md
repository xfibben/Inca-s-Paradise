# Estado actual Odoo web

## 1. Fuente activa

Para el sitio público y el flujo transaccional, la fuente activa es `Odoo`.

Aplica a:

- tours
- destinos
- style trips
- transportes
- tipos de transporte
- sostenibilidad
- nosotros
- términos
- políticas
- cancelaciones
- preguntas frecuentes
- reservas
- pagos

## 2. Frontend ya conectado

Secciones ya montadas contra endpoints Odoo:

- home
- navbar
- listado y detalle de destinos
- listado y detalle de tours
- listado y detalle de transportes
- listado y detalle de tipo transporte
- listado y detalle de style trips
- blog de sostenibilidad
- páginas legales
- reserva
- pago
- sitemap

## 3. Catálogo web Odoo

Modelos principales:

- `incas.servicio.catalogo`
- `incas.tour`
- `incas.catalogo.destino`
- `incas.estilo.viaje`
- `incas.catalogo.transporte`
- `incas.catalogo.vehiculo`

## 4. Endpoints públicos actuales

- `GET /incas/api/web/destinos`
- `GET /incas/api/web/destinos/<slug>`
- `GET /incas/api/web/tours`
- `GET /incas/api/web/tours/<slug>`
- `GET /incas/api/web/estilos-viaje`
- `GET /incas/api/web/estilos-viaje/<slug>`
- `GET /incas/api/web/tipo-transportes`
- `GET /incas/api/web/tipo-transportes/<slug>`
- `GET /incas/api/web/transportes`
- `GET /incas/api/web/transportes/<slug>`
- `GET /incas/api/web/sostenibilidad`
- `GET /incas/api/web/sostenibilidad/<slug>`
- `GET /incas/api/web/terminos`
- `GET /incas/api/web/nosotros`
- `GET /incas/api/web/politicas`
- `GET /incas/api/web/cancelaciones`
- `GET /incas/api/web/preguntas-frecuentes`

## 5. Reserva actual

El frontend usa:

- `serviceId`
- slug del recurso
- datos del pasajero
- moneda
- descuento
- vehículo si aplica

Odoo resuelve:

- servicio real
- tarifa real
- ticket
- voucher
- pago

## 6. Transporte

Estado actual:

- el precio depende del vehículo
- Odoo entrega varias tarifas por vehículo
- el frontend deja elegir vehículo
- la reserva persiste `vehiculo_seleccionado`

## 7. Multidioma actual

Interfaz:

- `es/en/pt/fr/it`

Contenido Odoo:

- fuerte en `es`
- usable en `en`
- parcial en `pt`
- `fr/it` con fallback frecuente

## 8. Pendientes reales

- fortalecer cobertura `fr/it`
- reducir lógica inline de booking
- cubrir flujo con pruebas automáticas
- seguir endureciendo validaciones entre frontend y API pública
