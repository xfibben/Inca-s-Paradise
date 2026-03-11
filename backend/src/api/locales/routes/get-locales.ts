export default {
  routes: [
    {
      method: 'GET',
      path: '/locales',
      handler: 'locale-controller.getLocales',
      config: {
        auth: false,
        policies: [],
      },
    },
  ],
};
