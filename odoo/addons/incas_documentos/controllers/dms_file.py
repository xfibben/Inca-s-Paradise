import base64
import json
import logging
import mimetypes
import re
import unicodedata

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)
RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")


def _clean_filename(name):
    return name.replace("<", "")


def _build_range_response(binary, mimetype, filename):
    httprequest = request.httprequest
    range_header = httprequest.headers.get("Range")
    size = len(binary)

    headers = [
        ("Content-Type", mimetype),
        ("Content-Disposition", f'inline; filename="{filename}"'),
        ("Accept-Ranges", "bytes"),
        ("X-Content-Type-Options", "nosniff"),
    ]

    if not range_header:
        headers.append(("Content-Length", str(size)))
        return request.make_response(binary, headers)

    match = RANGE_RE.fullmatch(range_header.strip())
    if not match:
        return request.make_response(
            b"",
            headers + [("Content-Range", f"bytes */{size}")],
            status=416,
        )

    start_text = match.group(1)
    end_text = match.group(2)
    start = int(start_text)
    end = int(end_text) if end_text else size - 1
    end = min(end, size - 1)

    if start >= size or start > end:
        return request.make_response(
            b"",
            headers + [("Content-Range", f"bytes */{size}")],
            status=416,
        )

    chunk = binary[start : end + 1]
    headers.extend(
        [
            ("Content-Length", str(len(chunk))),
            ("Content-Range", f"bytes {start}-{end}/{size}"),
        ]
    )
    return request.make_response(chunk, headers, status=206)


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
        query = "download=true" if str(download).lower() in {"1", "true", "yes", "on"} else "download=false"

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

    @http.route("/incas/dms/file/<int:file_id>/preview", type="http", auth="user")
    def vista_previa_archivo_dms(self, file_id, **kwargs):
        archivo = request.env["dms.file"].browse(file_id)
        archivo.check_access("read")

        binary = b""
        mimetype = archivo.mimetype

        if archivo.attachment_id:
            binary = archivo.attachment_id.raw or b""
            mimetype = mimetype or archivo.attachment_id.mimetype
        elif archivo.content_file:
            binary = base64.b64decode(
                archivo.with_context(bin_size=False).content_file or b""
            )
        elif archivo.content:
            binary = base64.b64decode(
                archivo.with_context(bin_size=False).content or b""
            )

        guessed_from_name = mimetypes.guess_type(archivo.name or "")[0]
        mimetype = (
            mimetype
            or guessed_from_name
            or guess_mimetype(binary)
            or "application/octet-stream"
        )
        return _build_range_response(binary, mimetype, archivo.name)
