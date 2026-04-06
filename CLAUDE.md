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
  reserva/            # Reservations (tiene estado_pago + relación oneToMany → pago)
  pago/               # Transacciones de pago (PayPal / IziPay)
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
`destino`, `destino-detalle`, `reserva`, `style-trip`, `tour-detalle`, `transporte`, `tipo-transporte`, `vehiculo`, `pago`

## Módulo de pagos

### Modelos
- `reserva` tiene `estado_pago` (enum: `pendiente`, `pagado`, `fallido`) y relación `oneToMany` → `pago`
- `pago`: `proveedor` (`paypal` | `izipay`), `metodo` (`paypal` | `tarjeta` | `yape_qr`), `moneda` (`PEN` | `USD` | `EUR`), `monto`, `estado`, `transaccion_id`, `orden_id`, `qr_url`, `fecha_pago`, `ip_cliente`
- Una reserva puede tener múltiples pagos (reintentos). `estado_pago` en reserva es resumen de conveniencia.

### Pasarelas
- **PayPal** — implementado. SDK JS en frontend + REST API v2 en backend.
- **IziPay Vpos** — skeleton listo (`izipay.ts`). Pendiente credenciales (`IZIPAY_SHOP_ID`, `IZIPAY_SECRET_KEY`).

### Arquitectura backend (gateway unificado)
```
backend/src/api/pago/
  services/
    paypal.ts      # getAccessToken, crearOrden, capturarOrden, verificarWebhook
    izipay.ts      # skeleton: crearTokenTarjeta, crearQrYape, verificarPago
    gateway.ts     # router unificado: iniciarPago(proveedor, monto, moneda) / confirmarPago(proveedor, token)
  routes/
    pago-custom.ts # POST /pagos/iniciar | /pagos/confirmar | /pagos/webhook (auth: false)
  controllers/
    pago.ts        # iniciar → confirmar (crea reserva + pago) → webhook
```

### Endpoints custom (todos `auth: false`)
| Endpoint | Body | Respuesta |
|---|---|---|
| `POST /api/pagos/iniciar` | `{ proveedor, monto, moneda }` | `{ orderID }` PayPal / `{ token, qrUrl }` IziPay |
| `POST /api/pagos/confirmar` | `{ proveedor, token, reservaData }` | `{ ticket }` |
| `POST /api/pagos/webhook` | payload del proveedor | `{ received: true }` |

### Flujo completo de pago
1. Usuario llena el formulario en `BookingModal` → clic "Continuar al pago"
2. Datos guardados en `window.__pendingBooking` (en memoria, sin redirect)
3. Usuario elige método (PayPal / Yape QR / Tarjeta)
4. **PayPal:** SDK JS carga dinámicamente → `createOrder` llama `/api/pagos/iniciar` → popup PayPal → `onApprove` llama `/api/pagos/confirmar` con `reservaData`
5. **IziPay (pendiente):** mismo patrón — `iniciar` devuelve token/QR → `confirmar` captura
6. El endpoint `confirmar` en Strapi: captura el pago → genera ticket → crea `reserva` (con `publishedAt`) → crea registro `pago` → retorna `{ ticket }`
7. Frontend muestra modal de éxito con el ticket

### Gotchas importantes
- `reserva` tiene `draftAndPublish: true` → al crear vía Document Service incluir `publishedAt: new Date().toISOString()` o quedará en draft
- PayPal **no acepta PEN** → convertir a USD usando `tasaCambio` antes de llamar a `iniciarPago`
- `PAYPAL_CLIENT_ID` es el mismo valor para backend y frontend — el frontend lo necesita como `PUBLIC_PAYPAL_CLIENT_ID`
- El lifecycle `afterCreate` de `reserva` hace sync con Google Sheets automáticamente — se ejecuta igual al crear desde el controller de pago
- Al agregar IziPay: solo crear lógica en `izipay.ts` y agregar `IZIPAY_SHOP_ID`/`IZIPAY_SECRET_KEY` en `.env` — el gateway y los endpoints no cambian

### Variables de entorno (`.env` raíz)
```
PAYPAL_CLIENT_ID=          # también usado como PUBLIC_PAYPAL_CLIENT_ID en frontend
PAYPAL_SECRET=             # solo backend
PAYPAL_MODE=sandbox        # sandbox | live
PAYPAL_WEBHOOK_ID=         # se obtiene al registrar webhook en dashboard PayPal
PUBLIC_PAYPAL_CLIENT_ID=   # mismo valor que PAYPAL_CLIENT_ID
# Futuro IziPay:
# IZIPAY_SHOP_ID=
# IZIPAY_SECRET_KEY=
# IZIPAY_MODE=TEST
```

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
