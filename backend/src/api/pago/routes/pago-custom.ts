/**
 * Rutas custom del módulo de pagos
 */

export default {
  routes: [
    {
      method: 'POST',
      path: '/pagos/iniciar',
      handler: 'pago.iniciar',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/pagos/confirmar',
      handler: 'pago.confirmar',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/pagos/webhook',
      handler: 'pago.webhook',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/pagos/tipo-cambio',
      handler: 'pago.tipoCambio',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
