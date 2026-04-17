# Guia de multidioma

## Idiomas soportados

- `es` - idioma por defecto
- `en`
- `pt`
- `fr`
- `it`

## Como funciona

El sitio combina dos capas:

1. Traducciones locales en el frontend.
2. Locales configurados en Strapi para contenido administrable.

## Frontend

Archivos principales:

- [frontend/src/i18n/index.ts](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/index.ts)
- [frontend/src/i18n/es.json](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/es.json)
- [frontend/src/i18n/en.json](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/en.json)
- [frontend/src/i18n/pt.json](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/pt.json)
- [frontend/src/i18n/fr.json](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/fr.json)
- [frontend/src/i18n/it.json](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/i18n/it.json)

Comportamiento:

- `defaultLanguage` es `es`
- `languages` tiene fallback local
- `fetchLanguagesFromBackend()` consulta `GET /api/locales`
- Si falla esa consulta, el sitio sigue con el fallback local

## Middleware de idioma

Archivo:

- [frontend/src/middleware.ts](/Users/arturo/Documents/Inca-s-Paradise/frontend/src/middleware.ts)

Responsabilidades:

- Validar segmentos de idioma en la URL
- Redirigir variantes como `es-pe` a `es`
- Redirigir rutas antiguas
- Devolver `404` para locales invalidos con formato de idioma
- Aplicar headers de cache

## Backend

Ruta custom:

- `GET /api/locales`

Archivos:

- [backend/src/api/locales/controllers/locale-controller.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/locales/controllers/locale-controller.ts)
- [backend/src/api/locales/routes/get-locales.ts](/Users/arturo/Documents/Inca-s-Paradise/backend/src/api/locales/routes/get-locales.ts)

La respuesta devuelve los locales del plugin i18n de Strapi en formato simplificado.

## Cuando agregar un idioma nuevo

1. Crear el JSON nuevo en `frontend/src/i18n/`.
2. Importarlo en `frontend/src/i18n/index.ts`.
3. Agregar el idioma al fallback local.
4. Agregar el codigo a `VALID_LANGS` en `frontend/src/middleware.ts`.
5. Configurar el locale en Strapi.
6. Verificar rutas `/[lang]/...`.
7. Confirmar que navbar, footer y selector de idioma lo exponen.

## Buenas practicas

- Mantener las mismas keys en todos los JSON.
- No mezclar nombres de locale largos en rutas del frontend.
- Usar siempre el codigo corto en el sitio: `es`, `en`, `pt`, `fr`, `it`.
- Si una traduccion falta, revisar primero el JSON local y luego la configuracion i18n de Strapi.

## Para contenido y operaciones

- Textos de interfaz: frontend JSON
- Contenido editable del negocio: Strapi
- Si un cambio no aparece en el sitio, validar en que capa vive ese texto antes de corregirlo
