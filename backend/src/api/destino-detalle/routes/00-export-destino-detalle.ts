export default {
  routes: [
    {
      method: 'GET',
      path: '/destino-detalles/export-csv',
      handler: 'destino-detalle.exportCsv',
      config: {
        auth: false,
        policies: [],
      },
    },
  ],
};
