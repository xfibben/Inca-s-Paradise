import base64
import html
import json
import logging
import mimetypes
import re
import struct
import unicodedata

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)
RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")


def _clean_filename(name):
    return name.replace("<", "")


def _is_video_mimetype(mimetype):
    return (mimetype or "").startswith("video/")


def _iter_mp4_boxes(binary, start=0, end=None):
    if end is None:
        end = len(binary)

    offset = start
    while offset + 8 <= end:
        size = struct.unpack(">I", binary[offset : offset + 4])[0]
        box_type = bytes(binary[offset + 4 : offset + 8])
        header_size = 8

        if size == 0:
            box_end = end
        elif size == 1:
            if offset + 16 > end:
                return
            size = struct.unpack(">Q", binary[offset + 8 : offset + 16])[0]
            header_size = 16
            box_end = offset + size
        else:
            box_end = offset + size

        if size < header_size or box_end > end:
            return

        yield {
            "type": box_type,
            "start": offset,
            "end": box_end,
            "size": size,
            "header_size": header_size,
        }

        if box_end <= offset:
            return
        offset = box_end


def _patch_moov_chunk_offsets(binary, delta):
    data = bytearray(binary)
    stack = [(0, len(data))]

    while stack:
        start, end = stack.pop()
        for box in _iter_mp4_boxes(data, start, end):
            box_type = box["type"]
            payload_start = box["start"] + box["header_size"]

            if box_type == b"stco":
                if payload_start + 8 > box["end"]:
                    return binary
                entry_count = struct.unpack(
                    ">I", data[payload_start + 4 : payload_start + 8]
                )[0]
                table_start = payload_start + 8
                table_end = table_start + (entry_count * 4)
                if table_end > box["end"]:
                    return binary
                for index in range(entry_count):
                    pos = table_start + (index * 4)
                    current = struct.unpack(">I", data[pos : pos + 4])[0]
                    updated = current + delta
                    if updated > 0xFFFFFFFF:
                        return binary
                    data[pos : pos + 4] = struct.pack(">I", updated)
                continue

            if box_type == b"co64":
                if payload_start + 8 > box["end"]:
                    return binary
                entry_count = struct.unpack(
                    ">I", data[payload_start + 4 : payload_start + 8]
                )[0]
                table_start = payload_start + 8
                table_end = table_start + (entry_count * 8)
                if table_end > box["end"]:
                    return binary
                for index in range(entry_count):
                    pos = table_start + (index * 8)
                    current = struct.unpack(">Q", data[pos : pos + 8])[0]
                    data[pos : pos + 8] = struct.pack(">Q", current + delta)
                continue

            if box_type in {
                b"moov",
                b"trak",
                b"mdia",
                b"minf",
                b"stbl",
                b"edts",
                b"udta",
            }:
                stack.append((payload_start, box["end"]))

    return bytes(data)


def _optimize_video_for_preview(binary, filename, mimetype):
    lower_name = (filename or "").lower()
    lower_mimetype = (mimetype or "").lower()
    if not (
        lower_name.endswith((".mp4", ".mov", ".m4v"))
        or lower_mimetype.startswith("video/mp4")
        or lower_mimetype == "video/quicktime"
    ):
        return binary

    boxes = list(_iter_mp4_boxes(binary))
    if not boxes:
        return binary

    moov_box = next((box for box in boxes if box["type"] == b"moov"), None)
    mdat_box = next((box for box in boxes if box["type"] == b"mdat"), None)

    if not moov_box or not mdat_box or moov_box["start"] < mdat_box["start"]:
        return binary

    moov_binary = binary[moov_box["start"] : moov_box["end"]]
    patched_moov = _patch_moov_chunk_offsets(moov_binary, len(moov_binary))

    reordered = bytearray()
    inserted = False

    for box in boxes:
        if box["type"] == b"moov":
            continue
        if not inserted and box["type"] == b"mdat":
            reordered.extend(patched_moov)
            inserted = True
        reordered.extend(binary[box["start"] : box["end"]])

    if not inserted:
        return binary

    return bytes(reordered)


def _get_dms_file_binary(archivo):
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
        binary = base64.b64decode(archivo.with_context(bin_size=False).content or b"")

    guessed_from_name = mimetypes.guess_type(archivo.name or "")[0]
    mimetype = (
        mimetype
        or guessed_from_name
        or guess_mimetype(binary)
        or "application/octet-stream"
    )
    return binary, mimetype


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
        binary, mimetype = _get_dms_file_binary(archivo)

        if _is_video_mimetype(mimetype):
            safe_title = html.escape(archivo.name or "Video")
            stream_url = f"/incas/dms/file/{archivo.id}/stream"
            body = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    html, body {{
      margin: 0;
      background: #111;
      height: 100%;
    }}
    body {{
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    video {{
      width: 100%;
      height: 100%;
      max-width: 100vw;
      max-height: 100vh;
      background: #000;
    }}
  </style>
</head>
<body>
  <video controls preload="metadata" playsinline>
    <source src="{html.escape(stream_url, quote=True)}" type="{html.escape(mimetype, quote=True)}">
  </video>
</body>
</html>"""
            return request.make_response(
                body,
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("X-Content-Type-Options", "nosniff"),
                ],
            )

        return _build_range_response(binary, mimetype, archivo.name)

    @http.route("/incas/dms/file/<int:file_id>/stream", type="http", auth="user")
    def stream_archivo_dms(self, file_id, **kwargs):
        archivo = request.env["dms.file"].browse(file_id)
        archivo.check_access("read")
        binary, mimetype = _get_dms_file_binary(archivo)
        binary = _optimize_video_for_preview(binary, archivo.name, mimetype)
        return _build_range_response(binary, mimetype, archivo.name)
