export default {
  routes: [
    {
      method: 'GET',
      path: '/preguntas-frecuentes/export-csv',
      handler: 'preguntas-frecuentes.exportCsv',
      config: {
        auth: false,
        policies: [],
      },
    },
  ],
};
