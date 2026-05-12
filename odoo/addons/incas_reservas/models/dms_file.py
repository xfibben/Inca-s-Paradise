from odoo import api, models


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _actualizar_pasajeros_documentales(self, directory_ids=None):
        directory_ids = set(directory_ids or [])
        directory_ids.update(self.exists().mapped("directory_id").ids)
        if not directory_ids:
            return
        directory_model = self.env["dms.directory"].sudo()
        passenger_directories = directory_model.search([("id", "parent_of", list(directory_ids))])
        pasajeros = self.env["incas.pasajero"].sudo().search([("documento_directory_id", "in", passenger_directories.ids)])
        pasajeros._actualizar_resumen_documental()

    @api.model_create_multi
    def create(self, vals_list):
        archivos = super().create(vals_list)
        archivos._actualizar_pasajeros_documentales()
        return archivos

    def write(self, vals):
        previous_directory_ids = self.mapped("directory_id").ids
        result = super().write(vals)
        self._actualizar_pasajeros_documentales(previous_directory_ids)
        return result

    def unlink(self):
        previous_directory_ids = self.mapped("directory_id").ids
        result = super().unlink()
        self._actualizar_pasajeros_documentales(previous_directory_ids)
        return result
