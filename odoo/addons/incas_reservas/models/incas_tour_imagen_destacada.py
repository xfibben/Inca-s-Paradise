from odoo import api, fields, models


class IncasTourImagenDestacada(models.Model):
    _name = "incas.tour.imagen.destacada"
    _description = "Imagen destacada de tour"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    tour_id = fields.Many2one("incas.tour", string="Tour", required=True, ondelete="cascade")
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
            tour = record.tour_id
            if not tour:
                continue
            directorio = tour._asegurar_subcarpeta_documental("Imagenes destacadas")
            if not record.imagen:
                if record.imagen_file_id:
                    record.imagen_file_id.unlink()
                    record.imagen_file_id = False
                continue
            archivo = tour._guardar_archivo_dms(
                record.imagen,
                "imagen-destacada",
                archivo_actual=record.imagen_file_id,
                directory=directorio,
            )
            record.imagen_file_id = archivo.id

    def unlink(self):
        tours = self.mapped("tour_id")
        archivos = self.mapped("imagen_file_id")
        result = super().unlink()
        if archivos:
            archivos.unlink()
        if tours:
            tours._sincronizar_servicio_operativo()
        return result
