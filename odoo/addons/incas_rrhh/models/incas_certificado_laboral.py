import base64
import mimetypes
from pathlib import Path

from odoo import api, fields, models


class IncasCertificadoLaboral(models.Model):
    _name = "incas.certificado.laboral"
    _description = "Certificado laboral"
    _order = "fecha_emision desc, id desc"

    numero = fields.Char(string="Número", required=True, copy=False, default="Nuevo")
    trabajador_id = fields.Many2one("res.users", string="Trabajador", required=True, ondelete="cascade")
    company_id = fields.Many2one(related="trabajador_id.company_id", string="Compañía", store=True)
    fecha_emision = fields.Date(string="Fecha de emisión", required=True, default=fields.Date.context_today)
    tipo = fields.Selection(
        [("trabajo", "Trabajo"), ("ingresos", "Ingresos"), ("practicas", "Prácticas")],
        string="Tipo",
        required=True,
        default="trabajo",
    )
    dirigido_a = fields.Char(string="Dirigido a")
    contenido_base = fields.Text(string="Contenido base")
    fecha_ingreso_snapshot = fields.Date(string="Fecha de ingreso")
    fecha_cese_snapshot = fields.Date(string="Fecha de cese")
    puesto_snapshot = fields.Char(string="Puesto")
    horas_semanales_snapshot = fields.Float(string="Horas semanales")
    sueldo_snapshot = fields.Monetary(string="Sueldo de referencia", currency_field="currency_id")
    currency_id = fields.Many2one(related="trabajador_id.currency_id", string="Moneda", store=True)
    firmante_id = fields.Many2one("res.users", string="Firmante", required=True, default=lambda self: self.env.user)
    estado = fields.Selection(
        [("borrador", "Borrador"), ("emitido", "Emitido"), ("anulado", "Anulado")],
        string="Estado",
        required=True,
        default="borrador",
    )
    observaciones = fields.Text(string="Observaciones")

    def _get_certificado_imagen_data_uri(self):
        self.ensure_one()
        report_dir = Path(__file__).resolve().parent.parent / "reports"
        candidate_names = (
            "certificado_imagen.png",
            "certificado_imagen.jpg",
            "certificado_imagen.jpeg",
            "certificado_imagen.webp",
        )

        # La imagen se toma manualmente desde la carpeta del reporte.
        for filename in candidate_names:
            image_path = report_dir / filename
            if image_path.is_file():
                mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
                encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
                return f"data:{mime_type};base64,{encoded}"
        return False

    @api.onchange("trabajador_id")
    def _onchange_trabajador_id(self):
        for record in self:
            record._cargar_snapshot_trabajador()

    def _cargar_snapshot_trabajador(self):
        for record in self:
            trabajador = record.trabajador_id
            if not trabajador:
                continue
            record.fecha_ingreso_snapshot = trabajador.fecha_ingreso
            record.fecha_cese_snapshot = trabajador.fecha_cese
            record.puesto_snapshot = trabajador.puesto
            record.horas_semanales_snapshot = trabajador.horas_semanales
            record.sueldo_snapshot = trabajador.sueldo_base

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("numero", "Nuevo") == "Nuevo":
                vals["numero"] = sequence.next_by_code("incas.certificado.laboral") or "Nuevo"
            trabajador_id = vals.get("trabajador_id")
            if trabajador_id:
                trabajador = self.env["res.users"].browse(trabajador_id)
                vals.setdefault("fecha_ingreso_snapshot", trabajador.fecha_ingreso)
                vals.setdefault("fecha_cese_snapshot", trabajador.fecha_cese)
                vals.setdefault("puesto_snapshot", trabajador.puesto)
                vals.setdefault("horas_semanales_snapshot", trabajador.horas_semanales)
                vals.setdefault("sueldo_snapshot", trabajador.sueldo_base)
        return super().create(vals_list)

    def action_emitir(self):
        self.write({"estado": "emitido"})

    def action_borrador(self):
        self.write({"estado": "borrador"})

    def action_anular(self):
        self.write({"estado": "anulado"})

    def action_imprimir_certificado(self):
        self.ensure_one()
        return self.env.ref("incas_rrhh.action_report_incas_certificado_laboral").report_action(self)
