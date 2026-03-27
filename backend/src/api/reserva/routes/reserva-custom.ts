export default {
  routes: [
    {
      method: 'POST',
      path: '/reservas/sync-sheets',
      handler: 'reserva.syncSheets',
      config: {
        auth: false, // no requiere configurar permisos en el panel
        policies: [],
        middlewares: [],
      },
    },
  ],
};
