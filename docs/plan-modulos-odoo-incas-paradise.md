# Plan de módulos Odoo - Inca's Paradise

## Objetivo

Actualizar el plan del back office Odoo según el estado real del código en este repositorio.

Este documento separa:

- lo ya construido
- lo ya iniciado pero incompleto
- lo que todavía falta implementar

La regla sigue siendo la misma:

- usar estándar de Odoo cuando resuelve bien
- crear módulos `incas_*` solo para lógica turística propia
- mantener `incas_reservas` como núcleo transaccional del negocio

## Estado real verificado en el repo

### Base técnica

Ya existe:

- `odoo/config/odoo.conf`
- `odoo/addons/`
- base de trabajo `odoo_incas`
- despliegue con Docker Compose

### Módulos custom existentes

Actualmente existen en código:

- `incas_core`
- `incas_reservas`
- `incas_documentos`
- `incas_operaciones`
- `incas_postventas`
- `incas_tesoreria`

También está incluido:

- `dms`

### Corte real mayo 2026

- `incas_reservas` es el núcleo más maduro y ya sostiene el flujo web y BO.
- `incas_operaciones` ya existe, pero todavía está en nivel agenda y tareas.
- `incas_postventas` ya existe y tiene estructura funcional real.
- `incas_tesoreria` ya existe, pero todavía es una base inicial de movimientos.
- `incas_facturacion`, `incas_rrhh` e `incas_integraciones` todavía no existen como módulos reales en este repo.

## Estado por módulo

### 1. `incas_core`

#### Ya implementado

- menú raíz `Inca's Paradise`
- menú `Reservas`
- menú `Operaciones`
- menú `Configuración`
- grupos base:
  - administración
  - reservas
  - operaciones
  - gerencia

#### Falta

- grupos más finos por proceso si crecen proveedores, tesorería, RRHH o marketing
- matriz de permisos por módulo futuro
- validación formal de roles por ambiente

### 2. `incas_documentos` + `dms`

#### Ya implementado

- integración de `dms` dentro del menú de Inca's Paradise
- menú `Documentos`
- accesos a:
  - archivos
  - carpetas
  - etiquetas
  - categorías
  - almacenamientos
  - grupos de acceso
- herencia de permisos:
  - administración y gerencia con permisos tipo manager
  - reservas y operaciones con permisos tipo user
- override sobre `dms.file`
- ampliación del tamaño máximo permitido
- habilitación práctica para subir videos quitando extensiones de video de la lista prohibida

#### Ya resuelto a nivel de arquitectura

- documentos queda como capa transversal
- `dms` sigue siendo motor documental
- `incas_documentos` queda como módulo puente del proyecto

#### Falta

- vincular documentos a modelos de negocio concretos:
  - reserva
  - pasajero
  - proveedor
  - operación
  - personal
  - activos
- definir estructura de carpetas y etiquetas por proceso
- checklist documental por reserva y por pasajero

### 3. `incas_reservas`

#### Estado

Es el módulo más avanzado del BO y ya supera una base simple de reservas.

#### Modelos implementados

- `incas.cotizacion`
- `incas.reserva`
- `incas.pago`
- `incas.pasajero`
- `incas.servicio.catalogo`
- `incas.catalogo.tour`
- `incas.catalogo.transporte`
- `incas.catalogo.vehiculo`
- `incas.estilo.transporte`
- `incas.cotizacion.paquete.linea`
- `incas.cotizacion.hotel.linea`
- `incas.cotizacion.extra.linea`
- `incas.hotel`
- `incas.hotel.tarifa`
- `incas.extra`
- `incas.extra.tarifa`
- `incas.horario.opcion`

#### Ya implementado en catálogo y sincronización

- catálogo local de tours
- catálogo local de transportes
- catálogo local de vehículos
- catálogo unificado de servicios
- sincronización desde Strapi
- actualización de tours
- actualización de transportes
- actualización de vehículos
- sincronización de horarios desde `scheduleItems`
- soporte de tarifas de transporte por vehículo leyendo `precios[]`

#### Ya implementado en cotización

- cliente principal
- fecha de cotización
- fecha de viaje
- idioma
- canal de venta
- tipo de servicio:
  - tour
  - transporte
  - paquete
- tipo de tour
- estilo de transporte
- servicio
- paquete con múltiples líneas
- conteo de items del paquete
- exportación PDF de cotización
- exportación PDF de detalle de paquete
- cantidad de adultos y niños
- cantidad total de pasajeros
- moneda:
  - PEN
  - USD
  - EUR
- cálculo de precios y totales
- descuento porcentual
- hoteles opcionales en múltiples líneas:
  - hotel
  - tarifa
  - check-in
  - check-out
  - noches
  - habitaciones
  - monto hotel
- extras opcionales en múltiples líneas:
  - extra
  - tarifa
  - unidad
  - cantidad
  - monto extra
- responsable
- observaciones
- estados:
  - borrador
  - enviada
  - aprobada
  - rechazada
  - cancelada
- relación con reservas

#### Ya implementado en reserva

- código interno
- ticket
- token de acceso público
- relación con cotización
- snapshot de datos web:
  - nombre
  - email
  - teléfono
  - tipo de documento
  - número de documento
  - nacionalidad
- fecha de reserva
- fecha de inicio
- fecha de fin
- fecha de viaje
- turno
- idioma
- canal de venta
- tipo de servicio
- tipo de tour
- estilo de transporte
- servicio
- nombre del servicio
- vehículo sugerido y vehículo seleccionado
- hoteles y extras asociados por líneas de cotización
- precios base USD
- precios convertidos por moneda
- descuento porcentual
- cantidad de adultos y niños
- cantidad total de pasajeros
- monto total
- monto pagado
- saldo pendiente
- pago restante
- monto final
- pagos relacionados
- pasajeros relacionados
- origen web
- comprobante PDF interno
- comprobante PDF público por token

#### Ya implementado en pagos

- modelo `incas.pago`
- proveedor:
  - efectivo
  - izipay
  - paypal
- método:
  - efectivo
  - tarjeta
  - yape_qr
  - paypal
- moneda del pago
- conversión de monto a moneda de la reserva
- estado:
  - pendiente
  - pagado
  - fallido
  - reembolsado
- transacción, orden, QR, IP y fecha de pago
- actualización de pendientes al crear o editar pagos

#### Ya implementado en API y web

- `GET /incas/api/pagos/tipo-cambio`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`
- `POST /incas/api/reservas`
- creación de reserva web desde Odoo
- inicio de orden PayPal
- confirmación de pago PayPal
- generación de `ticket`
- devolución de `reserva_id`
- devolución de `voucher_url`
- comprobante público en:
  - `/incas/public/reserva/<id>/pdf/<token>`

#### Ya implementado en operación auxiliar del módulo

- cron de tipo de cambio
- secuencias
- vistas de back office
- reportes PDF
- correo con PDF adjunto
- sincronización con Google Sheets desde reserva

#### Falta

- modelar de forma nativa precios de transporte por vehículo dentro de Odoo sin depender de JSON sincronizado
- reprogramaciones
- auditoría fina de cambios operativos
- checklist documental por reserva
- motivos de cancelación
- reglas más claras para cobranzas parciales y vencimientos
- flujo formal de reembolsos
- integración real IziPay
- separar mejor operación comercial vs operación ejecutada

### 4. `incas_operaciones`

#### Estado

Existe, pero todavía no resuelve la operación turística completa.

#### Ya implementado

- extensión de `mail.activity`
- estado de ejecución:
  - pendiente
  - en_progreso
  - finalizada
- fecha hora de inicio
- fecha hora de fin
- duración en minutos
- duración en horas
- botones para iniciar y concluir actividad desde popup, formulario y lista

#### Lo que realmente cubre hoy

- seguimiento básico de ejecución sobre actividades

#### Lo que falta para que sea un módulo de operaciones real

- modelo de servicio operativo
- agenda operativa por fecha
- asignación de guía
- asignación de conductor
- asignación de proveedor
- asignación de vehículo real
- incidencias operativas
- endosos
- estados operativos por reserva o tramo
- tablero diario o semanal de operaciones

### 5. `incas_postventas`

#### Estado

Ya no está solo planeado. Ya existe en código y tiene una base funcional real.

#### Modelos implementados

- `incas.postventa`
- `incas.postventa.caso`
- `incas.postventa.encuesta`
- `incas.postventa.reclamo`
- `incas.postventa.accion`

#### Ya implementado

- menú `Postventas`
- casos post viaje
- encuestas
- reclamos
- acciones correctivas
- extensión de `res.partner` con datos de cliente:
  - documento
  - idioma preferido
  - cumpleaños
  - preferencias
  - restricciones
  - satisfacción promedio
  - última encuesta
  - conteo de reservas
- extensión de `incas.reserva`:
  - relación con casos postventa
  - contador
  - acción para crear caso
- creación automática de caso si una reserva pasa a `finalizado`
- un caso único por reserva
- encuestas con métricas:
  - NPS
  - satisfacción general
  - puntualidad
  - atención del guía
  - transporte
  - comunicación previa
  - cumplimiento del itinerario
  - seguridad
  - relación precio/calidad
- detección de encuestas que requieren acción
- reclamos con prioridad, motivo, canal y cierre
- acciones correctivas con responsable, tipo, estado y resultado

#### Lo que falta

- envío real automatizado de encuesta por correo o link público
- portal o formulario público para responder encuesta
- integración con libro de reclamaciones formal si aplica
- SLA y alertas de postventa
- métricas y dashboards ejecutivos

## Módulos planeados que todavía no existen

### 6. Información y asesoría

#### Módulo propuesto

- `incas_informacion`

#### Base Odoo recomendada

- `crm`
- `contacts`
- `mail`
- `calendar`

#### Objetivo

Gestionar leads, consultas y primer contacto antes de cotizar.

#### Falta por implementar

- registro de consulta
- pipeline inicial
- asesor asignado
- SLA comercial
- conversión de lead a cotización

### 7. Ventas

#### Módulo propuesto

- `incas_ventas`

#### Base Odoo recomendada

- `crm`
- `mail`
- `calendar`

#### Objetivo

Ordenar la capa comercial alrededor de la cotización ya construida.

#### Falta por implementar

- etapas comerciales
- vencimiento de cotización
- motivos de pérdida
- actividades automáticas
- trazabilidad lead -> cotización -> reserva

### 8. Proveedores

#### Módulo propuesto

- `incas_proveedores`

#### Base Odoo recomendada

- `purchase`
- `contacts`
- `mail`

#### Objetivo

Gestionar hoteles, operadores, transportistas, guías y otros proveedores.

#### Falta por implementar

- ficha de proveedor operativo
- clasificación por tipo
- tarifas pactadas
- vigencias
- documentos
- evaluación
- relación con operaciones

### 9. Planificación

#### Módulo propuesto

- `incas_planificacion`

#### Base Odoo recomendada

- `planning`
- `calendar`
- `project`

#### Objetivo

Controlar capacidad futura, disponibilidad y carga operativa.

#### Falta por implementar

- calendario maestro
- capacidad por fecha
- bloqueos
- disponibilidad por rol
- alertas de sobrecarga

### 10. Infraestructura, equipamiento y activos

#### Módulo propuesto

- `incas_infraestructura`

#### Base Odoo recomendada

- `maintenance`
- `fleet`
- `stock` si aplica

#### Objetivo

Controlar activos usados en la operación turística.

#### Falta por implementar

- catálogo de activos
- mantenimiento preventivo
- disponibilidad
- relación activo -> operación

### 11. Gestión de personas

#### Módulo propuesto

- `incas_rrhh`

#### Base Odoo recomendada

- `hr`
- `hr_holidays`
- `planning`

#### Objetivo

Gestionar personal interno, roles, idiomas, certificaciones y disponibilidad.

### 12. Marketing

#### Módulo propuesto

- `incas_marketing`

#### Base Odoo recomendada

- `mass_mailing`
- `marketing_automation`
- `crm`

#### Objetivo

Segmentar leads y clientes para campañas y fidelización.

### 13. Tesorería

#### Módulo propuesto

- `incas_tesoreria`

#### Base Odoo recomendada

- `account`
- `account_accountant`
- `purchase`

#### Objetivo

Controlar caja, cobros, egresos y relación entre reserva, cobro y pago a proveedor.

### 14. Facturación

#### Módulo propuesto

- `incas_facturacion`

#### Base Odoo recomendada

- `account`
- localización Perú

#### Objetivo

Resolver comprobantes, tributación y flujo formal SUNAT.

### 15. Integraciones

#### Módulo propuesto

- `incas_integraciones`

#### Objetivo

Centralizar integraciones externas hoy dispersas entre módulos.

#### Alcance recomendado

- Strapi
- PayPal
- IziPay
- Google Sheets
- correo transaccional

## Roadmap actualizado por fases

### Fase 0

#### Ya hecho

- estructura técnica base
- addons locales
- menús y grupos base
- capa documental inicial

#### Falta

- backups y restore formalizados
- checklist de despliegue
- endurecimiento de permisos por ambiente

### Fase 1

#### Ya hecho

- núcleo de cotizaciones
- núcleo de reservas
- pagos básicos
- API pública para web
- PDF y voucher público
- sync inicial con Strapi
- sync con Google Sheets
- hoteles y extras
- paquetes
- vehículos y tarifas leídas desde Strapi

#### Falta

- IziPay real
- reprogramaciones
- checklist documental
- auditoría de cambios
- cobranzas parciales más robustas
- motivos de cancelación y reembolso
- modelo local más fuerte para tarifas por vehículo

### Fase 2

#### Estado real

Iniciada parcialmente.

#### Ya hecho

- `incas_operaciones` básico sobre actividades

#### Falta

- `incas_proveedores`
- operación ejecutable por reserva
- agenda operativa real
- incidencias y endosos

### Fase 3

#### Estado real

También iniciada parcialmente.

#### Ya hecho

- `incas_postventas` con casos, encuestas, reclamos y acciones

#### Falta

- automatización real de encuestas
- dashboards de satisfacción
- `incas_planificacion`

### Fase 4

#### Falta completa

- `incas_tesoreria`
- `incas_facturacion`
- localización Perú
- flujo tributario

### Fase 5

#### Falta completa

- `incas_infraestructura`

### Fase 6

#### Falta completa

- `incas_rrhh`

### Fase 7

#### Falta completa

- `incas_marketing`

## Orden recomendado de trabajo desde el estado actual

### Prioridad inmediata

1. cerrar huecos de `incas_reservas`
2. volver operativo `incas_operaciones`
3. construir `incas_proveedores`

### Prioridad alta siguiente

4. automatizar y cerrar `incas_postventas`
5. construir `incas_informacion`
6. construir `incas_ventas`

### Prioridad media

7. construir `incas_planificacion`
8. construir `incas_tesoreria`
9. construir `incas_facturacion`

### Prioridad posterior

10. construir `incas_infraestructura`
11. construir `incas_rrhh`
12. construir `incas_marketing`

## Lista final actualizada de módulos

### Ya existentes

- `incas_core`
- `incas_documentos`
- `incas_reservas`
- `incas_operaciones`
- `incas_postventas`

### Pendientes

- `incas_informacion`
- `incas_ventas`
- `incas_proveedores`
- `incas_planificacion`
- `incas_infraestructura`
- `incas_rrhh`
- `incas_marketing`
- `incas_tesoreria`
- `incas_facturacion`
- `incas_integraciones`

## Conclusión ejecutiva

El proyecto no está en fase conceptual.

Ya tiene:

- base técnica Odoo
- seguridad y menús base
- capa documental
- núcleo transaccional fuerte de reservas
- API web operativa
- pagos básicos
- postventa inicial real
- operaciones básicas sobre actividades

Lo correcto ahora no es planear desde cero, sino reconocer el avance real y cerrar lo que falta en este orden:

1. reforzar `incas_reservas`
2. convertir `incas_operaciones` en operación turística real
3. crear `incas_proveedores`
4. cerrar automatización de `incas_postventas`
5. recién después abrir capa comercial más completa con `incas_informacion` e `incas_ventas`
