from odoo import _, fields, models
from odoo.exceptions import UserError


class DmsFileMultiUploadWizard(models.TransientModel):
    _name = "incas.dms.file.multi.upload.wizard"
    _description = "Wizard de subida multiple de archivos DMS"

    directory_id = fields.Many2one(
        "dms.directory",
        string="Carpeta",
        required=True,
        domain="[('permission_create', '=', True)]",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Archivos",
    )

    def action_subir_archivos(self):
        self.ensure_one()
        if not self.attachment_ids:
            raise UserError(_("Debes seleccionar al menos un archivo."))

        self.env["dms.file"].crear_desde_adjuntos_subidos(
            self.attachment_ids.ids,
            self.directory_id.id,
        )
        return {"type": "ir.actions.client", "tag": "reload"}
