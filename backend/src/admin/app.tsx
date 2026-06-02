import type { StrapiApp } from '@strapi/strapi/admin';

import { CancelacionesExportButton } from './components/CancelacionesExportButton';
import { DestinoExportButton } from './components/DestinoExportButton';
import { PreguntasFrecuentesExportButton } from './components/PreguntasFrecuentesExportButton';
import { TourExportButton } from './components/TourExportButton';

export default {
  config: {
    locales: [],
  },
  bootstrap(app: StrapiApp) {
    app.getPlugin('content-manager').injectComponent('listView', 'actions', {
      name: 'export-tours-csv',
      Component: TourExportButton,
    });
    app.getPlugin('content-manager').injectComponent('listView', 'actions', {
      name: 'export-destinos-csv',
      Component: DestinoExportButton,
    });
    app.getPlugin('content-manager').injectComponent('editView', 'right-links', {
      name: 'export-cancelaciones-csv',
      Component: CancelacionesExportButton,
    });
    app.getPlugin('content-manager').injectComponent('editView', 'right-links', {
      name: 'export-preguntas-frecuentes-csv',
      Component: PreguntasFrecuentesExportButton,
    });
  },
};
