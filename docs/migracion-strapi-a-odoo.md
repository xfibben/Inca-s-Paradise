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
- `Strapi` puede mantenerse temporalmente como CMS durante la transicion.
- Las integraciones deben hacerse por API, jobs o procesos de importacion controlados.

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
- Ya existe catálogo local en Odoo para no depender de tablas externas.
- Modelos ya creados en Odoo:
  - `incas.servicio.catalogo`
  - `incas.estilo.transporte`
  - `incas.cotizacion`
  - `incas.reserva`
  - `incas.pasajero`

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

- `Cotización` y `Reserva` usan catálogo local Odoo.
- Ambas manejan:
  - `tour o transporte`
  - `tipo de tour`
  - `estilo de transporte`
  - `servicio`
  - `nombre del servicio`
  - `precio adulto`
  - `precio niño`
  - `descuento`
  - `cantidad adultos`
  - `cantidad niños`
  - `monto total`
- `Reserva` copia esos datos desde `Cotización`.

## Regla de cálculo ya aplicada en Odoo

- `monto_total` no es manual.
- Se calcula con:
  - (`cantidad_adultos` * `precio_adulto`) + (`cantidad_ninos` * `precio_nino`)
  - menos `descuento` como porcentaje

## Limitación actual importante

- En tours, el mapeo actual ya es correcto a nivel de precio adulto, precio niño y descuento.
- En transportes, hoy se está tomando temporalmente la primera entrada de `precios[]`.
- Eso es solo una etapa intermedia.
- El modelo final debe contemplar precio de transporte por `vehiculo`.

## Regla futura para la migración completa

- No migrar transporte como servicio con precio único.
- Crear en Odoo:
  - modelo de vehículo
  - relación entre transporte y vehículo
  - precios por vehículo
  - descuento por combinación de transporte y vehículo
- Al migrar reservas de transporte, conservar también `vehiculo_seleccionado`.

## Siguiente paso recomendado

1. crear modelo de vehículo en Odoo
2. modelar precios de transporte por vehículo
3. dejar de tratar transporte como un servicio de precio único
4. migrar reservas conservando:
   - adultos
   - niños
   - descuento
   - vehículo seleccionado

## Fuentes oficiales

- Importación de datos e imágenes en Odoo 19:
  - https://www.odoo.com/documentation/19.0/applications/essentials/export_import_data.html
- Importación de productos en Odoo 19:
  - https://www.odoo.com/documentation/19.0/applications/sales/sales/products_prices/products/import.html
