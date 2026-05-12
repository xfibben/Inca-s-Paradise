from odoo import _, api, models
from odoo.exceptions import UserError


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _get_binary_max_size(self):
        return 500

    def _get_forbidden_extensions(self):
        forbidden_extensions = super()._get_forbidden_extensions()
        video_extensions = {
            "mp4",
            "mov",
            "avi",
            "mkv",
            "webm",
            "m4v",
            "mpg",
            "mpeg",
            "ogv",
        }
        return [
            extension
            for extension in forbidden_extensions
            if extension.strip().lower() not in video_extensions
        ]

    @api.model
    def crear_desde_adjuntos_subidos(self, attachment_ids, directory_id):
        if not attachment_ids:
            raise UserError(_("No se recibieron adjuntos para procesar."))

        attachments = self.env["ir.attachment"].browse(attachment_ids)
        if any(
            attachment.res_id or attachment.res_model != "dms.file"
            for attachment in attachments
        ):
            raise UserError(_("Los adjuntos recibidos no son validos."))

        values = [
            {
                "name": attachment.name,
                "content": attachment.datas,
                "mimetype": attachment.mimetype,
                "directory_id": directory_id,
            }
            for attachment in attachments
        ]
        records = self.create(values)
        attachments.with_context(dms_file=True).unlink()
        return records.ids

    def unlink(self):
        attachments = self.mapped("attachment_id")
        result = super(DmsFile, self.with_context(dms_file=True)).unlink()
        if not self.env.context.get("dms_file") and attachments:
            attachments.exists().with_context(dms_file=True).unlink()
        return result
