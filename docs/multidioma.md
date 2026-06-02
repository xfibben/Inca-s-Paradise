# Multidioma

## 1. Idiomas de ruta

- `es`
- `en`
- `pt`
- `fr`
- `it`

Idioma por defecto:

- `es`

## 2. Dos capas de idioma

### Interfaz

Vive en:

- `frontend/src/i18n/es.json`
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/pt.json`
- `frontend/src/i18n/fr.json`
- `frontend/src/i18n/it.json`

Responsable:

- labels
- botones
- textos UI
- mensajes locales

### Contenido

Vive en Odoo y se serializa por `lang`.

Responsable:

- nombres de tours
- nombres de destinos
- contenido legal
- contenido corporativo
- sostenibilidad
- descripciones y SEO

## 3. Cómo resuelve el frontend

Helpers:

- `frontend/src/utils/odooWeb.ts`
- `frontend/src/utils/odooTransport.ts`

Funciones:

- normalizan `lang`
- generan `es|en|pt|fr|it`
- piden el payload correcto a Odoo

## 4. Cómo resuelve Odoo

Controlador:

- `odoo/addons/incas_reservas/controllers/api.py`

Usa:

- `_lang_base(lang)`
- `_campo_localizado(record, campo, lang)`

Regla:

- si existe campo específico para idioma, lo usa
- si no existe, cae al base español

## 5. Cobertura real

Interfaz:

- `es/en/pt/fr/it` completa

Contenido Odoo:

- fuerte en `es`
- habitual en `en`
- parcial en `pt`
- `fr/it` muchas veces son fallback

## 6. Middleware

Archivo:

- `frontend/src/middleware.ts`

Hace:

- redirect de `es-pe`, `en-us`, `pt-br`, etc.
- 404 a locales inválidos
- redirects de rutas antiguas

## 7. Qué revisar si un idioma falla

1. URL final después del middleware
2. JSON local del frontend
3. payload Odoo con `?lang=...`
4. campos por idioma en el modelo Odoo
5. fallback real en la serialización

## 8. Buenas prácticas

- no inventar nuevos códigos de idioma en rutas
- mantener mismas keys en todos los JSON
- no cambiar slugs localizados sin revisar enlaces
- validar `fr/it` después de cualquier cambio de contenido
