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
