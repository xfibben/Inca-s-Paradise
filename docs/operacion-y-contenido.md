# Operacion y contenido

## Para quien es

Este documento sirve para contenido, operaciones, comercial, reservas y soporte interno.

Complemento:

- [Guia de uso del CMS](./guia-cms.md)
- [Guia del VPS](./vps.md)

## Que se administra desde Strapi

El CMS concentra el contenido editable del negocio:

- destinos
- detalle de destinos
- tours
- style trips
- transporte
- tipos de transporte
- vehiculos
- terminos y condiciones
- reservas
- pagos

## Que no se administra desde Strapi

Hay partes que siguen en el frontend:

- textos de interfaz multidioma
- parte de los datos estaticos en `frontend/src/data/`
- validaciones y flujo visual de reservas

## Guia rapida para el equipo de contenido

### Antes de editar

- Confirmar en que idioma se hara el cambio
- Validar si el texto vive en Strapi o en el frontend
- Revisar si el cambio afecta SEO, URLs o reservas

### Cuando editar tours o destinos

- Verificar nombre, slug y consistencia entre idiomas
- Verificar precios si el contenido impacta reservas
- Validar imagenes y textos destacados

### Cuando editar transporte o vehiculos

- Mantener consistencia de precios por vehiculo
- Revisar que la comparativa de `/tipo-transporte` siga coherente
- No cambiar la logica visual verde de este modulo

### Cuando editar terminos y condiciones

- Confirmar con legal la version vigente
- Revisar la pagina publica `/[lang]/terminos`

## Guia para reservas y operaciones

### Datos minimos a validar en una reserva

- nombre
- email
- telefono
- fecha de inicio y fin
- cantidad de adultos y ninos
- tipo y numero de documento
- nacionalidad
- servicio reservado
- ticket
- estado
- estado de pago

### Estados que debe revisar operaciones

- `estado`
- `estado_pago`

Casos comunes:

- `confirmada` + `pagado`: adelanto cobrado correctamente
- `confirmada` + `pago_completo`: servicio pagado completamente
- `pendiente` o `fallido`: revisar manualmente

## Guia para soporte interno

### Si el cliente reporta que no recibio confirmacion

1. Buscar por email o ticket en Strapi.
2. Revisar si existe pago asociado.
3. Revisar si la reserva fue sincronizada a Sheets.

### Si el cliente reporta un monto distinto

1. Revisar moneda elegida.
2. Revisar si hubo conversion de PayPal a USD.
3. Revisar `precio_tour`, `monto_web`, `pago_restante` y `monto_final`.

### Si el cliente pide cambio de idioma

- Confirmar si el cambio es contenido CMS o texto de interfaz.
- Si es contenido CMS, revisar el locale en Strapi.
- Si es interfaz, el cambio es tecnico y debe pasar al equipo de desarrollo.

## Checklist editorial recomendado

- slugs correctos
- idioma correcto
- precios revisados
- imagen destacada disponible
- CTA y enlaces validos
- terminos y condiciones vigentes
- contenido visible en el frontend

## Documentacion recomendada para la siguiente fase

- Manual de carga de imagenes y pesos recomendados
- Manual de SEO por pagina
- Procedimiento de alta de nuevos tours
- Protocolo de soporte para pagos fallidos
- Procedimiento de cierre diario entre Strapi y Google Sheets
