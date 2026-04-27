# Plan de módulos Odoo - Inca's Paradise

## Objetivo del documento

Definir el plan de crecimiento del back office de Inca's Paradise en Odoo 19, partiendo del avance real ya implementado en el repositorio y aterrizando los bloques operativos solicitados:

1. Información y asesoría
2. Ventas
3. Reservas
4. Proveedores
5. Operaciones
6. Post venta
7. Planificación
8. Infraestructura, equipamiento y activos
9. Gestión de personas
10. Marketing
11. Tesorería

La idea no es crear once módulos custom aislados sin criterio. La regla propuesta es:

- usar módulos estándar de Odoo donde ya resuelven bien el problema
- crear módulos `incas_*` solo para la lógica propia del negocio turístico
- mantener `incas_reservas` como núcleo transaccional ya existente

---

## Estado actual confirmado en el proyecto

### Base técnica existente

Ya existe en el repo:

- `odoo/config/odoo.conf`
- `odoo/addons/`
- Docker Compose para Odoo test y producción
- base de trabajo `odoo_incas`

### Módulos custom existentes

Actualmente existen:

- `incas_core`
- `incas_reservas`
- `dms`
- `incas_documentos`

### Avance real verificado en `incas_core`

`incas_core` ya cumple la base estructural del BO:

- menú raíz `Inca's Paradise`
- menú `Reservas`
- menú `Operaciones`
- menú `Configuración`
- grupos base para:
  - administración
  - reservas
  - operaciones
  - gerencia

### Avance real verificado en documentos

Se agregó el módulo `dms` en `odoo/addons/dms` para gestionar archivos, carpetas, etiquetas, categorías, almacenamientos y grupos de acceso.

Para adaptarlo al back office de Inca's Paradise se creó el módulo puente `incas_documentos`.

`dms` queda como motor documental.

`incas_documentos` queda como integración propia del proyecto.

#### Ubicación funcional

Documentos no pertenece solo a Reservas, Proveedores, Operaciones o RRHH.

Debe tratarse como una capa transversal del BO porque será usada por varios módulos:

- reservas
- pasajeros
- proveedores
- operaciones
- post venta
- tesorería
- gestión de personas
- infraestructura y activos

#### Integración realizada

`incas_documentos` agrega:

- dependencia explícita con `incas_core`
- dependencia explícita con `dms`
- menú `Documentos` dentro de `Inca's Paradise`
- acceso a `Archivos`
- acceso a `Carpetas`
- configuración documental dentro de `Inca's Paradise > Configuración`
- acceso a `Etiquetas`
- acceso a `Categorías`
- acceso a `Almacenamientos`
- acceso a `Grupos de acceso`

#### Permisos integrados

Los grupos del BO quedan conectados con los grupos de DMS:

- `Administrador BO` obtiene permisos de `DMS Manager`
- `Gerencia` obtiene permisos de `DMS Manager`
- `Reservas` obtiene permisos de `DMS User`
- `Operaciones` obtiene permisos de `DMS User`

#### Uso esperado

Documentos debe servir para gestionar:

- vouchers
- comprobantes de pago
- documentos de pasajeros
- pasaportes
- DNI o documentos equivalentes
- archivos de reserva
- contratos con proveedores
- confirmaciones operativas
- evidencias de incidencias
- archivos de post venta
- documentos internos de personal
- documentos de activos o vehículos

### Avance real verificado en `incas_reservas`

`incas_reservas` ya tiene una base funcional importante y no debe rehacerse.

#### Modelos ya presentes

- `incas.cotizacion`
- `incas.reserva`
- `incas.pago`
- `incas.pasajero`
- `incas.servicio.catalogo`
- `incas.catalogo.tour`
- `incas.catalogo.transporte`
- `incas.estilo.transporte`
- `incas.cotizacion.paquete.linea`

#### Funcionalidad ya presente en cotización

La cotización ya maneja:

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
- precio adulto base USD
- precio niño base USD
- precio adulto convertido
- precio niño convertido
- descuento porcentual
- cantidad de adultos
- cantidad de niños
- cantidad de pasajeros
- moneda:
  - PEN
  - USD
  - EUR
- monto total calculado
- estados de cotización:
  - borrador
  - enviada
  - aprobada
  - rechazada
  - cancelada
- responsable
- observaciones
- relación con reservas

#### Funcionalidad ya presente en reserva

La reserva ya maneja:

- código de reserva
- ticket
- token de acceso
- relación con cotización
- cliente principal
- snapshot de datos del cliente web:
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
- vehículo seleccionado
- idioma
- canal de venta
- tipo de servicio
- tipo de tour
- estilo de transporte
- servicio
- nombre del servicio
- precio adulto y niño base USD
- precio adulto y niño en moneda operativa
- descuento
- cantidad de adultos
- cantidad de niños
- cantidad de pasajeros
- moneda
- monto total
- monto pagado
- saldo pendiente
- pago restante
- monto final
- estados de reserva:
  - reservado
  - por coordinar
  - falta pago
  - pagado
  - completado
  - finalizado
  - cancelado
- estado de pago calculado:
  - pendiente
  - parcial
  - pagado
  - reembolsado
- pagos relacionados
- pasajeros relacionados
- responsable
- observaciones
- marca de origen web

#### Capas ya presentes alrededor de reservas

Además del modelo, ya existen:

- secuencia de cotización
- cron de tipo de cambio
- vistas para:
  - catálogo de servicios
  - catálogo de tours
  - catálogo de transportes
  - tipo de cambio
  - cotización
  - reserva
  - pago
  - pasajero
- reportes de reservas
- controladores para API y vistas públicas

### Conclusión del estado actual

La empresa no está empezando desde cero.

Ya tiene resuelta una parte importante de:

- estructura base del BO
- seguridad base
- menú principal
- catálogo operativo inicial
- cotización
- reserva
- pagos básicos
- pasajeros
- voucher y salida documental base
- integración web inicial

Por eso el siguiente paso correcto no es rehacer `incas_reservas`, sino ordenar el crecimiento alrededor de ese núcleo.

---

## Criterio de arquitectura propuesto

### Lo que debe quedar en módulos custom `incas_*`

Crear custom para:

- lógica turística propia
- flujos operativos propios del negocio
- estados específicos del proceso de viaje
- cálculo de precios del negocio
- integración entre web, reservas y operación
- trazabilidad específica de reservas, proveedores y servicios

### Lo que debe quedar en módulos estándar de Odoo

Reusar estándar para:

- CRM
- agenda
- compras
- contabilidad
- RRHH
- planificación
- helpdesk
- encuestas
- marketing
- mantenimiento
- flota
- inventario si realmente aplica

### Regla principal

No conviene crear módulos custom para reemplazar completamente apps estándar como CRM, Compras, HR o Contabilidad.

Conviene extenderlas o apoyarse en ellas.

---

## Mapa propuesto de módulos

### 1. Información y asesoría

#### Módulo propuesto

- `incas_informacion`

#### Base Odoo recomendada

- `crm`
- `contacts`
- `mail`
- `calendar`

#### Objetivo

Gestionar consultas, leads y primer contacto comercial antes de la cotización.

#### Alcance mínimo

- registro de consulta
- canal de ingreso
- idioma
- destino o servicio de interés
- asesor asignado
- prioridad
- SLA de respuesta
- historial de contacto
- conversión a cotización

#### Entregables mínimos

- modelo de consulta o extensión CRM
- pipeline inicial de atención
- conversión a `incas.cotizacion`
- tablero por asesor

---

### 2. Ventas

#### Módulo propuesto

- `incas_ventas`

#### Base Odoo recomendada

- `crm`
- `mail`
- `calendar`

#### Objetivo

Ordenar el pipeline comercial sobre la cotización ya existente.

#### Alcance mínimo

- etapas comerciales
- seguimiento de cotizaciones
- recordatorios
- fecha de vencimiento
- motivos de pérdida
- conversión a reserva
- indicadores de cierre

#### Entregables mínimos

- pipeline comercial
- actividades automáticas
- métricas de conversión
- trazabilidad lead -> cotización -> reserva

#### Nota

No usar `sale_management` al inicio salvo que se decida migrar la cotización al flujo estándar de ventas de Odoo.

---

### 3. Reservas

#### Módulo existente

- `incas_reservas`

#### Base Odoo actual

- `mail`
- `contacts`

#### Estado

Ya implementado de forma importante.

#### Lo que falta reforzar

- reprogramaciones
- cambios operativos con auditoría
- checklist documental
- control de saldo y vencimientos
- motivos de cancelación
- rooming o agrupación si el negocio lo necesita

#### Entregables siguientes

- versión ampliada de reservas
- mejores estados internos
- trazabilidad de cambios
- relación más fuerte con operación

---

### 4. Proveedores

#### Módulo propuesto

- `incas_proveedores`

#### Base Odoo recomendada

- `purchase`
- `contacts`
- `mail`

#### Objetivo

Gestionar operadores, hoteles, transportistas, guías y partners operativos.

#### Alcance mínimo

- ficha de proveedor
- clasificación por tipo
- tarifas pactadas
- vigencias
- documentos
- moneda
- condiciones operativas
- evaluación

#### Entregables mínimos

- catálogo de proveedores operativos
- matriz de tarifas
- documentos asociados
- integración con operaciones

---

### 5. Operaciones

#### Módulo propuesto

- `incas_operaciones`

#### Base Odoo recomendada

- `project`
- `calendar`
- `mail`

#### Objetivo

Transformar una reserva confirmada en un servicio operativo ejecutable.

#### Alcance mínimo

- creación de servicio operativo
- agenda operativa
- asignación de responsable interno
- asignación de proveedor
- asignación de guía
- incidencias
- endosos
- cambios operativos
- estado de ejecución

#### Entregables mínimos

- tablero de operaciones
- agenda diaria o semanal
- ficha de servicio operativo
- bitácora de incidencias

#### Prioridad

Es el bloque más importante después de reservas.

---

### 6. Post venta

#### Módulo propuesto

- `incas_postventa`

#### Base Odoo recomendada

- `survey`
- `helpdesk`
- `mail`

#### Objetivo

Dar seguimiento al cliente después del servicio.

#### Alcance mínimo

- encuestas
- satisfacción
- NPS
- reclamos
- compensaciones
- cierre del caso
- recuperación del cliente

#### Entregables mínimos

- caso post viaje
- encuesta automática
- métricas de satisfacción
- relación con operación y reserva

---

### 7. Planificación

#### Módulo propuesto

- `incas_planificacion`

#### Base Odoo recomendada

- `planning`
- `calendar`
- `project`

#### Objetivo

Gestionar capacidad operativa y carga futura.

#### Alcance mínimo

- calendario maestro
- capacidad por fecha
- bloqueos
- disponibilidad por rol
- alertas por sobrecarga

#### Entregables mínimos

- tablero de capacidad
- calendario maestro de carga
- alertas de saturación

---

### 8. Infraestructura, equipamiento y activos

#### Módulo propuesto

- `incas_infraestructura`

#### Base Odoo recomendada

- `maintenance`
- `fleet`
- `stock` solo si aplica

#### Objetivo

Controlar activos usados en la operación turística.

#### Alcance mínimo

- vehículos
- equipos
- mantenimiento
- disponibilidad
- responsable
- costo asociado

#### Entregables mínimos

- catálogo de activos
- mantenimiento preventivo
- relación activo -> operación

---

### 9. Gestión de personas

#### Módulo propuesto

- `incas_rrhh`

#### Base Odoo recomendada

- `hr`
- `hr_holidays`
- `planning`

#### Objetivo

Gestionar personal interno y perfiles operativos.

#### Alcance mínimo

- ficha de empleado
- rol
- documentos
- disponibilidad
- vacaciones
- habilidades
- idiomas
- certificaciones

#### Entregables mínimos

- padrón de personal
- disponibilidad operativa
- perfil operativo por colaborador

#### Nota

Nómina solo después de validación legal peruana.

---

### 10. Marketing

#### Módulo propuesto

- `incas_marketing`

#### Base Odoo recomendada

- `mass_mailing`
- `marketing_automation`
- `crm`

#### Objetivo

Segmentar y activar campañas sobre leads y clientes.

#### Alcance mínimo

- segmentación
- campañas
- automatizaciones
- seguimiento de conversión
- seguimiento post viaje

#### Entregables mínimos

- segmentos base
- campañas iniciales
- automatizaciones simples
- reporte de conversión comercial

---

### 11. Tesorería

#### Módulo propuesto

- `incas_tesoreria`

#### Base Odoo recomendada

- `account`
- `account_accountant`
- `purchase`

#### Objetivo

Controlar cobros, egresos, saldos y flujo básico de caja.

#### Alcance mínimo

- saldo por reserva
- cuenta por cobrar
- cuenta por pagar
- caja diaria
- egresos operativos
- conciliación básica

#### Entregables mínimos

- tablero de caja
- control de saldos
- relación reserva -> cobro -> pago a proveedor

---

## Módulos base de Odoo recomendados

### Instalar primero

- `Contactos` (`contacts`)
- `CRM` (`crm`)
- `Calendario` (`calendar`)
- `Compras` (`purchase`)
- `Contabilidad` (`account`)
- `Contabilidad avanzada` (`account_accountant`)
- `Proyecto` (`project`)
- `Encuestas` (`survey`)

### Instalar en segunda etapa

- `Helpdesk` (`helpdesk`)
- `Planificación` (`planning`)
- `Empleados` (`hr`)
- `Ausencias` (`hr_holidays`)

### Instalar solo si aplica

- `Flota` (`fleet`)
- `Mantenimiento` (`maintenance`)
- `Inventario` (`stock`)
- `Email Marketing` (`mass_mailing`)
- `Automatización de marketing` (`marketing_automation`)

### Gestión documental

Si la instancia es Enterprise:

- `Documentos` (`documents`)

Si la instancia es Community:

- usar adjuntos estándar de Odoo
- evaluar módulo tercero de gestión documental si realmente hace falta

En este proyecto ya se agregó `dms`, por lo que la decisión práctica actual es:

- usar `dms` como reemplazo funcional de `documents`
- usar `incas_documentos` como módulo puente para integrarlo al menú y permisos de Inca's Paradise
- no mezclar reglas de negocio dentro de `dms`
- relacionar documentos con reservas, proveedores, operaciones y RRHH desde módulos `incas_*` cuando se implemente cada fase

---

## Roadmap por fases propuesto

### Fase 0

#### Estado

Prácticamente resuelta en lo esencial.

#### Ya logrado

- Docker
- base Odoo separada
- `odoo.conf`
- estructura local de addons
- módulo base `incas_core`
- seguridad y menús iniciales

#### Falta por cerrar

- operación formal de backups
- lineamientos de restore
- checklist de despliegue
- validación de roles por ambiente

---

### Fase 1A

#### Estado

Iniciada y avanzada.

#### Ya logrado

- `incas_reservas`
- cotización
- reserva
- pasajeros
- pagos básicos
- ticket
- reportes base
- API web inicial
- cron de tipo de cambio

#### Falta por cerrar

- reprogramaciones
- controles de saldo más visibles
- checklist documental
- trazabilidad fina de cambios
- ampliación de controles internos de reserva

---

### Fase 1B

#### Objetivo

Abrir la capa comercial previa a reserva.

#### Módulos

- `incas_informacion`
- `incas_ventas`

#### Resultado esperado

Todo lead debe poder convertirse en cotización y medirse.

#### Esta debería ser la siguiente fase

Sí. Es la siguiente fase recomendada.

---

### Fase 2

#### Objetivo

Resolver ejecución operativa real del servicio.

#### Módulos

- `incas_proveedores`
- `incas_operaciones`

#### Resultado esperado

Toda reserva confirmada debe producir una operación asignable, trazable y controlable.

#### Prioridad

Muy alta. Es la fase más crítica después del frente comercial.

---

### Fase 3

#### Objetivo

Mejorar experiencia del cliente y capacidad interna.

#### Módulos

- `incas_postventa`
- `incas_planificacion`

#### Resultado esperado

- medir satisfacción
- atender incidencias post viaje
- planificar capacidad

---

### Fase 4

#### Objetivo

Formalizar el control económico y tributario.

#### Módulos

- `incas_tesoreria`
- `incas_facturacion`

#### Resultado esperado

- caja
- cobranza
- pagos operativos
- conciliación
- documentos tributarios

---

### Fase 5

#### Objetivo

Controlar activos y, solo si aplica, inventario operativo.

#### Módulo

- `incas_infraestructura`

---

### Fase 6

#### Objetivo

Ordenar personal y disponibilidad interna.

#### Módulo

- `incas_rrhh`

---

### Fase 7

#### Objetivo

Escalar CRM, campañas y fidelización.

#### Módulo

- `incas_marketing`

---

## Orden recomendado de implementación

### Etapa inmediata

1. reforzar `incas_reservas`
2. construir `incas_informacion`
3. construir `incas_ventas`

### Etapa crítica siguiente

4. construir `incas_proveedores`
5. construir `incas_operaciones`

### Etapa de control y servicio

6. construir `incas_postventa`
7. construir `incas_planificacion`
8. construir `incas_tesoreria`

### Etapa de madurez

9. construir `incas_infraestructura`
10. construir `incas_rrhh`
11. construir `incas_marketing`

---

## Lista final de módulos `incas_*` propuestos

- `incas_core`
- `incas_documentos`
- `incas_informacion`
- `incas_ventas`
- `incas_reservas`
- `incas_proveedores`
- `incas_operaciones`
- `incas_postventa`
- `incas_planificacion`
- `incas_infraestructura`
- `incas_rrhh`
- `incas_marketing`
- `incas_tesoreria`
- `incas_facturacion`
- `incas_integraciones`

---

## Conclusión ejecutiva

El proyecto ya tiene construido el núcleo más delicado:

- base técnica Odoo
- menú y seguridad base
- cotización
- reserva
- pagos básicos
- pasajeros
- flujo web inicial

La siguiente decisión correcta no es rehacer reservas, sino:

1. cerrar huecos de `incas_reservas`
2. ordenar `información y asesoría`
3. ordenar `ventas`
4. después abrir `proveedores` y `operaciones`

Ese es el camino más sólido para que Inca's Paradise pase de un flujo transaccional básico a un back office turístico completo dentro de Odoo.
