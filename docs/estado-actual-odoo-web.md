# Estado Actual Odoo Web

## Alcance

Este documento resume el estado actual de la migracion de contenido y reserva web hacia Odoo para:

- Tours
- Estilos de viaje
- Destinos
- Transportes

El objetivo actual ya no es depender de Strapi para estos modulos. Odoo pasa a ser la fuente principal de datos y de operacion para el frontend en estas secciones.

## Modelos principales en Odoo

### Contenido y operacion

- `incas.servicio.catalogo`
  - Servicio operativo base para reservas.
  - Contiene el campo `ip` con valores `ip3` e `ip2`.
  - Valor por defecto: `ip3`.

- `incas.tour`
  - Modelo principal de tours en Odoo.
  - Reemplaza al flujo anterior basado en el modelo legacy de catalogo tour.
  - Se vincula con `incas.servicio.catalogo` mediante `servicio_id`.
  - Es la fuente usada por el frontend para listado y detalle de tours.

- `incas.estilo.viaje`
  - Modelo de contenido para estilos de viaje.
  - Relacionado con tours.
  - Fuente del frontend para `style-trips`.

- `incas.catalogo.destino`
  - Modelo de contenido para destinos.
  - Relacionado con tours y subcategorias.

- `incas.catalogo.transporte`
  - Modelo principal de transportes para frontend y reservas.
  - Tambien vinculado con `incas.servicio.catalogo`.

### Multidioma

Los modelos migrados para frontend trabajan con contenido en:

- Espanol
- Ingles
- Portugues

En la capa web ya se consumen los valores localizados desde Odoo para tours, destinos y estilos de viaje.

## API web en Odoo

El frontend consume endpoints publicos de Odoo para las secciones migradas.

### Tours

- `GET /incas/api/web/tours`
- `GET /incas/api/web/tours/{slug}`

Datos relevantes:

- `serviceId`
- `ip`
- `slug`
- contenido localizado
- relaciones con destinos, estilos y bloques del tour

### Destinos

- `GET /incas/api/web/destinos`
- `GET /incas/api/web/destinos/{slug}`

Datos relevantes:

- contenido localizado
- relaciones con tours y subcategorias

### Estilos de viaje

- `GET /incas/api/web/style-trips`
- `GET /incas/api/web/style-trips/{slug}`

Datos relevantes:

- contenido localizado
- imagen
- orden
- tours relacionados

### Transportes

- `GET /incas/api/web/transportes`
- `GET /incas/api/web/transportes/{slug}`
- `GET /incas/api/web/tipo-transportes`
- `GET /incas/api/web/tipo-transportes/{slug}`

Datos relevantes:

- `serviceId`
- `ip`
- contenido localizado
- vehiculos, precios y tipos relacionados

### Filtro por IP

Los listados web de tours y transportes aceptan filtro:

- `?ip=ip3`
- `?ip=ip2`

Si no se especifica, los registros existentes y nuevos quedan en `ip3` por defecto.

## Estado del frontend

### Ya migrado a Odoo

- Menu y navegacion de destinos
- Menu y navegacion de estilos de viaje
- Listado y detalle de tours
- Listado y detalle de destinos
- Listado y detalle de estilos de viaje
- Listado y detalle de transportes
- Flujo de reserva de tours y transportes
- Voucher de reserva usando datos resueltos desde Odoo
- Sitemap de las secciones migradas

### Flujo de reserva actual

El frontend ya no necesita identificadores legacy del flujo anterior para crear reservas en tours y transportes migrados.

Ahora el flujo usa:

- `serviceId`
- `tourSlug`
- `transporteSlug`

La resolucion del servicio en Odoo ocurre en `incas.reserva` usando esos valores.

## Limpieza realizada

### Odoo

Se retiraron del addon `incas_reservas` los restos operativos del flujo anterior:

- campos `strapi_id`
- campos `strapi_document_id`
- sincronizacion `sync_from_strapi`
- helpers de consulta remota del contenido antiguo
- vistas que mostraban identificadores legacy
- fallback operativo de reservas contra identificadores legacy

Tambien se elimino el modelo legacy de tour que ya no formaba parte del nuevo flujo:

- `incas.catalogo.tour`

### Frontend

Se limpiaron los restos operativos del flujo anterior en las secciones migradas:

- reserva de tours y transportes ya no envia ids legacy
- ahora envia `serviceId` y slugs
- paginas de tour y transporte inyectan datos Odoo al modal de reserva
- voucher usa el estado actual del flujo
- se elimino un componente legacy sin uso que seguia acoplado al contenido anterior

## Menu administrativo en Odoo

Se creo el menu principal `Catalogo` antes de `Configuracion`.

Dentro de `Catalogo` quedan:

- Catalogo de servicios
- Transporte
- Destinos
- Estilos de viaje
- Tours
- Hoteles
- Tarifas de hotel
- Extras
- Tarifas de extra

Dentro de `Transporte` quedan:

- Tipos de transporte
- Vehiculos
- Transportes

## Consideraciones pendientes

Todavia existen paginas informativas del frontend que siguen consumiendo contenido no migrado a Odoo. No forman parte de este bloque funcional de tours, destinos, estilos de viaje y transportes.

Entre ellas pueden seguir existiendo rutas como:

- nosotros
- preguntas frecuentes
- terminos
- politicas
- cancelaciones

Si se quiere eliminar completamente Strapi del proyecto, el siguiente bloque debe ser migrar esas paginas informativas y luego retirar sus utilidades asociadas.

## Conclusión

Para tours, destinos, estilos de viaje y transportes, el frontend ya puede operar con Odoo como fuente principal de contenido y reserva.

La sincronizacion operativa con el flujo anterior fue retirada en los modulos migrados.
