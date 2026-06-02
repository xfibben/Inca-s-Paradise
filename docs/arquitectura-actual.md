# Arquitectura actual

## 1. Corte real del sistema

El proyecto opera hoy con dos capas activas:

- `Astro` como frontend público SSR.
- `Odoo` como backend funcional y fuente pública de datos.

Relación:

```text
Visitante
  -> Frontend Astro
    -> Endpoints públicos Odoo /incas/api/web/*
    -> Endpoints públicos Odoo /incas/api/pagos/* y /incas/api/reservas
      -> Modelos Odoo
        -> PDF
        -> correo
        -> Google Sheets
        -> agenda operativa
```

## 2. Responsabilidad por capa

### Frontend

Responsable de:

- SSR de páginas públicas.
- SEO y sitemap.
- i18n de interfaz.
- render de contenido HTML recibido desde Odoo.
- UI de booking y pago.
- integración de PayPal JS.
- libro de reclamaciones.

No guarda reservas. Solo captura datos, presenta precios y dispara endpoints.

### Odoo

Responsable de:

- catálogo público.
- precios base y lógica de descuentos.
- reservas.
- pagos.
- documentos.
- operaciones.
- postventa.
- RRHH.
- tesorería.

## 3. Mapa del frontend

### Rutas principales

- `frontend/src/pages/[lang]/index.astro`
- `frontend/src/pages/[lang]/destinos/index.astro`
- `frontend/src/pages/[lang]/destinos/[slug].astro`
- `frontend/src/pages/[lang]/tours/[tour].astro`
- `frontend/src/pages/[lang]/style-trips/[slug].astro`
- `frontend/src/pages/[lang]/tipo-transporte/index.astro`
- `frontend/src/pages/[lang]/tipo-transporte/[slug].astro`
- `frontend/src/pages/[lang]/transporte/index.astro`
- `frontend/src/pages/[lang]/transporte/[slug].astro`
- `frontend/src/pages/[lang]/blog/[blog].astro`
- `frontend/src/pages/[lang]/nosotros/index.astro`
- `frontend/src/pages/[lang]/terminos/index.astro`
- `frontend/src/pages/[lang]/politicas/index.astro`
- `frontend/src/pages/[lang]/cancelaciones/index.astro`
- `frontend/src/pages/[lang]/preguntas-frecuentes/index.astro`
- `frontend/src/pages/[lang]/claims/index.astro`
- `frontend/src/pages/sitemap.xml.ts`

### Componentes sensibles

- `frontend/src/components/shared/Navbar.astro`
- `frontend/src/components/tours/BookingCard.astro`
- `frontend/src/components/tours/BookingModal.astro`
- `frontend/src/components/tours/voucher-pdf.ts`
- `frontend/src/components/LandingPage/DestinationsGallery.astro`
- `frontend/src/components/LandingPage/StylesTrips.astro`
- `frontend/src/components/LandingPage/SustainabilitySection.astro`

### Utilidades críticas

- `frontend/src/utils/odooWeb.ts`
- `frontend/src/utils/odooTransport.ts`
- `frontend/src/utils/richContent.ts`
- `frontend/src/utils/currency.ts`
- `frontend/src/middleware.ts`

## 4. Mapa de Odoo

### Addons propios

- `incas_core`
  - menú raíz y grupos base.

- `incas_documentos`
  - DMS, cargas, previews y overrides documentales.

- `incas_reservas`
  - catálogo web.
  - servicios.
  - tours.
  - destinos.
  - estilos de viaje.
  - transportes.
  - vehículos.
  - legales.
  - reservas.
  - pagos.
  - endpoints públicos web.
  - voucher PDF.

- `incas_operaciones`
  - agenda operativa.
  - matriz operativa por reserva.
  - pase operativo PDF.
  - revisión de tareas sobre `mail.activity`.

- `incas_postventas`
  - casos.
  - reclamos.
  - encuestas.
  - acciones.

- `incas_rrhh`
  - trabajadores.
  - boletas.
  - certificados laborales.
  - evaluación semanal/mensual.

- `incas_tesoreria`
  - movimientos manuales de tesorería.

- `incas_proveedores`
  - proveedores del back office.

- `incas_producto`
  - historial de tours.

## 5. Modelos Odoo más importantes

### Catálogo y contenido

- `incas.servicio.catalogo`
- `incas.tour`
- `incas.catalogo.destino`
- `incas.estilo.viaje`
- `incas.catalogo.transporte`
- `incas.catalogo.transporte.tarifa`
- `incas.catalogo.vehiculo`
- `incas.termino.condicion`
- `incas.politica`
- `incas.cancelacion`
- `incas.pregunta.frecuente`
- `incas.sostenibilidad.articulo`
- `incas.nosotros`

### Transaccional

- `incas.reserva`
- `incas.pago`
- `incas.pasajero`
- `incas.reserva.paquete.linea`
- `incas.reserva.hotel.linea`
- `incas.reserva.extra.linea`
- `incas.reserva.cambio`

### Operación

- `incas.agenda.evento`
- `incas.reserva.operacion.linea`

### RRHH

- `res.users` extendido en RRHH.
- `incas.boleta`
- `incas.certificado.laboral`
- `incas.evaluacion.desempeno.mensual`
- `incas.evaluacion.desempeno.semana`
- `incas.evaluacion.desempeno.linea`
- `incas.evaluacion.desempeno.criterio`

## 6. Flujo público de catálogo

### Tours

1. Astro pide `GET /incas/api/web/tours/<slug>?lang=...`.
2. Odoo serializa `incas.tour`.
3. Devuelve SEO, destacados, itinerario, incluye/no incluye, horarios, galería y `serviceId`.
4. El frontend renderiza detalle, schema y booking.

### Transportes

1. Astro pide `GET /incas/api/web/transportes/<slug>?lang=...`.
2. Odoo serializa `incas.catalogo.transporte`.
3. Devuelve tarifas por vehículo, tipos de transporte, descripción, incluye/no incluye y `serviceId`.
4. El frontend deja elegir vehículo y recalcula booking.

### Home y navegación

La home y navbar consultan Odoo para:

- destinos
- style trips
- sostenibilidad
- tipos de transporte

Eso implica que incluso cambios editoriales visibles en menús y secciones del home viven ya en Odoo.

## 7. Flujo de reserva

### Origen frontend

`BookingModal.astro`:

- guarda estado en `window.__pendingBooking`
- calcula porcentaje a cobrar
- dispara PayPal o reserva directa
- guarda último `voucher_url`

### Ingreso a Odoo

Endpoints:

- `POST /incas/api/reservas`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`

### Modelo central

`incas.reserva` hace:

- genera secuencia `name`
- genera `ticket`
- genera `access_token`
- completa datos del servicio
- resuelve tarifas por vehículo si es transporte
- convierte precios desde USD a la moneda elegida
- crea pasajero principal si no existe
- asegura carpeta documental DMS
- genera URL pública del voucher
- dispara sincronización posterior

## 8. Flujo post-reserva

Después de crear una reserva web:

1. registra pagos en `incas.pago`
2. sincroniza Google Sheets
3. genera PDF de voucher
4. envía correo
5. crea evento operativo
6. genera matriz operativa

## 9. Multidioma real

### Interfaz

Se resuelve en `frontend/src/i18n/*.json`.

### Contenido Odoo

La serialización pública soporta:

- `es`
- `en`
- `pt`
- fallback parcial para `fr`
- fallback parcial para `it`

En varios modelos el contenido completo multidioma está implementado solo con campos `es/en/pt`. Si `fr` o `it` no tienen campo dedicado, el controlador cae al base español.

## 10. Despliegue

### Desarrollo

- `docker-compose.yaml`
- frontend en `4321`
- odoo en `8069`

### Producción

- `docker-compose.prod.yaml`
- frontend en `4320`
- odoo en `8070`
- websocket Odoo en `8072`

## 11. Dependencias operativas externas

- PayPal
- Resend
- Google Apps Script para Sheets
- reCAPTCHA
- GTM / GA4

## 12. Riesgos de mantenimiento

- Mucha lógica de reserva vive en scripts inline del frontend.
- La serialización Odoo es extensa y manual.
- El contenido web y el flujo operacional comparten el mismo Odoo.
- No hay test suite que cubra reserva, pago y render SSR end to end.
