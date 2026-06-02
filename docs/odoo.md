# Odoo

## 1. Rol de Odoo en el proyecto

Odoo es hoy:

- back office principal
- fuente pública de catálogo
- motor de reservas
- motor de pagos
- generador de vouchers
- origen de agenda operativa
- origen de postventa, RRHH y tesorería

El frontend no debe crear lógica transaccional paralela fuera de Odoo.

## 2. Estructura de addons propios

### `incas_core`

Base técnica:

- menú raíz `Inca's Paradise`
- grupos y permisos base

### `incas_documentos`

Documental:

- integración con `dms`
- uploads grandes
- preview inline
- acciones custom de archivos

### `incas_reservas`

Addon central:

- catálogo de servicios
- tours
- destinos
- estilos de viaje
- transportes
- vehículos
- legales
- reservas
- pagos
- endpoints públicos
- PDF de reserva

### `incas_operaciones`

Operación:

- agenda de eventos
- líneas operativas por reserva
- pase operativo PDF
- workflow de revisión sobre `mail.activity`

### `incas_postventas`

Postventa:

- casos
- reclamos
- acciones
- encuestas de satisfacción

### `incas_rrhh`

RRHH:

- datos extendidos en `res.users`
- boletas
- certificados
- evaluación semanal/mensual

### `incas_tesoreria`

- movimientos de tesorería

### `incas_proveedores`

- proveedores

### `incas_producto`

- historial de tours

## 3. Modelos núcleo

### Catálogo

- `incas.servicio.catalogo`
- `incas.tour`
- `incas.catalogo.destino`
- `incas.estilo.viaje`
- `incas.catalogo.transporte`
- `incas.catalogo.transporte.tarifa`
- `incas.catalogo.vehiculo`

### Reserva

- `incas.reserva`
- `incas.pago`
- `incas.pasajero`
- `incas.reserva.paquete.linea`
- `incas.reserva.hotel.linea`
- `incas.reserva.extra.linea`
- `incas.reserva.cambio`

### Contenido legal y corporativo

- `incas.termino.condicion`
- `incas.politica`
- `incas.cancelacion`
- `incas.pregunta.frecuente`
- `incas.nosotros`
- `incas.sostenibilidad.articulo`

### Operación

- `incas.agenda.evento`
- `incas.reserva.operacion.linea`

## 4. `incas.reserva`: centro del sistema

Archivo:

- `odoo/addons/incas_reservas/models/incas_reserva.py`

Responsabilidades:

- secuencia interna `name`
- `ticket`
- `access_token`
- datos del cliente principal
- snapshot del formulario web
- tipo de servicio
- servicio resuelto
- precios base USD y precios convertidos
- descuentos
- pagos
- pasajeros
- carpeta documental
- URL pública del voucher

### Campos clave

- `ticket`
- `access_token`
- `partner_id`
- `nombre`
- `email`
- `telefono`
- `tipo_documento`
- `numero_documento`
- `nacionalidad`
- `fecha_inicio`
- `fecha_fin`
- `turno`
- `vehiculo_id`
- `vehiculo_seleccionado`
- `tipo_servicio`
- `tipo_tour`
- `servicio_id`
- `servicio_nombre`
- `precio_adulto_usd`
- `precio_nino_usd`
- `precio_adulto`
- `precio_nino`
- `descuento`
- `monto_total`
- `monto_pagado`
- `saldo_pendiente`
- `estado_comercial`
- `estado_reserva`
- `estado_pago`
- `origen_web`

### Reglas de negocio

- catálogo base en `USD`
- descuento porcentual
- conversión a `PEN`, `USD` o `EUR`
- si es transporte, el precio sale de la tarifa del vehículo
- si no hay pasajeros, crea pasajero principal
- si no hay carpeta documental, la crea

## 5. Reserva web

Método clave:

- `crear_reserva_web()`

Flujo:

1. prepara valores desde payload web
2. crea `incas.reserva`
3. crea `incas.pago` si hay `pago_data`
4. ejecuta `_post_reserva_web()`

`_post_reserva_web()` hace:

- `_actualizar_pendientes()`
- `_sincronizar_con_sheets()`
- `_enviar_correos_reserva()`

## 6. Pago

### Endpoints

- `GET /incas/api/pagos/tipo-cambio`
- `POST /incas/api/pagos/iniciar`
- `POST /incas/api/pagos/confirmar`

### Estado actual

- PayPal activo
- IziPay todavía no está operativo en esta guía

### Notas críticas

- PayPal trabaja en `USD`
- el frontend muestra moneda al usuario
- Odoo fija el monto transaccional real

## 7. Catálogo público

### Controlador

- `odoo/addons/incas_reservas/controllers/api.py`

### Endpoints

- destinos
- tours
- estilos de viaje
- sostenibilidad
- términos
- nosotros
- políticas
- cancelaciones
- preguntas frecuentes
- tipo-transportes
- transportes
- imagen pública

### Serialización

La API pública construye manualmente payloads. No es REST automático.

Importa porque:

- cambiar nombres de campos rompe frontend
- cambiar estructura de arrays rompe páginas SSR

## 8. Tours

Archivo:

- `odoo/addons/incas_reservas/models/incas_tour.py`

Características:

- slugs por idioma
- SEO por idioma
- bloques destacados
- itinerario
- incluye / no incluye
- horarios
- imágenes destacadas
- vínculo único a `incas.servicio.catalogo`
- campos de apoyo para migraciones y normalizaciones viejas

## 9. Transportes

Archivo:

- `odoo/addons/incas_reservas/models/incas_catalogo_transporte.py`

Características:

- hereda por `_inherits` de `incas.servicio.catalogo`
- múltiples tipos de transporte
- múltiples tarifas por vehículo
- SEO por idioma
- incluye / no incluye
- assets manejados por DMS

Punto importante:

- aquí está la lógica que reemplaza precio único por precio dependiente de vehículo

## 10. Operaciones

Archivo clave:

- `odoo/addons/incas_operaciones/models/incas_reserva.py`

Hace sobre `incas.reserva`:

- crea/sincroniza evento de agenda
- genera cronograma operativo
- genera líneas de operación
- resume agencias, fechas, servicios, horarios, saldos

PDF:

- `GET /incas/operaciones/reserva/<id>/pase-pdf`

## 11. Documentos

### Voucher de reserva

Rutas:

- privada: `/incas/reserva/<id>/pdf`
- pública: `/incas/public/reserva/<id>/pdf/<token>`

### DMS

Addon:

- `incas_documentos`

Uso:

- archivos de catálogo
- documentos de pasajeros
- previews inline

## 12. Correos

Desde `incas.reserva`:

- genera correo con voucher adjunto
- envía a cliente
- envía a correo de notificación
- usa datos de `RESEND_*`

## 13. Integraciones externas

- PayPal
- Resend
- Google Apps Script

Variables:

- `PAYPAL_CLIENT_ID`
- `PAYPAL_SECRET`
- `PAYPAL_MODE`
- `GOOGLE_APPS_SCRIPT_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `RESEND_FROM_NAME`
- `RESEND_NOTIFY_EMAIL`

## 14. RRHH

Archivo clave:

- `odoo/addons/incas_rrhh/models/incas_evaluacion_desempeno.py`

Estado actual:

- evaluación mensual
- semanas autogeneradas
- líneas por trabajador
- criterios por trabajador dentro de cada semana
- promedio automático por trabajador y por mes

También:

- boletas
- certificados laborales

## 15. Riesgos técnicos

- mucha lógica crítica está dentro de modelos muy grandes.
- la API pública no está separada por capa de servicio formal.
- hay migraciones de columnas legadas dentro de `_auto_init`.
- cambios de estructura en catálogo pueden romper SSR.
- no hay batería de tests que asegure reserva, pago y mail.

## 16. Archivos que un nuevo dev debe abrir primero

1. `odoo/addons/incas_reservas/__manifest__.py`
2. `odoo/addons/incas_reservas/controllers/api.py`
3. `odoo/addons/incas_reservas/models/incas_reserva.py`
4. `odoo/addons/incas_reservas/models/incas_tour.py`
5. `odoo/addons/incas_reservas/models/incas_catalogo_transporte.py`
6. `odoo/addons/incas_operaciones/models/incas_reserva.py`
7. `odoo/addons/incas_rrhh/models/incas_evaluacion_desempeno.py`
