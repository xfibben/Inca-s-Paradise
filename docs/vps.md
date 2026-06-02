# VPS y despliegue

## 1. Estructura operativa

Entornos conocidos:

- `apps/Incasparadisetest`
- `apps/IncasparadiseProduction`

Relación esperada:

- `test` -> pruebas
- `main` -> producción

## 2. Compose usado

### Desarrollo / test

- `docker-compose.yaml`

Servicios relevantes:

- `frontend`
- `odoo`
- `odoo_db`

### Producción

- `docker-compose.prod.yaml`

Servicios relevantes:

- `frontend`
- `odoo`
- `odoo_db`

## 3. Puertos

### Test

- frontend: `4321`
- odoo: `8069`
- odoo db: `5433`

### Producción

- frontend: `4320`
- odoo http: `8070`
- odoo websocket: `8072`
- odoo db: `5434`

## 4. Variables críticas en servidor

- `PUBLIC_ODOO_URL`
- `PUBLIC_ODOO_DB`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_SECRET`
- `PAYPAL_MODE`
- `GOOGLE_APPS_SCRIPT_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_NOTIFY_EMAIL`
- `PUBLIC_GTM_ID`
- `PUBLIC_GA_MEASUREMENT_ID`
- `PUBLIC_RECAPTCHA_SITE_KEY`
- `RECAPTCHA_SECRET_KEY`

## 5. Deploy de test

```bash
cd apps/Incasparadisetest
docker compose -f docker-compose.yaml down
git pull origin test
docker compose -f docker-compose.yaml up -d
```

## 6. Deploy de producción

```bash
cd apps/IncasparadiseProduction
docker compose -f docker-compose.prod.yaml down
git pull origin main
docker compose -f docker-compose.prod.yaml up -d
```

## 7. Validaciones post deploy

1. `git branch --show-current`
2. `git log -1 --oneline`
3. `docker ps`
4. abrir frontend
5. abrir Odoo
6. probar `GET /incas/api/pagos/tipo-cambio`
7. probar una página de tour
8. probar una página de transporte

## 8. Punto crítico de producción

Odoo puede no resolver la base si no llega `X-Odoo-Database`.

Por eso:

- frontend puede usar `PUBLIC_ODOO_DB`
- el proxy puede necesitar enviar `X-Odoo-Database`

Síntoma típico:

- `404`
- mensaje de Odoo indicando que no hay base seleccionada

## 9. Websocket de Odoo

Producción usa:

- `8072`

Si fallan cosas en tiempo real o assets backend:

- revisar proxy a `/websocket`
- confirmar `gevent_port`

## 10. DMS

Si manejan archivos pesados:

- revisar timeouts del proxy
- revisar `client_max_body_size`
- revisar que Odoo pueda procesar uploads grandes

## 11. Riesgos

- deploy con variables incompletas rompe frontend o pagos
- base Odoo mal resuelta rompe endpoints públicos
- cambio de proxy puede romper voucher, imágenes o websocket
