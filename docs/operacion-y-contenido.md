# Operación y contenido

## 1. Dónde vive cada cosa

### En Odoo

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
- reservas
- pagos

### En frontend

- textos de interfaz
- estructura visual
- i18n de botones y labels
- libro de reclamaciones
- analytics

## 2. Qué toca el equipo de contenido

En Odoo debe poder mantener:

- slugs
- SEO
- títulos
- descripciones
- galerías
- destacados
- itinerarios
- incluye/no incluye
- horarios
- artículos de sostenibilidad
- páginas legales

## 3. Qué toca operaciones

En Odoo:

- reservas
- pagos
- pasajeros
- estados
- agenda
- línea operativa
- pase operativo

## 4. Qué toca RRHH

En Odoo:

- trabajadores
- boletas
- certificados
- evaluación semanal y mensual

## 5. Reglas para contenido público

- no cambiar slug sin revisar enlaces frontend y sitemap
- no borrar registros activos sin revisar navbar o listados
- no asumir que `fr` e `it` tienen contenido completo
- si el texto viene en rich text, revisar render final en Astro

## 6. Checklist para editar tours

1. nombre
2. slug
3. tipo de tour
4. precio adulto USD
5. precio niño USD
6. descuento
7. destacados
8. itinerario
9. incluye
10. no incluye
11. horarios
12. SEO

## 7. Checklist para editar transportes

1. nombre
2. slug
3. tipos de transporte
4. tarifas por vehículo
5. descuento por vehículo
6. imagen y wallpaper
7. incluye
8. no incluye
9. SEO

Regla crítica:

- el precio de transporte no es único
- cada vehículo puede cambiar adulto, niño y descuento

## 8. Checklist para reservas

Validar:

- ticket
- cliente
- servicio
- fechas
- horario
- cantidades
- moneda
- descuento
- vehículo si aplica
- estado comercial
- estado reserva
- estado pago
- voucher

## 9. Estados que importan

### Comercial

- `borrador`
- `cotizada`
- `pre_reserva`
- `confirmada`
- `cancelada`

### Reserva

- `reservado`
- `por_coordinar`
- `falta_pago`
- `pagado`
- `completado`
- `finalizado`
- `cancelado`

### Pago

- `pendiente`
- `parcial`
- `pagado`
- `reembolsado`
- `cancelado`

## 10. Operación posterior a la reserva

Odoo debe dejar:

- evento de agenda
- línea operativa
- documentación de pasajeros
- correo enviado
- voucher accesible

## 11. Soporte rápido

### Si el cliente no recibió voucher

1. buscar reserva por ticket
2. revisar `voucher_url`
3. probar ruta pública del PDF
4. revisar correo

### Si el monto no cuadra

1. revisar moneda
2. revisar descuento
3. revisar vehículo en transporte
4. revisar precios USD base
5. revisar monto pagado

### Si la página pública no muestra contenido

1. revisar que el registro esté `active`
2. revisar slug
3. revisar endpoint Odoo
4. revisar render SSR en la ruta Astro

## 12. Riesgos operativos

- navbar y home dependen de contenido Odoo
- un slug roto puede romper rutas públicas
- un cambio de estructura del payload puede romper SSR
- una tarifa mal cargada en transporte impacta reserva y pago
