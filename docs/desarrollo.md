# Guia de desarrollo

## Objetivo

Este documento resume como trabajar en el proyecto sin romper los flujos principales de contenido, reservas y pagos.

## Requisitos

- Node.js 20 o superior
- npm
- Docker y Docker Compose para entorno completo
- PostgreSQL 14 si se ejecuta fuera de Docker

## Servicios

### Desarrollo local

- PostgreSQL: `5432`
- Strapi: `1337`
- Astro: `4321`

### Produccion segun compose

- PostgreSQL: `5431`
- Strapi: `1336`
- Astro SSR: `4320`

## Comandos

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
```

### Backend

```bash
cd backend
npm install
npm run develop
npm run build
npm run start
```

### Docker Compose

```bash
docker compose up
docker compose -f docker-compose.prod.yaml up
```

## Flujo de ramas

Ramas de trabajo actuales:

- `xfibben`
- `Arkds`
- `test`
- `main`

Flujo acordado:

1. Cada desarrollador trabaja en su propia rama.
2. Los cambios se integran primero hacia `test`.
3. La validacion funcional se hace sobre `test`.
4. Una vez aprobado en `test`, se sube a `main`.
5. El VPS de pruebas hace pull de `test`.
6. El VPS de produccion hace pull de `main`.

Uso esperado:

- trabajo individual: `xfibben` o `Arkds`
- integracion interna: `test`
- produccion: `main`

Nota:

- Este flujo fue documentado segun la operacion actual compartida por el equipo. Si se crean mas ramas personales, deben seguir el mismo patron: rama personal -> `test` -> `main`.

## Estructura de trabajo

### Frontend

- `frontend/src/pages/[lang]/`: paginas por idioma
- `frontend/src/components/LandingPage/`: home
- `frontend/src/components/tours/`: cards, booking y voucher
- `frontend/src/components/transporte/`: vistas de transporte
- `frontend/src/components/tipo-transporte/`: comparativas de vehiculos
- `frontend/src/components/shared/`: navbar, footer, selector de idioma
- `frontend/src/components/SEO/`: SEO e imagenes optimizadas
- `frontend/src/i18n/`: traducciones y UBIGEO
- `frontend/src/data/`: contenido estatico de apoyo

### Backend

- `backend/src/api/*/content-types/`: schemas
- `backend/src/api/*/controllers/`: logica HTTP
- `backend/src/api/*/routes/`: rutas core y custom
- `backend/src/api/*/services/`: integraciones y logica reusable
- `backend/src/components/`: componentes reutilizables de Strapi

## Convenciones del proyecto

- Idiomas de ruta: `es`, `en`, `pt`, `fr`, `it`
- Idioma por defecto: `es`
- El frontend usa SSR con rutas `/[lang]/...`
- Las paginas de transporte usan verde `#1AA093`
- `reserva` usa `draftAndPublish`, por eso desde backend debe enviarse `publishedAt`

## Flujos sensibles

### Reservas

- El frontend arma una reserva pendiente en memoria.
- El backend crea la `reserva` final solo al confirmar el pago.
- El ticket se genera en backend.

### Pagos

- La ruta custom de pago esta en `backend/src/api/pago/routes/pago-custom.ts`
- El gateway unificado esta en `backend/src/api/pago/services/gateway.ts`
- PayPal funciona.
- IziPay todavia no esta implementado.

### Google Sheets

- La sincronizacion ocurre en los lifecycles de `reserva`.
- Depende de `GOOGLE_APPS_SCRIPT_URL`.
- Si falla, la reserva igual puede existir en Strapi.

## Multidioma

- El frontend tiene traducciones JSON locales.
- Ademas consulta `/api/locales` para obtener idiomas disponibles desde Strapi.
- Si falla el backend, usa fallback local.

## Antes de tocar codigo

- Revisar si el cambio afecta rutas por idioma.
- Revisar si el cambio toca booking, pagos o sincronizacion.
- Revisar si el contenido existe en Strapi, en JSON local o en ambos.

## Riesgos actuales detectados

- No se encontro suite de tests automatizados en el repo.
- Los `README.md` de `frontend/` y `backend/` venian con boilerplate y no describian el sistema real.
- El proyecto depende de variables sensibles en `.env` raiz.
- El despliegue depende de disciplina de ramas y de `git pull` manual en el VPS.
