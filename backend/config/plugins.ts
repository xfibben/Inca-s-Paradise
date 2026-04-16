import type { Core } from '@strapi/strapi';

const config = ({ env }: Core.Config.Shared.ConfigParams): Core.Config.Plugin => ({
  upload: {
    config: {
      sizeOptimization: true,
      responsiveDimensions: true,
      // Convierte imagenes a WebP al subir
      formats: {
        thumbnail: { width: 245, height: 156 },
        small: { width: 500 },
        medium: { width: 750 },
        large: { width: 1000 },
      },
    },
  },
});

export default config;
