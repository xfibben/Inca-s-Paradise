import { defineConfig } from 'astro/config';

export default defineConfig({
  vite: {
    server: {
      watch: {
        usePolling: true,      // ← clave
        interval: 300,         // revisa cada 300ms (ajustable)
      },
      host: true,              // expone el servidor dentro del contenedor
      port: 4321,
    }
  }
});