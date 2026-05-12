import json
import logging
import unicodedata

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


def _clean_filename(name):
    return name.replace("<", "")


class IncasDocumentosDmsFileController(http.Controller):
    @http.route(
        "/web/binary/upload_attachment",
        type="http",
        auth="user",
        max_content_length=None,
    )
    def upload_attachment(self, model, id, ufile, callback=None):
        files = request.httprequest.files.getlist("ufile")
        attachment_model = request.env["ir.attachment"]
        args = []

        for uploaded_file in files:
            filename = uploaded_file.filename
            if request.httprequest.user_agent.browser == "safari":
                filename = unicodedata.normalize("NFD", uploaded_file.filename)
            try:
                attachment = attachment_model.create(
                    {
                        "name": filename,
                        "raw": uploaded_file.read(),
                        "res_model": model,
                        "res_id": int(id),
                    }
                )
                attachment._post_add_create()
            except AccessError:
                args.append(
                    {"error": _("You are not allowed to upload an attachment here.")}
                )
            except Exception:
                args.append({"error": _("Something horrible happened")})
                _logger.exception("Fail to upload attachment %s", uploaded_file.filename)
            else:
                args.append(
                    {
                        "filename": _clean_filename(filename),
                        "mimetype": attachment.mimetype,
                        "id": attachment.id,
                        "size": attachment.file_size,
                    }
                )

        if callback:
            return '%s(%s)' % (json.dumps(_clean_filename(callback)), json.dumps(args))
        return json.dumps(args)

    @http.route("/incas/dms/file/<int:file_id>/content", type="http", auth="user")
    def descargar_archivo_dms(self, file_id, download=None, **kwargs):
        archivo = request.env["dms.file"].browse(file_id)
        archivo.check_access("read")

        query = "download=true" if download else "download=false"

        if archivo.attachment_id:
            return request.redirect(
                f"/web/content/ir.attachment/{archivo.attachment_id.id}/datas?{query}"
            )

        if archivo.content_file:
            return request.redirect(
                "/web/content"
                f"?id={archivo.id}&field=content_file&model=dms.file"
                f"&filename_field=name&{query}"
            )

        return request.redirect(
            "/web/content"
            f"?id={archivo.id}&field=content&model=dms.file"
            f"&filename_field=name&{query}"
        )
