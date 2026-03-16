# 🎯 SEO Checklist - Inca's Paradise

## ✅ COMPLETADO

- [x] **Meta tags básicos** - Charset, viewport, description
- [x] **Open Graph tags** - Facebook, LinkedIn sharing (en SEOHead.astro)
- [x] **Twitter Card tags** - Twitter sharing mejorado
- [x] **Canonical links** - Anti-duplicate content
- [x] **Hreflang tags** - i18n multiidioma
- [x] **JSON-LD Schema** - TravelAgency estructura
- [x] **robots.txt** - Instrucciones para buscadores
- [x] **Sitemap XML** - Generador dinámico (src/pages/sitemap.xml.ts)
- [x] **Title tags** - Por idioma, optimizado
- [x] **Meta descriptions** - Por idioma, optimizado
- [x] **Alt text mejorado** - Hero images y certificaciones
- [x] **site configuration** - astro.config.mjs
- [x] **Image optimization** - Lazy loading + dimensiones
- [x] **Performance** - Preload/Prefetch estratégico
- [x] **Component SEO** - SEOHead.astro reutilizable
- [x] **Performance: Core Web Vitals** - LCP optimizado

## 📋 POR HACER (Prioritario)

### 1. **Actualizar Canvas i18n** ⚠️ IMPORTANTE
```typescript
// src/i18n.ts - Revisar que exporte Language correctamente
export type Language = 'es' | 'en' | 'pt';
```

### 2. **Breadcrumb Schema** en páginas dinámicas
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "/" },
    { "@type": "ListItem", "position": 2, "name": "Destinos", "item": "/destinos" },
    { "@type": "ListItem", "position": 3, "name": "[Destino]", "item": "/destinos/[slug]" }
  ]
}
```

### 3. **Schema para Tours y Destinos** 
```typescript
// src/components/LandingPage/DestinationsGallery.astro
// Agregar schema "@type": "TouristDestination"
```

### 4. **Contar palabras clave principales**
Meta keywords por sección:
- Hero: Perú, Machu Picchu, Inca Trail, aventuras
- Destinos: Cusco, Puno, Lake Titicaca
- Sustainability: turismo responsable, sostenibilidad

### 5. **Verificación en Google Search Console**
1. [ ] Agregar sitemap.xml
2. [ ] Solicitar indexación de URLs principales
3. [ ] Revisar errores de indexación
4. [ ] Monitorear Rich Results

### 6. **Implementar FAQ Schema** (si aplica)
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Cuál es el mejor momento para visitar?",
      "acceptedAnswer": {"@type": "Answer", "text": "..."}
    }
  ]
}
```

### 7. **Reviews/Ratings Schema**
Integrar con Trustpilot/Google Reviews:
```json
{
  "@type": "AggregateRating",
  "@ratingValue": "4.9",
  "@ratingCount": "151"
}
```

## 🔍 VALIDAR & VERIFICAR

- [ ] Validar JSON-LD en [Schema Validator](https://validator.schema.org)
- [ ] Test en [Google PageSpeed Insights](https://pagespeed.web.dev)
- [ ] Test en [Lighthouse](https://chromedevtools.io)
- [ ] Mobile-first testing
- [ ] Verificar robots.txt: `incasparadise.com/robots.txt`
- [ ] Verificar sitemap.xml: `incasparadise.com/sitemap.xml`

## 🎓 CONFIGURACIÓN DE DOMINIO

**ANTES DE IR A PRODUCCIÓN:**
1. Cambiar `site` en `astro.config.mjs` a dominio real
2. Agregar Google Analytics 4 (GA4)
3. Configurar Google Search Console
4. Configurar Bing Webmaster Tools
5. Verificar PageSpeed performance

```javascript
// astro.config.mjs
export default defineConfig({
  site: 'https://incasparadise.com', // ← CAMBIAR
  // ...
});
```

## 📊 KPIs A MONITOREAR (Mensual)

| Métrica | Target | Herramienta |
|---------|--------|------------|
| **Impressiones** | +20% | GSC |
| **CTR** | >4% | GSC |
| **Posición promedio** | <10 | GSC |
| **Core Web Vitals** | Good | PageSpeed |
| **Bounce Rate** | <60% | GA4 |
| **Conversion Rate** | >2% | GA4 |

## 🚀 ROADMAP SEO (Next 3 months)

### Mes 1: Fundación
- [x] Meta tags y Schema.org
- [x] robots.txt y sitemap
- [ ] Google Search Console setup
- [ ] Baseline de posiciones

### Mes 2: Contenido
- [ ] Mejorar descriptions dinámicamente desde CMS
- [ ] Agregar FAQ dinamico
- [ ] Blog con contenido largo (1500+ palabras)

### Mes 3: Linkbuilding
- [ ] Contactar directorios de turismo
- [ ] Guest blogging en viajes
- [ ] Notas de prensa digitales

## 📞 CONTACTOS IMPORTANTES

- **Google Search Console**: [URL](https://search.google.com/search-console)
- **Bing Webmaster Tools**: [URL](https://www.bing.com/webmasters)
- **Semrush**: Para tracking competitivo
- **Ahrefs**: Para análisis de backlinks

---

**Última actualización**: 16 de Marzo, 2026
**Responsable**: Arturo
**Estado**: En Progreso ✓
