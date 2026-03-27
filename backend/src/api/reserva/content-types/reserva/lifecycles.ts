// Sincroniza reservas con Google Sheets vía Apps Script (gratis, sin Google Cloud)
async function sincronizarConSheets(id: number) {
  const url = process.env.GOOGLE_APPS_SCRIPT_URL;
  if (!url) {
    strapi.log.warn('[Sheets] GOOGLE_APPS_SCRIPT_URL no configurado');
    return;
  }

  // Fetch con relaciones populadas para obtener nombre del tour/transporte
  const reserva = await strapi.entityService.findOne('api::reserva.reserva', id, {
    populate: ['tour', 'transportes'],
  });

  if (!reserva) return;

  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry: reserva }),
      redirect: 'follow',
    });

    strapi.log.info(`[Sheets] Reserva ID ${id} sincronizada`);
  } catch (error) {
    strapi.log.error('[Sheets] Error al sincronizar:', error);
  }
}

export default {
  async afterCreate(event: any) {
    await sincronizarConSheets(event.result.id);
  },

  async afterUpdate(event: any) {
    await sincronizarConSheets(event.result.id);
  },
};
