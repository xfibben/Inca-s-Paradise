# Actividades 29 abril

## Objetivo del día

Avanzar 3 tareas dentro de `incas_reservas`:

1. transporte: obtener vehículos disponibles correctamente
2. transporte: aplicar precios según vehículo seleccionado
3. checklist documental de pasajeros

## Orden de trabajo de hoy

### 1. Transporte - vehículos disponibles

#### Qué haremos

- revisar cómo se obtienen los vehículos disponibles desde el servicio de transporte
- validar que `cotizacion` y `reserva` muestren solo vehículos válidos para el transporte seleccionado
- validar que `vehiculo_id` no se pierda al guardar o recalcular
- validar que `vehiculo_seleccionado` quede persistido correctamente

#### Resultado esperado

- al elegir un transporte se cargan sus vehículos reales
- el usuario puede elegir el vehículo correcto
- la selección queda guardada

### 2. Transporte - precio por vehículo seleccionado

#### Qué haremos

- revisar cómo se obtiene la tarifa del vehículo desde `precios[]`
- validar cálculo de:
  - `precio_adulto`
  - `precio_nino`
  - `descuento`
  - `monto_total`
- revisar que el recálculo funcione tanto en `cotizacion` como en `reserva`
- probar con al menos 2 vehículos distintos del mismo transporte

#### Resultado esperado

- cambiar de vehículo cambia los precios
- cambiar de vehículo cambia el monto total
- los valores correctos pasan a la reserva

### 3. Checklist documental de pasajeros

#### Qué haremos

- definir el modelo mínimo para control documental del pasajero
- decidir si vive dentro de `incas.pasajero` o en modelo relacionado
- mostrar estado documental visible para cada pasajero
- dejar una vista simple de seguimiento

#### Resultado esperado

- cada pasajero tiene un estado documental claro
- se puede saber qué falta entregar
- la reserva puede identificar si el grupo está completo o no

## Definición funcional mínima para hoy

### Transporte

#### Debe quedar resuelto

- selección de vehículo por transporte
- lectura correcta de tarifa por vehículo
- persistencia del vehículo en reserva
- recálculo de totales

#### No es prioridad hoy

- rediseñar toda la estructura de tarifas por vehículo
- mover todavía toda la lógica a un modelo nuevo
- refactor grande del catálogo

### Checklist documental

#### Debe quedar resuelto

- estado documental por pasajero
- campos mínimos de control
- visibilidad en back office

#### No es prioridad hoy

- integración con `dms`
- carpetas automáticas
- reglas avanzadas por nacionalidad
- portal documental para cliente

## Datos importantes para retomar en otra conversación

### Contexto del proyecto

- proyecto: `Inca's Paradise`
- stack Odoo actual: `odoo/addons/`
- base de trabajo: `odoo_incas`
- idioma de trabajo: español

### Módulos Odoo existentes

- `incas_core`
- `incas_reservas`
- `incas_documentos`
- `incas_operaciones`
- `incas_postventas`

### Módulo en foco hoy

- `incas_reservas`

### Archivos clave a revisar

- `odoo/addons/incas_reservas/models/incas_servicio_catalogo.py`
- `odoo/addons/incas_reservas/models/incas_reserva.py`
- `odoo/addons/incas_reservas/models/incas_cotizacion.py`
- `odoo/addons/incas_reservas/models/incas_catalogo_transporte.py`
- `odoo/addons/incas_reservas/models/incas_catalogo_vehiculo.py`
- `odoo/addons/incas_reservas/views/incas_reserva_views.xml`
- `odoo/addons/incas_reservas/views/incas_cotizacion_views.xml`
- `odoo/addons/incas_reservas/models/incas_pasajero.py`
- `odoo/addons/incas_reservas/views/incas_pasajero_views.xml`

### Hallazgo importante ya identificado

- el problema inmediato está en transporte:
  - no se están obteniendo bien los vehículos
  - no se está aplicando bien el precio por vehículo seleccionado

### Reglas funcionales que no se deben romper

- en transporte el precio puede depender del `vehiculo`
- `vehiculo_seleccionado` debe viajar desde frontend hasta reserva
- el comprobante PDF debe mostrar `vehiculo_seleccionado` cuando sea transporte
- Google Sheets debe recibir `vehiculo` cuando la reserva sea de transporte
- descuentos siguen siendo porcentuales
- precios base del catálogo se manejan en `USD`

### Endpoints actuales del flujo web

- `GET /incas/api/pagos/tipo-cambio`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`
- `POST /incas/api/reservas`

### Resultado esperado al cerrar el trabajo

- transporte usable con vehículo correcto y tarifa correcta
- reserva guardando vehículo correctamente
- base mínima de checklist documental por pasajero

## Próximo paso sugerido al retomar

1. revisar `incas_servicio_catalogo.py`
2. revisar `incas_cotizacion.py`
3. revisar `incas_reserva.py`
4. revisar `incas_pasajero.py`
5. implementar transporte primero
6. implementar checklist documental después
