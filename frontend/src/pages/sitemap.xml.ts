// File: src/pages/sitemap.xml.ts
// Generates a dynamic sitemap for all available routes

import { getTranslation, languages } from '../i18n';

const baseUrl = "https://incasparadise.com"; // Change to your domain

// Define static pages for each language
const staticPages = [
  '/',
  '/destinos',
  '/claims'
];

// Generate sitemap URLs for all languages
const sitemapUrls = Object.keys(languages).flatMap(lang => 
  staticPages.map(page => ({
    url: page === '/' ? `${baseUrl}/${lang}/` : `${baseUrl}/${lang}${page}`,
    changefreq: page === '/' ? 'weekly' : 'monthly',
    priority: page === '/' ? '1.0' : '0.8'
  }))
);

// If you have dynamic routes from your CMS, add them here
// Example: tours, destinations from API

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:mobile="http://www.mobile.googlebot.org/schemas/mobile/1.0"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
${sitemapUrls
  .map(
    ({ url, changefreq, priority }) => `
  <url>
    <loc>${url}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
  </url>
`
  )
  .join('')}
</urlset>`.trim();

export async function GET() {
  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'max-age=3600'
    }
  });
}
