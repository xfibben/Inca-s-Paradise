# Inca's Paradise

Plataforma de turismo para destinos en Peru con frontend SSR, CMS headless, reservas y pasarela de pago.

## Stack

- Frontend: Astro 5.17.1 + Tailwind CSS 4.2.1 + Flowbite 4.0.1
- Backend: Strapi 5.37.1 + PostgreSQL 14
- Back office: Odoo 19 + PostgreSQL 15
- PDF: `jspdf`
- Contenido multidioma: i18n local en Astro + locales de Strapi
- Infraestructura local y productiva: Docker Compose

## Dependencias principales

### Frontend

- `astro`
- `@astrojs/node`
- `tailwindcss`
- `@tailwindcss/vite`
- `@tailwindcss/typography`
- `flowbite`
- `@fontsource/playfair-display`
- `markdown-it`
- `jspdf`

### Backend

- `@strapi/strapi`
- `@strapi/plugin-users-permissions`
- `@strapi/plugin-cloud`
- `pg`
- `react`
- `react-dom`
- `react-router-dom`
- `styled-components`

## Arquitectura

```text
/
├── frontend/                  # Sitio web SSR en Astro
│   ├── src/pages/[lang]/      # Rutas por idioma
│   ├── src/components/        # UI por dominio
│   ├── src/i18n/              # Traducciones locales y UBIGEO
│   └── src/data/              # Datos estaticos de apoyo
├── backend/                   # CMS y APIs en Strapi
│   └── src/api/               # Content types, controllers, routes y services
├── docker-compose.yaml        # Desarrollo
├── docker-compose.prod.yaml   # Produccion
└── docs/                      # Documentacion del proyecto
```

## Modulos funcionales

- Destinos y detalle de destinos
- Tours y reservas
- Style trips
- Transporte, tipos de transporte y vehiculos
- Terminos y condiciones
- Pagos con gateway unificado
- Sincronizacion de reservas con Google Sheets

## Arranque rapido

### Opcion 1: Docker Compose

1. Configurar variables en `.env`.
2. Levantar servicios:

```bash
docker compose up
```

Servicios por defecto:

- Frontend: `http://localhost:4321`
- Backend Strapi: `http://localhost:1337`
- PostgreSQL: `localhost:5432`
- Odoo: `http://localhost:8069`
- PostgreSQL Odoo: `localhost:5433`

### Opcion 2: Ejecucion por separado

Backend:

```bash
cd backend
npm install
npm run develop
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Variables de entorno

El proyecto usa variables en el `.env` raiz y ejemplos parciales en:

- [.env.example](/Users/arturo/Documents/Inca-s-Paradise/.env.example)
- [frontend/.env.example](/Users/arturo/Documents/Inca-s-Paradise/frontend/.env.example)
- [backend/.env.example](/Users/arturo/Documents/Inca-s-Paradise/backend/.env.example)

Variables clave:

- Base de datos: `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- Base de datos Odoo: `ODOO_DB_NAME`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD`
- Strapi: `ADMIN_JWT_SECRET`, `API_TOKEN_SALT`, `APP_KEYS`, `JWT_SECRET`
- Frontend: `PUBLIC_STRAPI_URL`, `PUBLIC_ODOO_URL`, `PUBLIC_GTM_ID`, `PUBLIC_GA_MEASUREMENT_ID`
- Google Sheets: `GOOGLE_APPS_SCRIPT_URL`
- PayPal: `PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`, `PAYPAL_MODE`, `PAYPAL_WEBHOOK_ID`
- Cambio de moneda y documentos: `APIS_NET_PE_TOKEN`

`PUBLIC_ODOO_URL` se define en el `.env` raiz del proyecto y se inyecta al frontend desde ambos archivos:

- [docker-compose.yaml](/Users/arturo/Documents/Inca-s-Paradise/docker-compose.yaml)
- [docker-compose.prod.yaml](/Users/arturo/Documents/Inca-s-Paradise/docker-compose.prod.yaml)

## Flujo general

1. El usuario navega el sitio en `/[lang]/...`.
2. El frontend consume contenido y datos desde Strapi.
3. La reserva se arma en el frontend.
4. El backend confirma el pago y crea la reserva.
5. La reserva se sincroniza a Google Sheets.

## Documentacion

- [Guia de desarrollo](./docs/desarrollo.md)
- [Guia de multidioma](./docs/multidioma.md)
- [Reservas y pagos](./docs/reservas-y-pagos.md)
- [Operacion y contenido](./docs/operacion-y-contenido.md)
- [Guia de uso del CMS](./docs/guia-cms.md)
- [Guia del VPS](./docs/vps.md)

## Estado actual

- PayPal: implementado
- IziPay tarjeta: pendiente
- IziPay Yape QR: pendiente
- Sincronizacion a Google Sheets: activa por lifecycle de `reserva`
- Suite de tests automatizados: no encontrada en el repositorio

## Recomendado documentar despues

- Proceso de despliegue y rollback
- Politica de manejo de credenciales y rotacion de secretos
- Flujo editorial para altas y cambios de contenido
- SEO, analytics y eventos de conversion
- Manejo de media en Strapi
- Respuesta operativa ante pagos fallidos o reservas incompletas
