# Guía de gestión de contenido

## 1. Panel a usar

El contenido público actual se gestiona desde `Odoo`.

Para el siguiente programador o editor:

- no asumir otro CMS como fuente activa
- validar siempre contra lo que sirve `/incas/api/web/*`

## 2. Qué se edita en Odoo

- tours
- destinos
- style trips
- transportes
- tipos de transporte
- vehículos
- sostenibilidad
- nosotros
- términos
- políticas
- cancelaciones
- preguntas frecuentes

## 3. Antes de editar

Revisar:

1. idioma
2. slug
3. SEO
4. relaciones
5. imágenes
6. si afecta navbar, home o sitemap

## 4. Publicación práctica

Después de editar:

1. guardar en Odoo
2. abrir la ruta pública del frontend
3. verificar payload Odoo si el cambio no aparece
4. limpiar caché del navegador si la imagen cambió

## 5. Campos sensibles

### Tours

- nombre
- slug
- precio adulto
- precio niño
- descuento
- destacados
- itinerario
- incluye/no incluye
- horarios

### Transportes

- nombre
- slug
- tipos de transporte
- tarifas por vehículo
- incluye/no incluye
- SEO

### Legales y corporativos

- títulos
- bloques rich text
- SEO

## 6. Errores comunes

- cambiar slug y no revisar enlaces
- editar un idioma y esperar cambio en otro
- olvidar que `fr/it` pueden caer a fallback
- cambiar tarifa de transporte sin revisar todos los vehículos

## 7. Cuándo escalar a desarrollo

- el endpoint Odoo responde bien pero el frontend no renderiza
- el rich text se ve roto
- la reserva no persiste vehículo
- el sitemap no incluye una nueva página
- la navbar no refleja un cambio de catálogo
