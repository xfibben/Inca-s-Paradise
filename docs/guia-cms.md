# Guia de uso del CMS

## Objetivo

Esta guia sirve para cualquier persona del equipo que use Strapi para crear, editar, publicar o revisar informacion del sitio.

## Que se gestiona desde el CMS

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

## Tareas habituales

### Crear o editar contenido

1. Ingresar al panel de Strapi.
2. Ir al tipo de contenido correspondiente.
3. Crear o editar el registro.
4. Revisar idioma, slug, imagenes y precios.
5. Guardar y publicar si corresponde.

## Publicacion

Puntos a revisar antes de publicar:

- titulo correcto
- slug correcto
- idioma correcto
- precios revisados
- relaciones correctas
- imagen principal cargada

## Idiomas en Strapi

- Cada contenido debe revisarse por locale.
- El frontend usa codigos cortos de idioma.
- Si falta una traduccion en el sitio, revisar si el contenido fue creado en el locale correcto.

## Reservas

En `reserva` se debe revisar:

- ticket
- nombre
- servicio
- fechas
- estado
- estado de pago
- montos

Interpretacion basica:

- `confirmada` + `pagado`: adelanto confirmado
- `confirmada` + `pago_completo`: pago total completado
- `fallido`: pago con problema

## Pagos

En `pago` se debe revisar:

- proveedor
- metodo
- moneda
- monto
- estado
- transaccion
- orden
- fecha

## Buenas practicas de uso

- No editar datos en masa sin validar el impacto.
- No cambiar slugs sin revisar enlaces y SEO.
- No asumir que un texto vive en Strapi si no aparece en el CMS.
- Si un cambio no se refleja, confirmar si el registro esta publicado.

## Cuando escalar al equipo tecnico

- La traduccion no existe en el CMS
- El cambio no aparece aunque el contenido esta publicado
- La reserva existe pero no aparece en Google Sheets
- El pago esta en estado inconsistente
- Hay que tocar textos de interfaz o flujo de reserva
