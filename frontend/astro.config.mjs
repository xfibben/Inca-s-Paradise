// @ts-check

import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://incasparadise.com', // Configurar dominio real cuando esté disponible
  output: 'server',
  adapter: node({
    mode: 'standalone'
  }),
  vite: {
    plugins: [tailwindcss()],
    server: {
      watch: {
        // Polling necesario en Windows con Docker para detectar cambios de archivos
        usePolling: true,
        interval: 500,
      }
    }
  },
});

