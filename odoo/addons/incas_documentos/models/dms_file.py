import base64
import struct

from odoo import _, api, models
from odoo.exceptions import UserError


class DmsFile(models.Model):
    _inherit = "dms.file"

    def _iter_mp4_boxes(self, binary, start=0, end=None):
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

    def _patch_moov_chunk_offsets(self, binary, delta):
        data = bytearray(binary)
        stack = [(0, len(data))]

        while stack:
            start, end = stack.pop()
            for box in self._iter_mp4_boxes(data, start, end):
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

    def _optimize_video_for_preview(self, binary, filename, mimetype):
        lower_name = (filename or "").lower()
        lower_mimetype = (mimetype or "").lower()
        if not (
            lower_name.endswith((".mp4", ".mov", ".m4v"))
            or lower_mimetype.startswith("video/mp4")
            or lower_mimetype == "video/quicktime"
        ):
            return binary

        boxes = list(self._iter_mp4_boxes(binary))
        if not boxes:
            return binary

        moov_box = next((box for box in boxes if box["type"] == b"moov"), None)
        mdat_box = next((box for box in boxes if box["type"] == b"mdat"), None)

        if not moov_box or not mdat_box or moov_box["start"] < mdat_box["start"]:
            return binary

        moov_binary = binary[moov_box["start"] : moov_box["end"]]
        patched_moov = self._patch_moov_chunk_offsets(moov_binary, len(moov_binary))

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

        values = []
        for attachment in attachments:
            binary = base64.b64decode(attachment.datas or b"")
            optimized_binary = self._optimize_video_for_preview(
                binary, attachment.name, attachment.mimetype
            )
            values.append(
                {
                    "name": attachment.name,
                    "content": base64.b64encode(optimized_binary),
                    "mimetype": attachment.mimetype,
                    "directory_id": directory_id,
                }
            )
        records = self.create(values)
        attachments.with_context(dms_file=True).unlink()
        return records.ids

    def unlink(self):
        attachments = self.mapped("attachment_id")
        result = super(DmsFile, self.with_context(dms_file=True)).unlink()
        if not self.env.context.get("dms_file") and attachments:
            attachments.exists().with_context(dms_file=True).unlink()
        return result

    def action_unlink_incas(self):
        self.unlink()
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def unlink_incas_safe(self, record_id):
        record = self.browse(record_id).exists()
        if not record:
            return True
        record.unlink()
        return True
