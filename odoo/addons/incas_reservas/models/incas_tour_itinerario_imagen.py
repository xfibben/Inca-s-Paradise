from odoo import api, fields, models


class IncasTourItinerarioImagen(models.Model):
    _name = "incas.tour.itinerario.imagen"
    _description = "Imagen de itinerario de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    itinerario_id = fields.Many2one(
        "incas.tour.itinerario",
        string="Itinerary item",
        required=True,
        ondelete="cascade",
    )
    imagen = fields.Image(
        string="Imagen",
        compute="_compute_imagen",
        inverse="_inverse_imagen",
        store=False,
        required=True,
    )
    imagen_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)

    @api.depends("imagen_file_id")
    def _compute_imagen(self):
        for record in self:
            record.imagen = record.imagen_file_id.content if record.imagen_file_id else False

    def _inverse_imagen(self):
        for record in self:
            tour = record.itinerario_id.tour_id
            if not tour:
                continue
            directorio = tour._asegurar_subcarpeta_documental("Itinerary")
            if not record.imagen:
                if record.imagen_file_id:
                    record.imagen_file_id.unlink()
                    record.imagen_file_id = False
                continue
            archivo = tour._guardar_archivo_dms(
                record.imagen,
                "itinerary-image",
                archivo_actual=record.imagen_file_id,
                directory=directorio,
            )
            record.imagen_file_id = archivo.id

    def unlink(self):
        archivos = self.mapped("imagen_file_id")
        result = super().unlink()
        if archivos:
            archivos.unlink()
        return result
