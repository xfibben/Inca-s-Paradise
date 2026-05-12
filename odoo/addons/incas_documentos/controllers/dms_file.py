from odoo import http
from odoo.http import request


class IncasDocumentosDmsFileController(http.Controller):
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
