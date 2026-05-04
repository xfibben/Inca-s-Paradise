# Migracion Strapi a Odoo

## Objetivo

Migrar el backend operativo desde Strapi hacia Odoo sin hacer una migracion directa de base de datos a base de datos.

## Regla principal

- No migrar tablas directamente.
- Migrar datos por extraccion, transformacion e importacion.
- Strapi actua como fuente de extraccion.
- Odoo actua como destino funcional y operativo.

## Arquitectura recomendada

- `Astro` sigue como frontend publico.
- `Odoo` pasa a ser el backend operativo principal.
- `Strapi` queda como CMS durante la transicion y luego solo como CMS si se mantiene.
- Las integraciones deben hacerse por API, jobs o procesos de importacion controlados.

## Flujo transaccional objetivo

- `Strapi` crea y mantiene contenido.
- `Astro` consulta contenido a Strapi.
- `Astro` envía reservas y pagos a Odoo.
- `Odoo` procesa:
  - creación de reserva
  - registro de pago
  - ticket
  - comprobante PDF
  - correos
  - sincronización a Google Sheets

## Estado actual de la transición

- El frontend ya quedó preparado para usar `PUBLIC_ODOO_URL` en el flujo de reservas y pagos.
- `PUBLIC_ODOO_URL` debe definirse en el `.env` raíz.
- `PUBLIC_ODOO_URL` se pasa al frontend desde `docker-compose.yaml` y `docker-compose.prod.yaml`.
- Odoo ya expone:
  - `GET /incas/api/pagos/tipo-cambio`
  - `POST /incas/api/pagos/iniciar`
  - `POST /incas/api/pagos/confirmar`
  - `POST /incas/api/reservas`
- Se validó localmente la creación real de una reserva pública en Odoo.
- Odoo devuelve `ticket`, `reserva_id` y `voucher_url`.
- El comprobante PDF público se entrega por URL con token.
- El tipo de cambio ya vive en Odoo y se guarda en `res.currency.rate`.
- Las tasas se actualizan desde API externa y Odoo las expone al frontend.
- La dependencia transaccional con Strapi ya no pasa por el tipo de cambio.
- Módulos reales ya presentes en Odoo:
  - `incas_core`
  - `incas_documentos`
  - `incas_reservas`
  - `incas_operaciones`
  - `incas_postventas`
  - `incas_tesoreria`

## Orden recomendado de migracion

1. Catalogos base
2. Tours
3. Tipos de transporte
4. Transportes
5. Clientes y contactos
6. Cotizaciones y reservas
7. Pagos
8. Operaciones
9. Imagenes y media restante

## No recomendado

- copiar la base de PostgreSQL de Strapi dentro de Odoo
- relacionar Odoo directo con tablas de Strapi
- mezclar como fuente maestra a Strapi y Odoo indefinidamente

## Estrategia ETL

### Extraccion

- leer datos desde la API de Strapi
- descargar relaciones y media
- conservar `id`, `documentId`, `slug`, `locale`, `publishedAt`

### Transformacion

- mapear content types de Strapi a modelos Odoo
- crear claves de trazabilidad con `strapi_id`
- normalizar enums, relaciones y catálogos
- separar contenido operativo de contenido editorial

### Carga

- importar primero catálogos
- luego relaciones
- luego transaccionales
- luego imágenes
- validar al final

## Imagenes

### Opcion recomendada

Importar las imagenes a Odoo.

Proceso:

1. generar archivo CSV o XLSX con columna de imagen
2. poner en la columna el nombre exacto del archivo
3. subir el archivo de datos
4. subir los archivos de imagen en `Files to import`
5. Odoo vincula los archivos por nombre

Documentacion oficial:

- https://www.odoo.com/documentation/19.0/applications/essentials/export_import_data.html

### Opcion temporal

Mantener URLs de Strapi durante una fase de transicion, pero no como solucion final.

## Modelos del proyecto que requieren cuidado especial

### Tour Detalle en Strapi

Campos importantes detectados:

- `title`
- `slug`
- `tourType`
- `adultUnitPrice`
- `childUnitPrice`
- `discount`

### Transporte en Strapi

Campos importantes detectados:

- `nombre`
- `slug`
- `tipos_transporte`
- `precios[]`

### Componente de precios de transporte

Cada transporte puede tener entradas en `precios` con:

- `precioAdulto`
- `precioNino`
- `descuento`
- `vehiculo`

Esto significa que el precio de transporte no es un precio simple. Puede depender del vehículo.

### Reserva en Strapi

Campos importantes detectados:

- `cantidad_adultos`
- `cantidad_ninos`
- `descuento`
- `precio_tour`
- `precio_adulto_web`
- `precio_nino_web`
- `monto_estimado`
- `monto_web`
- `pago_restante`
- `monto_final`
- `estado_pago`
- `vehiculo_seleccionado`

## Regla funcional de precios

- Los precios no son solo un monto total.
- Deben conservarse:
  - precio adulto
  - precio niño
  - descuento
- En transporte, si el precio depende de vehículo, ese nivel de detalle debe modelarse en Odoo.

## Estado actual en Odoo

Actualmente el catálogo sincronizado en Odoo ya contempla:

- `tour o transporte`
- `tipo de tour`
- `estilo de transporte`
- `precio adulto`
- `precio niño`
- `descuento`

## Avance real ya implementado

- Existe módulo `incas_core` como base del BO.
- Existe módulo `incas_reservas` como primera implementación funcional.
- Existe `incas_documentos` como capa transversal documental sobre `dms`.
- Existe `incas_operaciones` como base de agenda y tareas operativas.
- Existe `incas_postventas` como base de casos, encuestas, reclamos y acciones.
- Existe `incas_tesoreria` como base inicial de movimientos de caja.
- Ya existe catálogo local en Odoo para no depender de tablas externas.
- Modelos ya creados en Odoo:
  - `incas.servicio.catalogo`
  - `incas.estilo.transporte`
  - `incas.cotizacion`
  - `incas.reserva`
  - `incas.pasajero`
  - `incas.pago`
  - `incas.catalogo.vehiculo`
  - `incas.agenda.evento`

## Qué ya se está jalando desde Strapi

### Tours

Desde `tour-detalle` ya se están trayendo:

- `title`
- `slug`
- `tourType`
- `adultUnitPrice`
- `childUnitPrice`
- `discount`

### Transportes

Desde `transporte` ya se están trayendo:

- `nombre`
- `slug`
- `tipos_transporte`
- datos de `precios[]`

### Tipos de transporte

Desde `tipo-transporte` ya se están trayendo:

- nombres de estilo de transporte
- slugs cuando existen

## Cómo quedó modelado hoy en Odoo

- `Cotización` usa catálogo local Odoo.
- La selección comercial ahora vive en líneas de `Paquete`.
- Cada línea del paquete referencia un servicio base de Odoo.
- Cada línea guarda un snapshot editable del contenido del servicio.
- Ese snapshot es propio de la cotización y no modifica Strapi.
- `Reserva` toma su resumen comercial desde `Cotización`.

## Flujo funcional actual

### Cotización

- una cotización puede tener una o varias líneas en `Paquete`
- cada línea puede ser `tour` o `transporte`
- cada línea copia al crearse:
  - nombre
  - precios
  - descuento
  - contenido descriptivo
  - itinerario o bloques equivalentes
- luego ese contenido puede editarse solo para esa cotización

### Reserva BO

- la reserva se vincula a una cotización
- la reserva toma desde la cotización:
  - tipo resumido del servicio
  - nombre comercial
  - precios
  - descuento
  - importes convertidos por moneda

### Reserva web

- la web sigue permitiendo reservar un solo servicio
- Odoo convierte esa selección en una cotización interna con una sola línea de paquete
- después crea la reserva desde esa cotización
- con eso el flujo web y el flujo BO usan el mismo modelo funcional

## Regla de resumen

- si la cotización tiene una sola línea:
  - el resumen conserva `tour` o `transporte`
- si la cotización tiene varias líneas:
  - el resumen pasa a `paquete`
- el monto total se calcula con la suma neta de líneas del paquete

## Regla de cálculo ya aplicada en Odoo

- `monto_total` no es manual.
- Se calcula con:
  - (`cantidad_adultos` * `precio_adulto`) + (`cantidad_ninos` * `precio_nino`)
  - menos `descuento` como porcentaje
- `saldo_pendiente` es el saldo real actual en Odoo.
- `pago_restante` se conserva solo por compatibilidad histórica con Strapi.

## Limitaciones actuales importantes

- En tours, el mapeo actual ya es correcto a nivel de precio adulto, precio niño y descuento.
- En transportes, Odoo ya contempla vehículo y tarifas leídas desde `precios[]`.
- Lo que falta no es el dato base sino endurecer su explotación operativa:
  - validaciones
  - procesos internos
  - reportes
  - consistencia entre reservas, operación y tesorería
- IziPay sigue pendiente de implementación real.
- Falta un módulo explícito de integraciones con jobs, logs, retry y monitoreo.
- La media y parte del contenido editorial siguen viviendo en Strapi.

## Regla futura para la migración completa

- No migrar contenido operativo leyendo tablas directas de Strapi.
- Mantener:
  - catálogo local Odoo
  - trazabilidad por `strapi_id` y `documentId`
  - reserva operativa naciendo en Odoo
- Al migrar reservas de transporte, conservar también `vehiculo_seleccionado`.

## Siguiente paso recomendado

1. formalizar `incas_integraciones` para sync, logs y jobs observables
2. completar `incas_operaciones` con asignaciones reales, incidencias y responsables externos
3. cerrar `incas_postventas` con automatización de encuestas, SLA y seguimiento
4. ampliar `incas_tesoreria` hacia caja real, conciliación y vínculo fuerte con pagos
5. implementar IziPay real en Odoo
6. preparar `incas_facturacion` con localización Perú y SUNAT

## Fuentes oficiales

- Importación de datos e imágenes en Odoo 19:
  - https://www.odoo.com/documentation/19.0/applications/essentials/export_import_data.html
- Importación de productos en Odoo 19:
  - https://www.odoo.com/documentation/19.0/applications/sales/sales/products_prices/products/import.html
