# Roadmap BO Odoo

## Objetivo

Construir el back office de Inca's Paradise sobre Odoo como base ERP/CRM, iniciando por reservas y operaciones, y creciendo de forma controlada hacia un ERP más completo.

## Principios

- Odoo será el back office principal.
- Astro + Strapi seguirán siendo el canal web público.
- No compartir base de datos entre Strapi y Odoo.
- La integración entre ambos sistemas se hará por API, jobs o sincronización controlada.
- Primero resolver reservas y operaciones.
- Facturación, SUNAT, contabilidad, RRHH e inventario se implementarán por fases.
- Evitar replicar en custom code lo que Odoo estándar ya resuelve bien.

## Arquitectura objetivo

- `Odoo 19` como BO principal.
- `PostgreSQL` separado para Odoo.
- Módulos propios de la empresa dentro de `addons/`.
- Separación clara entre:
  - sistema público web
  - gestión comercial y operativa interna
  - integraciones

## Fase 0 - Base técnica

### Objetivo

Dejar Odoo listo para crecer sin rehacer infraestructura.

### Incluye

- Odoo en Docker para test y producción.
- PostgreSQL separado para Odoo.
- `odoo.conf`.
- estructura base de `addons/`.
- estrategia de backups.
- dominios y proxy reverso.
- usuarios administradores iniciales.
- contraseña maestra y lineamientos de seguridad.

### Entregables

- stack Odoo estable
- configuración persistente
- estructura de módulos propia
- guía de despliegue y operación

## Fase 1 - Núcleo funcional mínimo

### Objetivo

Cubrir el flujo principal del negocio turístico desde cotización hasta reserva confirmada.

### Módulos

- `incas_core`
- `incas_reservas`

### Incluye

- clientes
- pasajero principal
- pasajeros
- cotizaciones
- reservas
- estados de reserva
- observaciones
- historial de cambios
- calendario de reservas
- pagos básicos
- vouchers de reserva
- envío de correos
- filtros y búsquedas
- vistas tipo lista, formulario, calendario y kanban

### Flujo esperado

Lead o contacto -> cotización -> reserva -> pago -> voucher -> seguimiento

### Entregables

- modelo de datos base
- pantallas internas de reservas
- estados operativos iniciales
- reportes iniciales

## Fase 2 - Operaciones

### Objetivo

Controlar la ejecución real de los servicios vendidos.

### Módulos

- `incas_operaciones`

### Incluye

- servicios operativos derivados de reservas
- asignación de guías
- asignación de operadores y proveedores
- agenda operativa
- endosos
- vouchers operativos
- incidencias
- cambios operativos
- seguimiento del servicio
- responsables internos y externos

### Entregables

- tablero de operaciones
- agenda de servicios
- trazabilidad de incidencias
- control de responsables por servicio

## Fase 3 - Integración con la web actual

### Objetivo

Conectar la plataforma pública con el BO sin mezclar responsabilidades.

### Incluye

- sincronización de clientes
- sincronización de reservas
- sincronización de pagos
- sincronización o replicación controlada de tours y productos
- definición de sistema maestro por entidad
- jobs y logs de sincronización

### Regla

- Strapi sigue siendo fuente de contenido público.
- Odoo pasa a ser fuente operativa para reservas, clientes y proceso interno.

### Entregables

- contrato de integración
- mapeo de entidades
- proceso de sincronización inicial

## Fase 4 - Facturación y capa fiscal

### Objetivo

Formalizar el flujo comercial y tributario.

### Incluye

- facturas y boletas
- localización Perú
- SUNAT
- documentos tributarios
- series
- impuestos
- conciliación básica con pagos

### Nota

Esta fase requiere validación funcional y contable real.

## Fase 5 - Contabilidad e inventario

### Objetivo

Ampliar el control financiero y operativo de la empresa.

### Incluye

- contabilidad
- cuentas por cobrar
- cuentas por pagar
- compras
- inventario
- productos internos
- control de consumos o insumos
- reportes financieros base

## Fase 6 - RRHH y gestión interna

### Objetivo

Llevar el control interno del personal y procesos.

### Incluye

- empleados
- asistencia
- horarios
- permisos
- planificación
- tareas
- procesos internos
- evaluación de desempeño

### Nota

Si se implementa nómina, debe revisarse con criterio legal peruano.

## Fase 7 - Marketing y expansión ERP

### Objetivo

Conectar operación, ventas y fidelización.

### Incluye

- CRM avanzado
- automatizaciones comerciales
- campañas
- segmentación
- seguimiento post venta
- tableros gerenciales

## Módulos propios previstos

- `incas_core`
- `incas_reservas`
- `incas_operaciones`
- `incas_pagos`
- `incas_facturacion`
- `incas_rrhh`
- `incas_integraciones`

## Criterios de diseño

- nombres funcionales en español para modelos de negocio propios
- permisos por rol desde el inicio
- bitácora y trazabilidad desde el inicio
- evitar lógica crítica escondida en automatizaciones no documentadas
- cada fase debe quedar operativa antes de abrir la siguiente

## Estado actual

- Odoo ya está incorporado en Docker para test y producción.
- Existe estructura local de Odoo en el repo:
  - `odoo/config/odoo.conf`
  - `odoo/addons/`
- Ya existe el módulo `incas_core` como base del BO.
- Ya existe el módulo `incas_reservas` como primera capa funcional.
- El menú principal del BO es `Inca's Paradise`.
- La base Odoo actual de trabajo es `odoo_incas`.
- El flujo transaccional web ya empezó a migrarse desde Strapi hacia Odoo.

## Avance real implementado

### Fase 0 completada en lo esencial

- Odoo 19 corriendo en Docker Compose.
- PostgreSQL separado para Odoo.
- Configuración persistente con `odoo.conf`.
- Carpeta local de addons custom lista para crecer.
- Separación técnica entre Strapi y Odoo mantenida.

### Fase 1 iniciada

## Flujo actual implementado en Odoo

- `Cotización` pasó a ser la fuente de verdad del servicio vendido.
- La pestaña `Paquete` en cotización maneja líneas locales editables.
- La cotización ahora maneja pestañas separadas de `Hoteles` y `Extras` con listas editables al mismo nivel que `Paquete`.
- Cada línea del paquete copia un snapshot del servicio sincronizado desde Strapi.
- Ese snapshot incluye precios y contenido editable por cotización.
- Editar una línea del paquete no modifica Strapi ni el catálogo local base.
- El PDF `detalle paquete` sale desde el snapshot guardado en la línea de cotización.
- El resumen del PDF `detalle paquete` se renderiza en formato tabla.

## Regla operativa actual

- Si la cotización tiene una sola línea de paquete:
  - el flujo se comporta como un `tour` o `transporte` individual
  - se conserva el tipo del servicio original
- Si la cotización tiene más de una línea de paquete:
  - el flujo se comporta como `paquete`
  - el resumen comercial se calcula como suma de líneas

## Flujo reserva desde BO

- Usuario crea o edita una `cotización`.
- Usuario agrega una o varias líneas en `Paquete`.
- Usuario puede agregar una o varias líneas en `Hoteles`.
- Usuario puede agregar una o varias líneas en `Extras`.
- Cada línea puede abrirse en una ventana modal para editar:
  - nombre
  - precios
  - descuento
  - descripciones
  - itinerario
  - bloques de contenido del tour o transporte
- Los montos de hotel y extra se calculan como suma de sus líneas.
- La `reserva` toma sus importes y resumen desde la `cotización`.
- La `reserva` ya no debe considerarse la fuente primaria del servicio comercial.

## Flujo reserva desde web

- Astro envía la reserva a Odoo.
- Odoo busca el servicio sincronizado en el catálogo local.
- Odoo crea primero una `cotización` interna.
- Esa cotización se crea con una sola línea en `Paquete`.
- Luego Odoo crea la `reserva` asociada a esa cotización.
- Con eso, el flujo web y el flujo BO comparten la misma base funcional.

#### `incas_core`

- Estructura base del BO.
- Menú raíz `Inca's Paradise`.
- Grupos y privilegios base:
  - `Administrador BO`
  - `Reservas`
  - `Operaciones`
  - `Gerencia`
- Compatibilidad ajustada a Odoo 19 usando `res.groups.privilege`.

#### `incas_reservas`

- Modelos creados:
  - `incas.cotizacion`
  - `incas.reserva`
  - `incas.pasajero`
  - `incas.servicio.catalogo`
  - `incas.estilo.transporte`
- Vistas base de cotizaciones, reservas y pasajeros.
- Secuencias iniciales para cotización y reserva.
- Permisos de acceso para grupos del BO y administradores de Odoo.

### Catálogo comercial sincronizado desde Strapi

- Ya existe un catálogo local en Odoo para evitar depender directo de tablas de Strapi.
- El catálogo actual sincroniza desde la API de Strapi:
  - tours
  - transportes
  - estilos de transporte
- Campos ya sincronizados en Odoo:
  - `tour o transporte`
  - `tipo de tour`
  - `estilo de transporte`
  - `servicio`
  - `precio adulto`
  - `precio niño`
  - `descuento`

### Lógica funcional ya implementada en cotización y reserva

- `Cotización` y `Reserva` manejan:
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
- Al seleccionar una cotización en una reserva, los campos comunes se copian automáticamente.
- Al seleccionar un servicio, se autocompletan:
  - `nombre del servicio`
  - `precio adulto`
  - `precio niño`
  - `descuento`
- Los campos que quedan manuales para cálculo son:
  - `cantidad adultos`
  - `cantidad niños`

### Regla de cálculo actual

- `monto_total` se calcula así:
  - subtotal = (`cantidad_adultos` * `precio_adulto`) + (`cantidad_ninos` * `precio_nino`)
  - descuento = porcentaje aplicado sobre el subtotal
  - monto total = subtotal menos descuento

## Pendientes inmediatos

- Crear flujo formal `cotización -> reserva`.
- Modelar precios de transporte por vehículo en Odoo.
- Dejar de tratar transporte como servicio de precio único.
- Crear `incas_operaciones`.
- Definir vouchers, pagos internos y reportes del BO.

## Nota crítica de migración

- La migración futura desde Strapi a Odoo no debe hacerse copiando bases de datos.
- La estrategia correcta sigue siendo:
  - extracción
  - transformación
  - importación
- El mayor punto pendiente de modelado es transporte por vehículo, porque en Strapi el precio de transporte depende de `vehiculo`.

## Historial de avance

### 2026-04-23

- Se incorporó Odoo 19 al `docker-compose` de test y producción.
- Se dejó PostgreSQL separado para Odoo.
- Se creó la estructura local:
  - `odoo/config/`
  - `odoo/addons/`
- Se configuró `odoo.conf` y montaje de addons custom.
- Se creó el módulo `incas_core`.
- Se creó el menú raíz `Inca's Paradise`.
- Se ajustó seguridad de `incas_core` para Odoo 19 con `res.groups.privilege`.
- Se creó el módulo `incas_reservas`.
- Se implementaron modelos de:
  - cotización
  - reserva
  - pasajero
  - catálogo de servicios
  - estilos de transporte
- Se implementaron vistas base y permisos del módulo de reservas.
- Se habilitó acceso también para administradores de Odoo (`base.group_system`).
- Se sincronizó catálogo local desde Strapi por API.
- Se empezó a traer desde Strapi:
  - tours
  - transportes
  - tipos de transporte
  - precio adulto
  - precio niño
  - descuento
- Se cambió el modelo para usar `servicio` como catálogo local Odoo en vez de texto libre.
- Se agregó copia automática de datos de `cotización` hacia `reserva`.
- Se definió cálculo automático de `monto total` con:
  - cantidad de adultos
  - cantidad de niños
  - precio adulto
  - precio niño
  - descuento porcentual
- Se dejó USD como moneda base interna para precios en cotización y reserva.
- Se conectó Odoo al endpoint `GET /api/pagos/tipo-cambio` del backend para convertir precios en tiempo real a:
  - `PEN`
  - `USD`
  - `EUR`
- Al cambiar la moneda en cotización o reserva, se recalculan:
  - `precio adulto`
  - `precio niño`
  - `monto total`
- Se dejó documentada la estrategia futura de migración `Strapi -> Odoo`.
- Se dejó documentado que transporte por vehículo sigue pendiente de modelado correcto en Odoo.
- La primera fase a ejecutar será `Fase 0` y luego `Fase 1`.

## Próximos pasos inmediatos

1. Crear `odoo.conf`.
2. Crear estructura `addons/`.
3. Crear módulo base `incas_core`.
4. Diseñar modelo de datos de `incas_reservas`.
5. Implementar el primer flujo: cotización -> reserva.
#### Flujo web operativo actual

- Astro ya puede crear reservas directamente en Odoo.
- Odoo expone endpoints públicos para:
  - `GET /incas/api/pagos/tipo-cambio`
  - `POST /incas/api/pagos/iniciar`
  - `POST /incas/api/pagos/confirmar`
  - `POST /incas/api/reservas`
- Odoo genera:
  - ticket
  - reserva
  - pago
  - URL pública de comprobante PDF
- Odoo guarda en la reserva snapshot de datos web:
  - nombre
  - email
  - teléfono
  - documento
  - nacionalidad
  - fecha inicio
  - fecha fin
  - turno
  - vehículo seleccionado
- Odoo sincroniza Google Sheets desde la propia reserva.
- Odoo envía correos con Resend y adjunta el comprobante PDF.
- Astro ya usa `PUBLIC_ODOO_URL` para el flujo transaccional.
- `saldo_pendiente` quedó como único saldo operativo visible en reserva.
- `pago_restante` queda solo por compatibilidad de datos y transición.
- `PUBLIC_ODOO_URL` vive en el `.env` raíz del proyecto.
- `PUBLIC_ODOO_URL` se inyecta al frontend desde:
  - `docker-compose.yaml`
  - `docker-compose.prod.yaml`
- Strapi queda como CMS y catálogo fuente.
- La conversión de moneda sigue tomando temporalmente `GET /api/pagos/tipo-cambio` del backend Strapi.

#### Validación local hecha

- Se probó `GET /incas/api/pagos/tipo-cambio` en Odoo.
- Se probó `POST /incas/api/reservas` y devolvió:
  - `ticket`
  - `reserva_id`
  - `voucher_url`
- Se probó la URL pública del comprobante PDF y respondió `200 OK`.

#### Pendientes inmediatos del flujo web

- mover el tipo de cambio a Odoo para cortar la dependencia transaccional restante con Strapi
- implementar IziPay real en Odoo
- definir webhook de pagos en Odoo
- afinar el HTML de correo si se requiere paridad visual más exacta con Strapi

## Changelog

### 2026-04-23

- se creó el flujo público `Astro -> Odoo` para reservas y pagos
- se agregaron endpoints públicos de Odoo para iniciar pago, confirmar pago, tipo de cambio y crear reserva
- se movió la creación de ticket y reserva web a Odoo
- se agregó URL pública con token para descargar el comprobante PDF de reserva
- se inyectaron variables de PayPal, Resend, Google Sheets y `PUBLIC_ODOO_URL` en Docker Compose
- se validó la creación real de una reserva web de prueba contra Odoo
