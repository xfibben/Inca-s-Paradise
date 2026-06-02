# Inca's Paradise

Documentación actual del proyecto enfocada en `frontend + Odoo`.

`Strapi` queda fuera de esta guía operativa. Si aparece en compose o en docs viejas, trátalo como legado no prioritario.

## 1. Qué es el sistema

Inca's Paradise tiene dos piezas activas para el flujo principal:

- `frontend/`: sitio público SSR en Astro.
- `odoo/`: back office, catálogo operativo, reservas, pagos, documentos, RRHH, operaciones y postventa.

Flujo actual:

1. El visitante entra al sitio en `/[lang]/...`.
2. Astro consulta contenido público de Odoo por endpoints `/incas/api/web/*`.
3. El visitante navega tours, destinos, style trips, transportes, legales y blog de sostenibilidad.
4. El modal de reserva arma la compra y llama endpoints públicos de Odoo.
5. Odoo crea `incas.reserva`, registra `incas.pago`, genera ticket, PDF, correos y sincronización externa.
6. Operaciones, tesorería, postventa y RRHH continúan el ciclo desde Odoo.

## 2. Stack actual

- Frontend: `Astro 5`, `Tailwind CSS 4`, `Flowbite`
- Back office: `Odoo 19`
- Base pública principal: `Odoo + PostgreSQL 15`
- Infra local y productiva: `Docker Compose`
- Pago actual: `PayPal`
- PDF: generación desde Odoo
- Analytics: `GTM` y `GA4`
- Validación de libro de reclamaciones: `reCAPTCHA`

## 3. Estructura útil

```text
/
├── frontend/
│   ├── src/pages/[lang]/              # Rutas públicas por idioma
│   ├── src/components/                # UI y bloques funcionales
│   ├── src/utils/odooWeb.ts           # Fetch catálogo web Odoo
│   ├── src/utils/odooTransport.ts     # Fetch transporte Odoo
│   └── src/i18n/                      # Textos de interfaz
├── odoo/
│   ├── addons/incas_reservas/         # Catálogo, reservas, pagos, legales
│   ├── addons/incas_operaciones/      # Agenda y matriz operativa
│   ├── addons/incas_documentos/       # DMS y uploads
│   ├── addons/incas_postventas/       # Casos, reclamos, encuestas
│   ├── addons/incas_rrhh/             # Trabajadores, boletas, evaluación
│   ├── addons/incas_tesoreria/        # Movimientos de tesorería
│   └── config/odoo.conf               # Configuración Odoo
├── docker-compose.yaml                # Desarrollo
├── docker-compose.prod.yaml           # Producción
└── docs/
```

## 4. Módulos funcionales en producción

### Frontend

- Home multidioma.
- Listado y detalle de destinos.
- Listado y detalle de tours.
- Listado y detalle de transportes.
- Listado y detalle de tipos de transporte.
- Listado y detalle de style trips.
- Blog de sostenibilidad.
- Páginas legales y corporativas.
- Libro de reclamaciones.
- Sitemap dinámico.

### Odoo

- Catálogo de servicios.
- Tours, destinos, estilos de viaje, transportes y vehículos.
- Reservas y pagos.
- PDF de voucher público y privado.
- Agenda operativa y pase operativo.
- Gestión documental DMS.
- Postventa.
- RRHH.
- Tesorería.

## 5. Endpoints públicos Odoo que usa el frontend

### Catálogo web

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
- `GET /incas/public/image`

### Reserva y pago

- `GET /incas/api/pagos/tipo-cambio`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`
- `POST /incas/api/reservas`
- `GET /incas/public/reserva/<id>/pdf/<token>`

### Operaciones

- `GET /incas/operaciones/reserva/<id>/pase-pdf`

## 6. Flujo real de reserva

### Tours y transportes

1. La página detalle carga contenido desde Odoo por slug.
2. El detalle deja `serviceId`, slug y contexto en `window`.
3. `BookingCard.astro` calcula precios visibles por moneda.
4. `BookingModal.astro` arma `window.__pendingBooking`.
5. Si es pago directo, llama `POST /incas/api/reservas`.
6. Si es PayPal:
   - llama `POST /incas/api/pagos/iniciar`
   - aprueba en PayPal
   - llama `POST /incas/api/pagos/confirmar`
7. Odoo devuelve:
   - `ticket`
   - `reserva_id`
   - `voucher_url`
8. El frontend abre el comprobante o genera PDF local de respaldo.

### Reglas relevantes

- El descuento es porcentual.
- El catálogo base está en `USD`.
- Odoo convierte visualmente según moneda.
- En transportes el precio depende del vehículo elegido.
- `vehiculo_seleccionado` debe viajar desde frontend hasta la reserva.

## 7. Variables de entorno importantes

### Frontend

- `PUBLIC_ODOO_URL`
- `PUBLIC_ODOO_DB`
- `PUBLIC_PAYPAL_CLIENT_ID`
- `PUBLIC_GTM_ID`
- `PUBLIC_GA_MEASUREMENT_ID`
- `PUBLIC_GOOGLE_CLAIMS_FORM_URL`
- `PUBLIC_RECAPTCHA_SITE_KEY`
- `RECAPTCHA_SECRET_KEY`

### Odoo

- `ODOO_DB_NAME`
- `ODOO_DB_USER`
- `ODOO_DB_PASSWORD`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_SECRET`
- `PAYPAL_MODE`
- `GOOGLE_APPS_SCRIPT_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_NOTIFY_EMAIL`

Nota:

- No existe un `.env.example` completo y confiable en raíz.
- El siguiente programador debe reconstruir el `.env` leyendo `docker-compose.yaml` y `docker-compose.prod.yaml`.

## 8. Cómo correr local

### Todo el stack

```bash
docker compose up
```

Puertos de desarrollo:

- Frontend: `4321`
- Odoo: `8069`
- PostgreSQL Odoo: `5433`

### Solo frontend

```bash
cd frontend
npm install
npm run dev
```

### Odoo

La forma estable del proyecto es vía Docker.

## 9. Documentos que debes leer primero

- [Arquitectura actual](./docs/arquitectura-actual.md)
- [Frontend](./docs/frontend.md)
- [Odoo](./docs/odoo.md)
- [Reservas y pagos](./docs/reservas-y-pagos.md)
- [Operación y contenido](./docs/operacion-y-contenido.md)
- [Desarrollo](./docs/desarrollo.md)
- [VPS y despliegue](./docs/vps.md)
- [Multidioma](./docs/multidioma.md)

## 10. Riesgos actuales

- No vi suite de tests automática consolidada.
- El proyecto depende bastante de integración real con Odoo y variables de entorno.
- Hay mezcla de SSR, scripts inline y estado en `window` dentro del flujo de reserva.
- Algunas traducciones de contenido en Odoo están completas en `es/en/pt`; `fr/it` muchas veces caen a fallback.
- El home y la navbar mezclan contenido estático con fetch a Odoo.

## 11. Punto de entrada recomendado para un dev nuevo

1. Leer `docs/arquitectura-actual.md`.
2. Levantar `docker compose up`.
3. Revisar `frontend/src/pages/[lang]/tours/[tour].astro`.
4. Revisar `frontend/src/components/tours/BookingModal.astro`.
5. Revisar `odoo/addons/incas_reservas/controllers/api.py`.
6. Revisar `odoo/addons/incas_reservas/models/incas_reserva.py`.
7. Revisar `odoo/addons/incas_operaciones/models/incas_reserva.py`.
