# SEO Improvements para Inca's Paradise - Landing Page

## ✅ Implementado

### 1. **Componente SEO Reutilizable** (`src/components/SEO/SEOHead.astro`)
- Meta tags críticas (description, robots, viewport)
- Open Graph tags para redes sociales (Facebook, LinkedIn)
- Twitter Card tags para compartir en Twitter
- Hreflang tags para i18n multiidioma
- JSON-LD Schema.org estructurado
- Canonical links (anti-duplicate content)

### 2. **robots.txt** (`public/robots.txt`)
- Permite indexación de rutas principales
- Disallow de rutas administrativas
- Sitemap reference
- Crawl-delay optimizado por bot

### 3. **Sitemap XML Dinámico** (`src/pages/sitemap.xml.ts`)
- Genera automáticamente el sitemap
- Incluye todas las rutas por idioma
- Change frequency y prioridades configuradas
- URL: `https://incasparadise.com/sitemap.xml`

### 4. **Meta Descriptions Optimizadas por Idioma**
```
ES: "Viajes personalizados de lujo a Perú. Experiencie el Camino Inca..."
EN: "Tailor-made luxury travel in Peru. Experience the Inca Trail..."
PT: "Viagens personalizadas de luxo no Peru..."
```

### 5. **Schema.org Structured Data** (JSON-LD)
- **Type**: TravelAgency
- Incluye:
  - Nombre, descripción, URL
  - Logo e imagen
  - Redes sociales
  - Dirección (Puno, Perú)
  - Contacto (teléfono, email)
  - Rango de precios

### 6. **Alt Text Mejorados**
- Hero images: Descripciones específicas de contenido
- Destinos: Nombres de ubicaciones incluidos
- Certificaciones: Nombres de organismos

### 7. **Titles por Idioma Mejorados**
- Incluyen palabras clave (Perú, Inca Trail, Machu Picchu)
- Incluyen marca + descriptor único
- Longitud óptima (55-60 caracteres)

### 8. **Hreflang Implementado**
```html
<link rel="alternate" hreflang="es-PE" href="..." />
<link rel="alternate" hreflang="en" href="..." />
<link rel="alternate" hreflang="pt-BR" href="..." />
<link rel="alternate" hreflang="x-default" href="..." />
```

## 📋 Próximos Pasos (Recomendados)

### 1. **Estructura de Headings Mejorada**
Verificar que los headings sigan una jerarquía correcta:
```
<h1> - Una sola por página (título principal)
<h2> - Secciones principales
<h3> - Subsecciones
```

### 2. **Imágenes Hero Optimizadas**
Para aún mejor rendimiento, convertir a WebP:
```bash
cwebp imagen.jpg -o imagen.webp -q 80
```

### 3. **Breadcrumbs Schema.org**
Agregara en páginas de destinos y tours:
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [...]
}
```

### 4. **LocalBusiness vs TravelAgency**
Revisar si LocalBusiness schema es más apropiado por estar en Puno.

### 5. **Rich Cards para Reviews**
Implementar Review schema con ratings verificados:
```json
{
  "@type": "Review",
  "@ratingValue": "4.9",
  "@author": "Google Reviews"
}
```

### 6. **Internal Linking Strategy**
- Vincular destinos en Hero
- Vincular tours desde destinos
- Crear contenido relacionado
- Usar anchor text descriptivo

### 7. **Performance Core Web Vitals**
Continuar monitoreando:
- LCP (Largest Contentful Paint)
- FID (First Input Delay)
- CLS (Cumulative Layout Shift)

### 8. **XML Sitemap Dinámico Mejorado**
Agregar tours y destinos dinámicos desde Strapi:
```typescript
// Fetch de Strapi
const tours = await fetch('http://strapi/api/tours');
const destinations = await fetch('http://strapi/api/destinos');
```

## 🔍 Verificación

### Google Search Console
1. Agregar sitemap: `https://incasparadise.com/sitemap.xml`
2. Solicitar indexación de URLs principales
3. Revisar Google Rich Results

### Herramientas Recomendadas
- [Google PageSpeed Insights](https://pagespeed.web.dev) - Rendimiento y SEO
- [Schema Validator](https://validator.schema.org) - Validar JSON-LD
- [Lighthouse](https://chrome.google.com/webstore) - Auditoría completa
- [SEMrush](https://www.semrush.com) - Análisis competitivo

## 📊 KPIs a Monitorear

1. **Posiciones en Google** - Tours/destinos principales
2. **CTR desde búsqueda** - Mejorar titles/descriptions
3. **Impresiones** - Indexación de nuevas URLs
4. **Core Web Vitals** - Performance
5. **Conversión** - Bookings desde búsqueda orgánica

## 🚀 Configuración de Domain
En `astro.config.mjs`, asegurar que `site` esté configurado:
```javascript
export default defineConfig({
  site: "https://incasparadise.com",
  // ...
});
```

Esto es crítico para que funcionen:
- Canonical URLs
- Sitemap
- Hreflang tags
