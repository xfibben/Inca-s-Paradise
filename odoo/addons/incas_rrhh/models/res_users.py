from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    rol_rrhh = fields.Char(string="Rol", compute="_compute_rol_rrhh")
    puesto = fields.Char(string="Puesto")
    area = fields.Char(string="Área")
    tipo_documento = fields.Selection(
        [("dni", "DNI"), ("ce", "Carnet de extranjería"), ("pasaporte", "Pasaporte"), ("otro", "Otro")],
        string="Tipo de documento",
        default="dni",
    )
    numero_documento = fields.Char(string="Número de documento")
    fecha_ingreso = fields.Date(string="Fecha de ingreso")
    fecha_cese = fields.Date(string="Fecha de cese")
    estado_laboral = fields.Selection(
        [("activo", "Activo"), ("cesado", "Cesado"), ("suspendido", "Suspendido")],
        string="Estado laboral",
        required=True,
        default="activo",
    )
    horas_semanales = fields.Float(string="Horas semanales", default=48.0)
    correo_personal = fields.Char(string="Correo personal")
    correo_corporativo = fields.Char(string="Correo corporativo")
    telefono = fields.Char(string="Teléfono")
    direccion = fields.Char(string="Dirección")
    nacionalidad = fields.Char(string="Nacionalidad")
    fecha_nacimiento = fields.Date(string="Fecha de nacimiento")
    banco = fields.Char(string="Banco")
    moneda_pago = fields.Selection(
        [("PEN", "PEN"), ("USD", "USD")],
        string="Moneda de pago",
        required=True,
        default="PEN",
    )
    numero_cuenta = fields.Char(string="Número de cuenta")
    cci = fields.Char(string="CCI")
    titular_cuenta = fields.Char(string="Titular de cuenta")
    tipo_contrato = fields.Selection(
        [
            ("indefinido", "Indefinido"),
            ("plazo_fijo", "Plazo fijo"),
            ("practicante", "Practicante"),
            ("servicios", "Servicios"),
            ("otro", "Otro"),
        ],
        string="Tipo de contrato",
        default="indefinido",
    )
    fecha_inicio_contrato = fields.Date(string="Inicio de contrato")
    fecha_fin_contrato = fields.Date(string="Fin de contrato")
    modalidad_trabajo = fields.Selection(
        [("presencial", "Presencial"), ("remoto", "Remoto"), ("hibrido", "Híbrido")],
        string="Modalidad de trabajo",
        default="presencial",
    )
    horario_trabajo = fields.Char(string="Horario de trabajo")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Moneda", store=True)
    sueldo_base = fields.Monetary(string="Sueldo base", currency_field="currency_id")
    frecuencia_pago = fields.Selection(
        [("mensual", "Mensual"), ("quincenal", "Quincenal"), ("semanal", "Semanal")],
        string="Frecuencia de pago",
        required=True,
        default="mensual",
    )
    observaciones_rrhh = fields.Text(string="Observaciones")
    boleta_ids = fields.One2many("incas.boleta", "trabajador_id", string="Boletas")
    certificado_ids = fields.One2many("incas.certificado.laboral", "trabajador_id", string="Certificados")

    @api.depends("group_ids")
    def _compute_rol_rrhh(self):
        grupo_admin = self.env.ref("incas_core.group_incas_core_admin", raise_if_not_found=False)
        grupo_gerencia = self.env.ref("incas_core.group_incas_core_gerencia", raise_if_not_found=False)
        grupo_operaciones = self.env.ref("incas_core.group_incas_core_operaciones", raise_if_not_found=False)
        grupo_reservas = self.env.ref("incas_core.group_incas_core_reservas", raise_if_not_found=False)

        for record in self:
            rol = "Usuario interno"
            if grupo_admin and grupo_admin in record.group_ids:
                rol = "Administrador BO"
            elif grupo_gerencia and grupo_gerencia in record.group_ids:
                rol = "Gerencia"
            elif grupo_operaciones and grupo_operaciones in record.group_ids:
                rol = "Operaciones"
            elif grupo_reservas and grupo_reservas in record.group_ids:
                rol = "Reservas"
            record.rol_rrhh = rol
