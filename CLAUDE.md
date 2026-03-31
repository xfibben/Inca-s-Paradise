# Inca's Paradise

Tourism platform for Peruvian destinations. Booking, tours, style-trips, multi-language.

## Stack
- **Frontend:** Astro 5 (SSR) + Tailwind CSS 4 + Flowbite — `/frontend`
- **Backend:** Strapi 5 (Headless CMS) + PostgreSQL 14 — `/backend`
- **Deploy:** Docker Compose (postgres:5432, strapi:1337, astro:4321)

## i18n
5 languages: `es` (default), `en`, `pt`, `fr`, `it`
Routes: `/[lang]/...` — translations at `frontend/src/i18n/*.json`

## Key directories
```
frontend/src/
  pages/[lang]/       # i18n routes
  components/
    LandingPage/      # Home sections
    shared/           # Navbar, Footer, LanguageSwitcher
    stylestrips/      # Style-trips UI
    tours/            # Tour UI
    terminos/         # Terminos y condiciones 
  data/               # Static destination/tour data (es/en)
  i18n/               # Translation files + UBIGEO JSON

backend/src/api/
  destino/            # Destinations
  destino-detalle/    # Destination details
  reserva/            # Reservations
  style-trip/         # Style trips
  terminos/condiciones/ #Terminos y condiciones
  tour-detalle/       # Tour details
  tipo-transporte/    # Kind of transport
  transporte/         # Transport routes
  vehiculo/           # Vehicle types (Expedition, Observatory, Vistadome 33)

backend/src/components/
  tours/              # Tour-related components
  destinos/           # Destination-related components
  legal/              # Terms components
  transporte/         # precio-vehiculo (vehiculo relation + precio)
```

## Content types (Strapi)
`destino`, `destino-detalle`, `reserva`, `style-trip`, `tour-detalle`, `transporte`, `tipo-transporte`, `vehiculo`

## Transporte / Vehículo model
- `vehiculo`: nombre, descripcion, imagen, features (repeatable `tours.inclusion-item`)
- `transporte` tiene campo `precios` (repeatable component `transporte.precio-vehiculo`)
  - cada entrada: `vehiculo` (manyToMany → vehiculo) + `precioAdulto` (decimal) + `precioNino` (decimal)
- La tabla comparativa en `/tipo-transporte` usa estos datos: filas = rutas, columnas = vehículos

## Color scheme
- **Transporte pages** usan el verde `#1AA093` (hover `#0e8a7e`, fondo suave `#e0f7f5`) — el mismo que BookingCard y BookingModal. No usar amber/naranja en páginas de transporte o tipo-transporte.

## Conventions
- Astro components use `.astro`, data files use `.ts` or `.json`
- Images served via Strapi media or local `/public`
- SEO handled by `components/SEO/`
- Geographic data (UBIGEO) in `frontend/src/i18n/ubigeo_*.json`

## Idioma
Siempre responder en español.

## Response style
- Be concise. Skip summaries of what you just did.
- Don't add comments, docstrings, or type annotations to unchanged code.
- Don't refactor beyond what's asked.
- Prefer editing existing files over creating new ones.
- Always coment my code in Spanish
