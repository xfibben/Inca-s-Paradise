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
```

## Content types (Strapi)
`destino`, `destino-detalle`, `reserva`, `style-trip`, `tour-detalle`

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
