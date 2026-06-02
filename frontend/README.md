# Frontend Inca's Paradise

Esta carpeta contiene el sitio público SSR.

Documentación principal:

- [README raíz](../readme.md)
- [Arquitectura](../docs/arquitectura-actual.md)
- [Frontend](../docs/frontend.md)
- [Reservas y pagos](../docs/reservas-y-pagos.md)
- [Multidioma](../docs/multidioma.md)

## Comandos

```bash
npm install
npm run dev
npm run build
npm run preview
```

## Archivos clave

- `src/pages/[lang]/tours/[tour].astro`
- `src/pages/[lang]/transporte/[slug].astro`
- `src/components/tours/BookingCard.astro`
- `src/components/tours/BookingModal.astro`
- `src/utils/odooWeb.ts`
- `src/utils/odooTransport.ts`
- `src/middleware.ts`
