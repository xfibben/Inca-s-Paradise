from odoo import api, fields, models
from odoo.exceptions import UserError


class IncasPasajero(models.Model):
    _name = "incas.pasajero"
    _description = "Pasajero"
    _order = "apellidos, nombres"
    _rec_name = "name"

    name = fields.Char(string="Nombre completo", compute="_compute_name", store=True)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade")
    nombres = fields.Char(string="Nombres", required=True)
    apellidos = fields.Char(string="Apellidos", required=True)
    tipo_documento = fields.Selection(
        [
            ("dni", "DNI"),
            ("ce", "CE"),
            ("pasaporte", "Pasaporte"),
            ("otro", "Otro"),
        ],
        string="Tipo de documento",
    )
    numero_documento = fields.Char(string="Número de documento")
    nacionalidad = fields.Char(string="Nacionalidad")
    fecha_nacimiento = fields.Date(string="Fecha de nacimiento")
    email = fields.Char(string="Correo")
    telefono = fields.Char(string="Teléfono")
    documento_directory_id = fields.Many2one("dms.directory", string="Carpeta documental", readonly=True, copy=False)
    documento_file_count = fields.Integer(string="Cantidad de documentos", readonly=True, copy=False)
    documento_entregado = fields.Boolean(string="Documento entregado", readonly=True, copy=False)
    fecha_entrega_documento = fields.Date(string="Fecha de entrega documental")
    estado_documental = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("parcial", "Parcial"),
            ("completo", "Completo"),
        ],
        string="Estado documental",
        compute="_compute_estado_documental",
        store=True,
    )
    faltantes_documentales = fields.Char(string="Faltantes documentales", compute="_compute_estado_documental", store=True)
    observaciones = fields.Text(string="Observaciones")

    @api.depends("nombres", "apellidos")
    def _compute_name(self):
        for record in self:
            record.name = " ".join(part for part in [record.nombres, record.apellidos] if part)

    @api.depends("tipo_documento", "numero_documento", "documento_entregado")
    def _compute_estado_documental(self):
        for record in self:
            faltantes = []
            if not record.tipo_documento:
                faltantes.append("tipo de documento")
            if not record.numero_documento:
                faltantes.append("número de documento")
            if not record.documento_entregado:
                faltantes.append("archivo documental")
            record.faltantes_documentales = ", ".join(faltantes)
            if not faltantes:
                record.estado_documental = "completo"
            elif len(faltantes) == 3:
                record.estado_documental = "pendiente"
            else:
                record.estado_documental = "parcial"

    def _actualizar_resumen_documental(self):
        file_model = self.env["dms.file"].sudo()
        for record in self:
            if record.documento_directory_id:
                cantidad = file_model.search_count([("directory_id", "child_of", record.documento_directory_id.id)])
            else:
                cantidad = 0
            valores = {
                "documento_file_count": cantidad,
                "documento_entregado": bool(cantidad),
                "fecha_entrega_documento": fields.Date.context_today(record) if cantidad else False,
            }
            super(IncasPasajero, record.sudo()).write(valores)

    def _asegurar_carpeta_documental(self):
        directory_model = self.env["dms.directory"].sudo()
        for record in self:
            if not record.reserva_id:
                continue
            record.reserva_id._asegurar_carpeta_documental()
            nombre_carpeta = record.reserva_id._nombre_directorio_seguro(record.name, f"PASAJERO-{record.id}")
            parent_directory = record.reserva_id.documento_directory_id
            directory = record.documento_directory_id
            if directory:
                valores = {}
                if directory.parent_id != parent_directory:
                    valores["parent_id"] = parent_directory.id
                if directory.name != nombre_carpeta:
                    valores["name"] = nombre_carpeta
                if valores:
                    directory.write(valores)
                continue
            existente = directory_model.search(
                [("parent_id", "=", parent_directory.id), ("name", "=", nombre_carpeta)],
                limit=1,
            )
            if not existente:
                existente = directory_model.create(
                    {
                        "name": nombre_carpeta,
                        "parent_id": parent_directory.id,
                        "is_root_directory": False,
                    }
                )
            record.documento_directory_id = existente.id

    @api.model_create_multi
    def create(self, vals_list):
        pasajeros = super().create(vals_list)
        pasajeros._asegurar_carpeta_documental()
        pasajeros._actualizar_resumen_documental()
        return pasajeros

    def write(self, vals):
        result = super().write(vals)
        if any(campo in vals for campo in ["nombres", "apellidos", "reserva_id"]):
            self._asegurar_carpeta_documental()
        if any(campo in vals for campo in ["documento_directory_id"]):
            self._actualizar_resumen_documental()
        return result

    def action_ver_documentos(self):
        self.ensure_one()
        self._asegurar_carpeta_documental()
        if not self.documento_directory_id:
            raise UserError("No existe un directorio raíz en Documentos. Crea uno en el módulo Documentos primero.")
        return self.documento_directory_id.action_dms_files_all_directory()
