import json

from odoo import api, fields, models


class IncasCatalogoVehiculo(models.Model):
    _name = "incas.catalogo.vehiculo"
    _description = "Catálogo local de vehículos"
    _order = "nombre"
    _rec_name = "nombre"
    _inherit = ["incas.dms.asset.mixin"]

    nombre = fields.Char(string="Nombre", required=True, default="Nuevo vehículo")
    descripcion = fields.Html(string="Descripción")
    nombre_en = fields.Char(string="Nombre en inglés")
    descripcion_en = fields.Html(string="Descripción en inglés")
    nombre_pt = fields.Char(string="Nombre en portugués")
    descripcion_pt = fields.Html(string="Descripción en portugués")
    imagen = fields.Image(
        string="Imagen",
        compute="_compute_imagen",
        inverse="_inverse_imagen",
        store=False,
    )
    imagen_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)
    numero_asientos = fields.Integer(string="Número de asientos")
    caracteristica_ids = fields.One2many(
        "incas.catalogo.vehiculo.caracteristica",
        "vehiculo_id",
        string="Características",
    )
    tarifa_transporte_ids = fields.One2many(
        "incas.catalogo.transporte.tarifa",
        "vehiculo_id",
        string="Tarifas de transporte",
    )
    active = fields.Boolean(string="Activo", default=True)

    def _auto_init(self):
        self._migrar_columnas_legadas_jsonb()
        return super()._auto_init()

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)

    def _migrar_columnas_legadas_jsonb(self):
        columnas = {
            "nombre": "varchar",
            "descripcion": "text",
            "nombre_en": "varchar",
            "descripcion_en": "text",
            "nombre_pt": "varchar",
            "descripcion_pt": "text",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_catalogo_vehiculo'
                  AND column_name = %s
                """,
                [columna],
            )
            fila = self.env.cr.fetchone()
            if not fila or fila[0] != "jsonb":
                continue
            self.env.cr.execute(
                f"""
                ALTER TABLE incas_catalogo_vehiculo
                ALTER COLUMN {columna} TYPE {tipo_destino}
                USING CASE
                    WHEN {columna} IS NULL THEN NULL
                    WHEN jsonb_typeof({columna}) = 'string' THEN trim(both '"' from {columna}::text)
                    ELSE COALESCE(
                        {columna}->>'es_PE',
                        {columna}->>'es',
                        {columna}->>'en_US',
                        {columna}->>'en',
                        {columna}->>'pt_BR',
                        {columna}->>'pt',
                        {columna}->>'fr_FR',
                        {columna}->>'fr',
                        {columna}->>'it_IT',
                        {columna}->>'it'
                    )
                END
                """
            )

    def _normalizar_valor_legacy(self, valor):
        if not isinstance(valor, dict):
            return valor
        for clave in ("es_PE", "es", "en_US", "en", "pt_BR", "pt", "fr_FR", "fr", "it_IT", "it"):
            if valor.get(clave):
                return valor[clave]
        return next(iter(valor.values()), False)

    def _normalizar_filas_legacy(self, filas):
        for fila in filas:
            for campo in ("nombre", "descripcion", "nombre_en", "descripcion_en", "nombre_pt", "descripcion_pt"):
                if campo in fila:
                    fila[campo] = self._normalizar_valor_legacy(fila[campo])
        return filas

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_legadas_jsonb()
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._asegurar_carpeta_documental()
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        self._migrar_columnas_legadas_jsonb()
        result = super().write(vals)
        if any(campo in vals for campo in ["nombre", "documento_directory_id"]):
            self._asegurar_carpeta_documental()
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

    def _dms_storage_name(self):
        return "Transportes"

    def _dms_root_directory_name(self):
        return "Vehículos"

    @api.depends("imagen_file_id")
    def _compute_imagen(self):
        for record in self:
            record.imagen = record.imagen_file_id.content if record.imagen_file_id else False

    def _inverse_imagen(self):
        for record in self:
            if not record.imagen:
                if record.imagen_file_id:
                    record.imagen_file_id.unlink()
                    record.imagen_file_id = False
                continue
            archivo = record._guardar_archivo_dms(
                record.imagen,
                "vehiculo-imagen",
                archivo_actual=record.imagen_file_id,
            )
            record.imagen_file_id = archivo.id

    def read(self, fields=None, load="_classic_read"):
        self._migrar_columnas_legadas_jsonb()
        filas = super().read(fields=fields, load=load)
        return self._normalizar_filas_legacy(filas)

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        self._migrar_columnas_legadas_jsonb()
        filas = super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return self._normalizar_filas_legacy(filas)

    def _autocompletar_traducciones_en_vals(self, vals):
        nombre_base = vals.get("nombre")
        descripcion_base = vals.get("descripcion")
        if nombre_base:
            for campo in ("nombre_en", "nombre_pt"):
                if not vals.get(campo):
                    vals[campo] = nombre_base
        if descripcion_base:
            for campo in ("descripcion_en", "descripcion_pt"):
                if not vals.get(campo):
                    vals[campo] = descripcion_base

    def _completar_traducciones_vacias(self):
        for record in self:
            valores = {}
            if record.nombre:
                for campo in ("nombre_en", "nombre_pt"):
                    if not record[campo]:
                        valores[campo] = record.nombre
            if record.descripcion:
                for campo in ("descripcion_en", "descripcion_pt"):
                    if not record[campo]:
                        valores[campo] = record.descripcion
            if valores:
                record.with_context(skip_autocompletar_traducciones=True).write(valores)

    @api.onchange("nombre", "descripcion")
    def _onchange_autocompletar_traducciones(self):
        for record in self:
            if record.nombre:
                for campo in ("nombre_en", "nombre_pt"):
                    if not record[campo]:
                        record[campo] = record.nombre
            if record.descripcion:
                for campo in ("descripcion_en", "descripcion_pt"):
                    if not record[campo]:
                        record[campo] = record.descripcion
