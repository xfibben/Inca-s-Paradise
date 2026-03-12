# Guía de Estilos - Tipografía

## Tipografía General

Este proyecto utiliza **Tailwind CSS** y **Flowbite** para gestionar la tipografía y los estilos visuales.

---

## Familias de Fuentes

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen",
  "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue",
  sans-serif;
```

---

## Sistema de Tipografía Responsivo

## Filosofía de Diseño

Para mantener **consistencia y simplificar** el desarrollo, este proyecto utiliza **elementos tipográficos responsivos** que se adaptan según el dispositivo.

---

## H1 - Títulos Principales

### Especificaciones
- **Móvil:** `text-2xl` (24px)
- **Tablet:** `md:text-3xl` (30px)
- **Desktop:** `lg:text-4xl` (36px)
- **Peso:** `font-bold`
- **Color:** `text-gray-900`

```html
<head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500&display=swap" rel="stylesheet" />
</head>
<h1 class="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 leading-tight mb-4 md:mb-6 lg:mb-8 style="font-family: 'Playfair Display', serif; font-style: italic;">
  Título Principal
</h1>
```

---

## H2 - Subtítulos Secundarios

### Especificaciones
- **Móvil:** `text-lg` (18px)
- **Tablet:** `md:text-xl` (20px)
- **Desktop:** `lg:text-2xl` (24px)
- **Peso:** `font-semibold`
- **Color:** `text-gray-800`

```html
<h2 class="text-lg md:text-xl lg:text-2xl font-semibold text-gray-800 leading-snug my-3 md:my-4 lg:my-6">
  Subtítulo Secundario
</h2>
```

---

## H3 - Subtítulos Terciarios

### Especificaciones
- **Móvil:** `text-base` (16px)
- **Tablet:** `md:text-lg` (18px)
- **Desktop:** `lg:text-xl` (20px)
- **Peso:** `font-semibold`
- **Color:** `text-gray-700`

```html
<h3 class="text-base md:text-lg lg:text-xl font-semibold text-gray-700 leading-snug my-2 md:my-3 lg:my-4">
  Subtítulo Terciario
</h3>
```

---

## P - Párrafos de Contenido

### Especificaciones
- **Móvil:** `text-sm` (14px)
- **Tablet:** `md:text-base` (16px)
- **Desktop:** `lg:text-lg` (18px)
- **Peso:** `font-normal`
- **Color:** `text-gray-700`

```html
<p class="text-sm md:text-base lg:text-lg text-gray-700 leading-relaxed mb-3 md:mb-4 lg:mb-6">
  Párrafo de contenido principal.
</p>
```

---

## Tabla Resumen

| Elemento | Móvil | Tablet | Desktop | Peso | Color |
|----------|-------|--------|---------|------|-------|
| **H1** | 24px | 30px | 36px | bold | gray-900 |
| **H2** | 18px | 20px | 24px | semibold | gray-800 |
| **H3** | 16px | 18px | 20px | semibold | gray-700 |
| **P** | 14px | 16px | 18px | normal | gray-700 |

---

## Breakpoints

```
Móvil:   0px - 767px
Tablet:  768px - 1023px
Desktop: 1024px+
```

---
