import calendar
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError


MESES = [
    ("01", "Enero"),
    ("02", "Febrero"),
    ("03", "Marzo"),
    ("04", "Abril"),
    ("05", "Mayo"),
    ("06", "Junio"),
    ("07", "Julio"),
    ("08", "Agosto"),
    ("09", "Septiembre"),
    ("10", "Octubre"),
    ("11", "Noviembre"),
    ("12", "Diciembre"),
]


class IncasEvaluacionDesempenoMensual(models.Model):
    _name = "incas.evaluacion.desempeno.mensual"
    _description = "Evaluación de desempeño mensual"
    _order = "anio desc, mes desc, id desc"
    _rec_name = "nombre"
    _sql_constraints = [
        ("incas_evaluacion_desempeno_mes_unique", "unique(anio, mes)", "Ya existe una evaluación para ese mes."),
    ]

    nombre = fields.Char(string="Nombre", compute="_compute_nombre", store=True)
    anio = fields.Integer(string="Año", required=True, default=lambda self: fields.Date.today().year)
    mes = fields.Selection(
        MESES,
        string="Mes",
        required=True,
        default=lambda self: fields.Date.today().strftime("%m"),
    )
    estado = fields.Selection(
        [("borrador", "Borrador"), ("cerrado", "Cerrado")],
        string="Estado",
        required=True,
        default="borrador",
    )
    semana_ids = fields.One2many(
        "incas.evaluacion.desempeno.semana",
        "evaluacion_mensual_id",
        string="Semanas",
        copy=False,
    )
    observaciones = fields.Text(string="Observaciones")
    calificacion_final_mes = fields.Float(
        string="Calificación final de mes",
        compute="_compute_calificacion_final_mes",
        store=True,
        digits=(16, 2),
    )
    tabla_resumen_html = fields.Html(
        string="Tabla mensual",
        compute="_compute_tabla_resumen_html",
        sanitize=False,
    )

    @api.depends("anio", "mes")
    def _compute_nombre(self):
        meses = dict(MESES)
        for record in self:
            record.nombre = f"{meses.get(record.mes, '')} {record.anio}".strip()

    @api.depends(
        "semana_ids.linea_ids.calificacion",
        "semana_ids.linea_ids.trabajador_id",
    )
    def _compute_calificacion_final_mes(self):
        for record in self:
            promedios_trabajadores = []
            for trabajador in record._get_trabajadores_tabla():
                calificaciones = []
                for semana in record.semana_ids:
                    linea = semana.linea_ids.filtered(lambda item: item.trabajador_id.id == trabajador.id)[:1]
                    if linea:
                        calificaciones.append(linea.calificacion)
                if calificaciones:
                    promedios_trabajadores.append(sum(calificaciones) / len(calificaciones))
            record.calificacion_final_mes = (
                sum(promedios_trabajadores) / len(promedios_trabajadores) if promedios_trabajadores else 0.0
            )

    @api.depends(
        "semana_ids.name",
        "semana_ids.fecha_inicio",
        "semana_ids.fecha_fin",
        "semana_ids.linea_ids.calificacion",
        "semana_ids.linea_ids.trabajador_id",
    )
    def _compute_tabla_resumen_html(self):
        for record in self:
            trabajadores = record._get_trabajadores_tabla()
            semanas = record.semana_ids.sorted(key=lambda item: item.numero_semana)
            encabezados = []
            for semana in semanas:
                rango = ""
                if semana.fecha_inicio and semana.fecha_fin:
                    rango = f"<br/><span style='font-weight:400'>({semana.fecha_inicio.strftime('%d/%m')} - {semana.fecha_fin.strftime('%d/%m')})</span>"
                encabezados.append(
                    "<th style='min-width:160px; white-space:nowrap; text-align:center; padding:12px 16px'>"
                    f"{semana.name}{rango}</th>"
                )
            filas = []
            for trabajador in trabajadores:
                celdas = []
                calificaciones_trabajador = []
                for semana in semanas:
                    linea = semana.linea_ids.filtered(lambda item: item.trabajador_id.id == trabajador.id)[:1]
                    if linea:
                        calificaciones_trabajador.append(linea.calificacion)
                    celdas.append(
                        "<td style='text-align:center; white-space:nowrap; padding:12px 16px'>"
                        f"{linea.calificacion if linea else '-'}</td>"
                    )
                promedio_trabajador = (
                    f"{(sum(calificaciones_trabajador) / len(calificaciones_trabajador)):.2f}"
                    if calificaciones_trabajador
                    else "-"
                )
                filas.append(
                    "<tr>"
                    "<td style='min-width:220px; white-space:nowrap; padding:12px 16px'>"
                    f"<strong>{trabajador.name}</strong></td>"
                    f"{''.join(celdas)}"
                    "<td style='text-align:center; white-space:nowrap; padding:12px 16px; font-weight:600'>"
                    f"{promedio_trabajador}</td></tr>"
                )
            if not filas:
                filas.append("<tr><td colspan='99'>Sin semanas generadas</td></tr>")
            record.tabla_resumen_html = (
                "<div style='width:100%; overflow-x:auto; overflow-y:hidden'>"
                "<table class='table table-sm table-bordered' "
                "style='width:max-content; min-width:100%; table-layout:auto; margin:0'>"
                "<thead><tr>"
                "<th style='min-width:220px; white-space:nowrap; padding:12px 16px'>Trabajador</th>"
                f"{''.join(encabezados)}"
                "<th style='min-width:180px; white-space:nowrap; text-align:center; padding:12px 16px'>Calificación mensual</th>"
                "</tr></thead>"
                f"<tbody>{''.join(filas)}</tbody>"
                "</table>"
                "</div>"
            )

    @api.constrains("anio")
    def _check_anio(self):
        for record in self:
            if record.anio < 2020 or record.anio > 2100:
                raise ValidationError("El año debe estar entre 2020 y 2100.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._generar_estructura_mes()
        return records

    def write(self, vals):
        regenerar = "anio" in vals or "mes" in vals
        result = super().write(vals)
        if regenerar:
            self._generar_estructura_mes()
        return result

    def action_regenerar_tabla(self):
        self._generar_estructura_mes()

    def action_cerrar(self):
        self.write({"estado": "cerrado"})

    def action_borrador(self):
        self.write({"estado": "borrador"})

    def _get_trabajadores_activos(self):
        return self.env["res.users"].search(
            [("share", "=", False), ("active", "=", True), ("estado_laboral", "=", "activo")],
            order="name asc",
        )

    def _get_trabajadores_tabla(self):
        self.ensure_one()
        trabajadores = self.semana_ids.mapped("linea_ids.trabajador_id").sorted(key=lambda item: item.name or "")
        return trabajadores or self._get_trabajadores_activos()

    def _get_rangos_semanales(self):
        self.ensure_one()
        ultimo_dia = calendar.monthrange(self.anio, int(self.mes))[1]
        inicio_mes = date(self.anio, int(self.mes), 1)
        fin_mes = date(self.anio, int(self.mes), ultimo_dia)
        rangos = []
        cursor = inicio_mes
        numero = 1
        while cursor <= fin_mes:
            semana_fin = min(date.fromordinal(cursor.toordinal() + 6), fin_mes)
            rangos.append(
                {
                    "numero_semana": numero,
                    "name": f"Semana {numero}",
                    "fecha_inicio": cursor,
                    "fecha_fin": semana_fin,
                }
            )
            numero += 1
            cursor = date.fromordinal(semana_fin.toordinal() + 1)
        return rangos

    def _generar_estructura_mes(self):
        trabajadores = self._get_trabajadores_activos()
        for record in self:
            lineas_existentes = {
                (semana.numero_semana, linea.trabajador_id.id): [
                    {
                        "name": detalle.name,
                        "nota": detalle.nota,
                    }
                    for detalle in linea.detalle_ids
                ]
                for semana in record.semana_ids
                for linea in semana.linea_ids
            }
            semanas_commands = [(5, 0, 0)]
            for semana_vals in record._get_rangos_semanales():
                lineas_commands = []
                for trabajador in trabajadores:
                    detalle_commands = [
                        (0, 0, detalle_vals)
                        for detalle_vals in lineas_existentes.get((semana_vals["numero_semana"], trabajador.id), [])
                    ]
                    lineas_commands.append(
                        (
                            0,
                            0,
                            {
                                "trabajador_id": trabajador.id,
                                "detalle_ids": detalle_commands,
                            },
                        )
                    )
                semanas_commands.append((0, 0, {**semana_vals, "linea_ids": lineas_commands}))
            record.semana_ids = semanas_commands


class IncasEvaluacionDesempenoSemana(models.Model):
    _name = "incas.evaluacion.desempeno.semana"
    _description = "Semana de evaluación de desempeño"
    _order = "evaluacion_mensual_id desc, numero_semana asc, id asc"

    evaluacion_mensual_id = fields.Many2one(
        "incas.evaluacion.desempeno.mensual",
        string="Evaluación mensual",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Semana", required=True)
    numero_semana = fields.Integer(string="Nro semana", required=True)
    fecha_inicio = fields.Date(string="Inicio", required=True)
    fecha_fin = fields.Date(string="Fin", required=True)
    linea_ids = fields.One2many(
        "incas.evaluacion.desempeno.linea",
        "semana_id",
        string="Calificaciones",
        copy=False,
    )


class IncasEvaluacionDesempenoLinea(models.Model):
    _name = "incas.evaluacion.desempeno.linea"
    _description = "Línea de evaluación semanal"
    _order = "trabajador_id asc, id asc"
    _sql_constraints = [
        (
            "incas_evaluacion_desempeno_linea_unique",
            "unique(semana_id, trabajador_id)",
            "Cada trabajador solo puede tener una calificación por semana.",
        )
    ]

    semana_id = fields.Many2one(
        "incas.evaluacion.desempeno.semana",
        string="Semana",
        required=True,
        ondelete="cascade",
    )
    trabajador_id = fields.Many2one("res.users", string="Trabajador", required=True, ondelete="cascade")
    detalle_ids = fields.One2many(
        "incas.evaluacion.desempeno.criterio",
        "linea_id",
        string="Detalle de calificaciones",
        copy=False,
    )
    calificacion = fields.Float(
        string="Calificación",
        compute="_compute_calificacion",
        store=True,
        digits=(16, 2),
    )

    @api.depends("detalle_ids.nota")
    def _compute_calificacion(self):
        for record in self:
            notas = record.detalle_ids.mapped("nota")
            record.calificacion = sum(notas) / len(notas) if notas else 0.0

    @api.constrains("calificacion")
    def _check_calificacion(self):
        for record in self:
            if record.calificacion < 0 or record.calificacion > 5:
                raise ValidationError("La calificación debe estar entre 0 y 5.")


class IncasEvaluacionDesempenoCriterio(models.Model):
    _name = "incas.evaluacion.desempeno.criterio"
    _description = "Criterio de evaluación semanal"
    _order = "id asc"

    linea_id = fields.Many2one(
        "incas.evaluacion.desempeno.linea",
        string="Línea",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Nombre", required=True)
    nota = fields.Float(string="Nota", required=True, digits=(16, 2), default=0.0)

    @api.constrains("nota")
    def _check_nota(self):
        for record in self:
            if record.nota < 0 or record.nota > 5:
                raise ValidationError("La nota debe estar entre 0 y 5.")
