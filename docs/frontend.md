# Frontend

## 1. Stack

- `Astro 5`
- `@astrojs/node`
- `Tailwind CSS 4`
- `Flowbite`
- `markdown-it`
- `jspdf`

Configuración base:

- `frontend/astro.config.mjs`
- `frontend/src/middleware.ts`

## 2. Estructura

```text
frontend/src/
├── pages/
│   ├── [lang]/                   # Sitio público por idioma
│   ├── api/claims/submit.ts      # API server-side del libro de reclamaciones
│   └── sitemap.xml.ts            # Sitemap dinámico
├── components/
│   ├── shared/                   # Navbar, Footer, Analytics
│   ├── LandingPage/              # Home
│   ├── tours/                    # BookingCard, BookingModal, voucher
│   ├── transporte/               # UI transporte
│   ├── tipo-transporte/          # Comparativas
│   └── stylestrips/              # Style trips
├── utils/
│   ├── odooWeb.ts
│   ├── odooTransport.ts
│   ├── richContent.ts
│   └── currency.ts
├── i18n/
└── styles/
```

## 3. Reglas de navegación

### Idiomas

Rutas válidas:

- `es`
- `en`
- `pt`
- `fr`
- `it`

`frontend/src/middleware.ts`:

- normaliza locales como `es-pe` -> `es`
- hace redirects de rutas viejas
- da `404` a locales inválidos
- setea headers de cache según HTML o asset

## 4. Consumo de Odoo

### Base URL

Helpers:

- `frontend/src/utils/odooWeb.ts`
- `frontend/src/utils/odooTransport.ts`

Comportamiento:

- en SSR usa `ODOO_URL` si existe.
- en browser usa `PUBLIC_ODOO_URL`.
- si existe `PUBLIC_ODOO_DB`, envía header `X-Odoo-Database`.

### Uso real

#### Home

- `DestinationsGallery.astro` -> `/incas/api/web/destinos`
- `StylesTrips.astro` -> `/incas/api/web/estilos-viaje`
- `SustainabilitySection.astro` -> `/incas/api/web/sostenibilidad`
- `Navbar.astro` -> tipos de transporte, style trips, destinos, sostenibilidad

#### Páginas de detalle

- tour -> `/incas/api/web/tours/<slug>`
- destino -> `/incas/api/web/destinos/<slug>`
- transporte -> `/incas/api/web/transportes/<slug>`
- tipo de transporte -> `/incas/api/web/tipo-transportes/<slug>`
- style trip -> `/incas/api/web/estilos-viaje/<slug>`
- blog -> `/incas/api/web/sostenibilidad/<slug>`
- legales/corporativas -> endpoints dedicados

## 5. Booking

### Archivos clave

- `frontend/src/components/tours/BookingCard.astro`
- `frontend/src/components/tours/BookingModal.astro`
- `frontend/src/components/tours/voucher-pdf.ts`

### Cómo funciona

`BookingCard.astro`:

- muestra precios base
- controla moneda visible
- controla cantidad de adultos y niños
- en transporte se sincroniza con el vehículo seleccionado

`BookingModal.astro`:

- abre formulario completo
- valida términos
- arma payload de reserva
- guarda estado temporal en `window.__pendingBooking`
- decide si usa PayPal o reserva directa
- abre voucher cuando Odoo responde

### Variables `window` usadas

- `window.__pendingBooking`
- `window.__odooUrl`
- `window.__paypalClientId`
- `window.__lastCompletedBookingVoucherUrl`
- `window.__tourData`
- `window.__tourSlugs`

Esto importa porque cualquier refactor del booking tiene que respetar estas dependencias o reemplazarlas completas.

## 6. Páginas sensibles

### Tour detail

Archivo:

- `frontend/src/pages/[lang]/tours/[tour].astro`

Hace:

- fetch SSR por slug
- SEO dinámico
- schema `TouristTrip`
- render de itinerario, galería, FAQ
- inyección de `serviceId`
- montaje de `BookingCard` y `BookingModal`

### Transporte detail

Archivo:

- `frontend/src/pages/[lang]/transporte/[slug].astro`

Hace:

- fetch SSR por slug
- selector de vehículo desde query param o primer vehículo
- precios por vehículo
- schema `Service`
- render de booking con datos del vehículo activo

### Sitemap

Archivo:

- `frontend/src/pages/sitemap.xml.ts`

Hace fetch de slugs Odoo para:

- tours
- destinos
- estilos de viaje
- tipo-transportes
- transportes
- sostenibilidad

## 7. Libro de reclamaciones

Archivos:

- `frontend/src/pages/[lang]/claims/index.astro`
- `frontend/src/pages/api/claims/submit.ts`

Flujo:

1. Formulario público multidioma.
2. validación de `reCAPTCHA`.
3. submit server-side desde Astro.
4. reenvío a `PUBLIC_GOOGLE_CLAIMS_FORM_URL`.

## 8. Rich text

Utilidad:

- `frontend/src/utils/richContent.ts`

Rol:

- normalizar HTML/rich text desde Odoo.
- convertir contenido para render.

Regla práctica:

- si se toca contenido Odoo visible en frontend, revisar siempre cómo lo procesa `richContent.ts`.

## 9. SEO y analytics

### SEO

- `frontend/src/components/SEO/SEOHead.astro`
- `frontend/src/pages/sitemap.xml.ts`

### Analytics

- `frontend/src/components/shared/GoogleAnalytics.astro`

Variables:

- `PUBLIC_GTM_ID`
- `PUBLIC_GA_MEASUREMENT_ID`

## 10. Variables de entorno frontend

- `PUBLIC_ODOO_URL`
- `PUBLIC_ODOO_DB`
- `ODOO_URL`
- `PUBLIC_PAYPAL_CLIENT_ID`
- `PUBLIC_GTM_ID`
- `PUBLIC_GA_MEASUREMENT_ID`
- `PUBLIC_GOOGLE_CLAIMS_FORM_URL`
- `PUBLIC_RECAPTCHA_SITE_KEY`
- `RECAPTCHA_SECRET_KEY`

## 11. Comandos

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
```

## 12. Riesgos concretos

- `BookingModal.astro` concentra mucha lógica y estado.
- Hay scripts inline largos y acoplados a DOM.
- El home depende de Odoo incluso para navegación.
- La configuración de moneda en `currency.ts` usa tasas fijas visuales; la tasa transaccional sale de Odoo.
- `fr` e `it` dependen varias veces de fallback.
