from odoo import models


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
