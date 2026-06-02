export default {
  routes: [
    {
      method: 'GET',
      path: '/cancelaciones/export-csv',
      handler: 'cancelaciones.exportCsv',
      config: {
        auth: false,
        policies: [],
      },
    },
  ],
};
