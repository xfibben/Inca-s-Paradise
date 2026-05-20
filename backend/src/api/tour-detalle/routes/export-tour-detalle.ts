export default {
  routes: [
    {
      method: 'GET',
      path: '/tour-detalles/export-csv',
      handler: 'tour-detalle.exportCsv',
      config: {
        auth: false,
        policies: [],
      },
    },
  ],
};
