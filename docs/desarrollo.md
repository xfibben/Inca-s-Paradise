# Desarrollo

## 1. Objetivo

Guía corta para levantar, tocar y no romper el sistema actual `Astro + Odoo`.

## 2. Requisitos

- Docker
- Docker Compose
- Node.js 20+
- npm

## 3. Entorno local recomendado

### Stack completo

```bash
docker compose up
```

Puertos:

- frontend: `http://localhost:4321`
- odoo: `http://localhost:8069`
- odoo db: `localhost:5433`

### Frontend aislado

```bash
cd frontend
npm install
npm run dev
```

## 4. Variables que debes tener sí o sí

### Frontend

- `PUBLIC_ODOO_URL`
- `PUBLIC_ODOO_DB`
- `PUBLIC_PAYPAL_CLIENT_ID`
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

## 5. Flujo de ramas

Ramas vistas en el proyecto:

- `main`
- `test`
- ramas personales

Uso práctico:

1. rama personal
2. merge a `test`
3. validación
4. merge a `main`

## 6. Qué revisar antes de tocar frontend

- si la página consume Odoo o solo i18n local
- si el cambio impacta `Navbar.astro`
- si toca `BookingCard.astro` o `BookingModal.astro`
- si cambia estructura esperada del payload Odoo
- si afecta rutas `/[lang]/...`

## 7. Qué revisar antes de tocar Odoo

- si el campo lo usa la API pública
- si el cambio impacta `incas.reserva`
- si el modelo tiene `create`, `write` o `_auto_init`
- si el campo participa en precios, moneda o descuento
- si el cambio rompe serializadores del controlador `api.py`

## 8. Checklist por tipo de cambio

### Catálogo web

1. revisar modelo Odoo
2. revisar serialización en `api.py`
3. revisar página Astro que lo consume
4. revisar sitemap si aplica

### Reserva / pago

1. revisar `BookingModal.astro`
2. revisar endpoints `/incas/api/*`
3. revisar `incas.reserva`
4. revisar `incas.pago`
5. revisar voucher PDF
6. revisar correo y `voucher_url`

### Operaciones

1. revisar `incas_operaciones/models/incas_reserva.py`
2. revisar agenda
3. revisar pase PDF

### RRHH

1. revisar vistas XML
2. revisar modelos RRHH
3. revisar accesos

## 9. Comandos útiles

### Frontend

```bash
cd frontend
npm run dev
npm run build
```

### Búsqueda rápida

```bash
rg "incas/api/web" frontend/src
rg "@http.route" odoo/addons/incas_reservas/controllers
rg "_name = \"incas\\." odoo/addons/incas_*/models
```

### Sintaxis Python

```bash
python3 -m py_compile odoo/addons/incas_rrhh/models/incas_evaluacion_desempeno.py
```

## 10. Riesgos conocidos

- no vi suite formal de tests E2E
- `BookingModal.astro` es frágil
- la API pública Odoo está acoplada al render SSR
- el deploy depende de variables correctas en compose
- `PUBLIC_ODOO_DB` puede ser obligatorio cuando Odoo no resuelve bien la base

## 11. Orden recomendado para entender el proyecto

1. `readme.md`
2. `docs/arquitectura-actual.md`
3. `docs/frontend.md`
4. `docs/odoo.md`
5. `frontend/src/pages/[lang]/tours/[tour].astro`
6. `frontend/src/components/tours/BookingModal.astro`
7. `odoo/addons/incas_reservas/controllers/api.py`
8. `odoo/addons/incas_reservas/models/incas_reserva.py`
