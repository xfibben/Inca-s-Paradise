# Guia del VPS

## Objetivo

Documentar como esta organizado el proyecto en el VPS y como se actualizan los entornos de prueba y produccion.

## Estructura actual

Carpetas indicadas por el equipo:

- `apps/Incasparadisetest`
- `apps/IncasparadiseProduction`

Relacion esperada con ramas:

- `apps/Incasparadisetest` -> rama `test`
- `apps/IncasparadiseProduction` -> rama `main`

## Flujo de despliegue

### Entorno de prueba

Se usa para validar cambios integrados antes de produccion.

Secuencia:

1. Los cambios de ramas personales se integran a `test`.
2. En el VPS se entra a `apps/Incasparadisetest`.
3. Se bajan los servicios con `docker compose -f docker-compose.yaml down`.
4. Se hace `git pull` de la rama `test`.
5. Se levantan los servicios con `docker compose -f docker-compose.yaml up -d`.

### Entorno de produccion

Se usa solo para cambios aprobados.

Secuencia:

1. Una vez aprobado lo que esta en `test`, se sube a `main`.
2. En el VPS se entra a `apps/IncasparadiseProduction`.
3. Se bajan los servicios con `docker compose -f docker-compose.prod.yaml down`.
4. Se hace `git pull` de la rama `main`.
5. Se levantan los servicios con `docker compose -f docker-compose.prod.yaml up -d`.

## Resumen rapido

- ramas personales: desarrollo individual
- `test`: integracion y validacion
- `main`: produccion

- `apps/Incasparadisetest`: entorno asociado a `test`
- `apps/IncasparadiseProduction`: entorno asociado a `main`

## Secuencia exacta en el VPS

### Pruebas

```bash
cd apps/Incasparadisetest
docker compose -f docker-compose.yaml down
git pull origin test
docker compose -f docker-compose.yaml up -d
```

### Produccion

```bash
cd apps/IncasparadiseProduction
docker compose -f docker-compose.prod.yaml down
git pull origin main
docker compose -f docker-compose.prod.yaml up -d
```

## Validaciones despues de la actualizacion

- confirmar rama activa con `git branch --show-current`
- confirmar ultimo commit con `git log -1 --oneline`
- revisar que variables de entorno sigan presentes
- confirmar que los contenedores hayan levantado correctamente
- confirmar acceso a Odoo en `8069` para pruebas y `8070` para produccion

## Red Docker y proxy en produccion

En produccion se fijo la red Docker para evitar que Hestia o Nginx apunten a destinos variables o fallen al reiniciar contenedores.

IPs internas usadas en `docker-compose.prod.yaml`:

- `postgres` -> `172.19.0.2`
- `odoo_db` -> `172.19.0.3`
- `backend` -> `172.19.0.10`
- `odoo` -> `172.19.0.11`
- `frontend` -> `172.19.0.20`

Subnet usada:

- `172.19.0.0/16`

Regla operativa:

- no usar IP publica del VPS en `proxy_pass`
- no depender de `127.0.0.1` si el proxy del host pierde acceso estable al publish de Docker
- en dominios productivos de Hestia, apuntar a IP interna fija del contenedor

### Proxy correcto para API

`api.incasparadise.com` debe apuntar a:

- `http://172.19.0.10:1336`

### Proxy correcto para Odoo

`odoo.incasparadise.com` debe apuntar a:

- rutas normales -> `http://172.19.0.11:8069`
- websocket -> `http://172.19.0.11:8072`

### Nota importante de Odoo

Para que Odoo funcione detras de proxy:

- `proxy_mode = True`
- `workers = 2`
- `gevent_port = 8072`
- `client_max_body_size 600M;` en el vhost/proxy si se suben videos por DMS

Y en `docker-compose.prod.yaml` el servicio `odoo` debe publicar:

- `8070:8069`
- `8072:8072`

Si Odoo devuelve error de websocket tipo:

`Couldn't bind the websocket. Is the connection opened on the evented port (8072)?`

revisar que `location /websocket` del vhost no siga apuntando a `8070`.

## Orden recomendado de arranque en produccion

Para levantar servicios manualmente:

```bash
docker compose -f docker-compose.prod.yaml up -d postgres
docker compose -f docker-compose.prod.yaml up -d backend
docker compose -f docker-compose.prod.yaml up -d odoo_db
docker compose -f docker-compose.prod.yaml up -d odoo
docker compose -f docker-compose.prod.yaml up -d frontend
```

## Datos que conviene completar despues

Este documento ya deja clara la estructura base del VPS. Conviene completar cuando el equipo lo confirme:

- usuario del VPS
- dominio o IP
- comando exacto para reiniciar servicios
- si se usa `docker compose`, `pm2` o `systemd`
- ubicacion del `.env` en cada entorno
- politica de backups y rollback

## Riesgos operativos

- hacer `git pull` en la carpeta equivocada puede mezclar entornos
- subir directo a `main` sin validar en `test` aumenta el riesgo de regresiones
- si hay cambios locales sin commitear en el VPS, el `git pull` puede fallar o dejar el repo en estado inconsistente
