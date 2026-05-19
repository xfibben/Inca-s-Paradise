import base64
import mimetypes
import re

from odoo import api, fields, models
from odoo.addons.dms.tools import file as dms_file_tools
from odoo.tools.mimetypes import guess_mimetype


class IncasDmsAssetMixin(models.AbstractModel):
    _name = "incas.dms.asset.mixin"
    _description = "Mixin documental para activos"

    documento_directory_id = fields.Many2one(
        "dms.directory",
        string="Carpeta documental",
        readonly=True,
        copy=False,
    )

    def _dms_storage_name(self):
        return "General"

    def _dms_root_directory_name(self):
        return self._name

    def _dms_record_display_name(self):
        self.ensure_one()
        return getattr(self, "name", False) or getattr(self, "nombre", False) or f"{self._name}-{self.id}"

    def _dms_record_fallback_name(self):
        self.ensure_one()
        return f"{self._name.replace('.', '-').upper()}-{self.id}"

    def _nombre_directorio_seguro(self, valor, fallback):
        nombre = (valor or fallback or "").strip()
        nombre = re.sub(r"[\\/:*?\"<>|]+", "-", nombre)
        nombre = re.sub(r"\s+", " ", nombre).strip(" .-_")
        return nombre or fallback

    def _obtener_storage_documental(self):
        storage_model = self.env["dms.storage"].sudo()
        storage = storage_model.search(
            [("name", "=", self._dms_storage_name())],
            limit=1,
        )
        if not storage:
            storage = storage_model.create(
                {
                    "name": self._dms_storage_name(),
                    "save_type": "file",
                }
            )
        elif storage.save_type != "file":
            storage.write({"save_type": "file"})
        return storage

    def _obtener_directorio_raiz_documental(self):
        directory_model = self.env["dms.directory"].sudo()
        storage = self._obtener_storage_documental()
        root = directory_model.search(
            [
                ("is_root_directory", "=", True),
                ("storage_id", "=", storage.id),
                ("name", "=", self._dms_root_directory_name()),
            ],
            limit=1,
        )
        if not root:
            root = directory_model.create(
                {
                    "name": self._dms_root_directory_name(),
                    "storage_id": storage.id,
                    "is_root_directory": True,
                }
            )
        return root

    def _asegurar_carpeta_documental(self):
        directory_model = self.env["dms.directory"].sudo()
        root = self._obtener_directorio_raiz_documental()
        for record in self:
            nombre_carpeta = record._nombre_directorio_seguro(
                record._dms_record_display_name(),
                record._dms_record_fallback_name(),
            )
            directory = record.documento_directory_id
            if directory:
                valores = {}
                if directory.parent_id != root:
                    valores["parent_id"] = root.id
                if directory.name != nombre_carpeta:
                    valores["name"] = nombre_carpeta
                if valores:
                    directory.write(valores)
                continue
            existente = directory_model.search(
                [("parent_id", "=", root.id), ("name", "=", nombre_carpeta)],
                limit=1,
            )
            if not existente:
                existente = directory_model.create(
                    {
                        "name": nombre_carpeta,
                        "parent_id": root.id,
                        "is_root_directory": False,
                    }
                )
            record.documento_directory_id = existente.id

    def _asegurar_subcarpeta_documental(self, nombre):
        self.ensure_one()
        self._asegurar_carpeta_documental()
        if not self.documento_directory_id:
            return self.env["dms.directory"]
        directory_model = self.env["dms.directory"].sudo()
        nombre_carpeta = self._nombre_directorio_seguro(nombre, "Archivos")
        existente = directory_model.search(
            [("parent_id", "=", self.documento_directory_id.id), ("name", "=", nombre_carpeta)],
            limit=1,
        )
        if existente:
            return existente
        return directory_model.create(
            {
                "name": nombre_carpeta,
                "parent_id": self.documento_directory_id.id,
                "is_root_directory": False,
            }
        )

    def _extension_desde_mimetype(self, mimetype):
        extension = mimetypes.guess_extension(mimetype or "")
        if extension == ".jpe":
            return ".jpg"
        return extension or ""

    def _campos_archivo_dms(self):
        return [
            nombre
            for nombre, field in self._fields.items()
            if field.type == "many2one" and getattr(field, "comodel_name", False) == "dms.file"
        ]

    def _nombre_archivo_unico(self, directory, nombre_archivo, archivo_actual=None):
        nombres = directory.sudo().file_ids.mapped("name")
        if archivo_actual and archivo_actual.name in nombres:
            nombres.remove(archivo_actual.name)
        return dms_file_tools.unique_name(nombre_archivo, nombres, escape_suffix=True)

    def _guardar_archivo_dms(self, contenido, nombre_base, archivo_actual=None, directory=None):
        self.ensure_one()
        if not contenido:
            if archivo_actual:
                archivo_actual.unlink()
            return self.env["dms.file"]
        self._asegurar_carpeta_documental()
        target_directory = directory or self.documento_directory_id
        binary_base64 = contenido if isinstance(contenido, bytes) else contenido.encode()
        try:
            binary = base64.b64decode(binary_base64)
        except Exception:
            binary = binary_base64
        mimetype = guess_mimetype(binary)
        extension = self._extension_desde_mimetype(mimetype)
        nombre_archivo = nombre_base if str(nombre_base).lower().endswith(extension.lower()) else f"{nombre_base}{extension}"
        nombre_archivo = self._nombre_archivo_unico(target_directory, nombre_archivo, archivo_actual=archivo_actual)
        valores = {
            "name": nombre_archivo,
            "content": contenido,
            "directory_id": target_directory.id,
            "mimetype": mimetype,
        }
        if archivo_actual:
            archivo_actual.write(valores)
            return archivo_actual
        return self.env["dms.file"].sudo().create(valores)

    def action_ver_documentos(self):
        self.ensure_one()
        self._asegurar_carpeta_documental()
        if not self.documento_directory_id:
            return False
        return self.documento_directory_id.action_dms_files_all_directory()

    def unlink(self):
        for record in self:
            for campo in record._campos_archivo_dms():
                archivo = record[campo]
                if archivo:
                    archivo.unlink()
            if record.documento_directory_id:
                record.documento_directory_id.unlink()
        return super().unlink()
