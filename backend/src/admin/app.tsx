import type { StrapiApp } from '@strapi/strapi/admin';

import { DestinoExportButton } from './components/DestinoExportButton';
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
  },
};
