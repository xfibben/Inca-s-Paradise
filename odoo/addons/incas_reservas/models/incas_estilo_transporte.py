from odoo import api, fields, models, tools


class IncasEstiloTransporte(models.Model):
    _name = "incas.estilo.transporte"
    _description = "Estilo de transporte"
    _order = "nro_orden, name"
    _inherit = ["incas.dms.asset.mixin"]

    name = fields.Char(string="Nombre", required=True)
    name_en = fields.Char(string="Nombre en inglés")
    name_pt = fields.Char(string="Nombre en portugués")
    slug = fields.Char(string="Slug")
    descripcion = fields.Html(string="Descripción")
    descripcion_en = fields.Html(string="Descripción en inglés")
    descripcion_pt = fields.Html(string="Descripción en portugués")
    image_data = fields.Image(
        string="Imagen",
        compute="_compute_image_data",
        inverse="_inverse_image_data",
        store=False,
    )
    wallpaper_data = fields.Image(
        string="Imagen de fondo",
        compute="_compute_wallpaper_data",
        inverse="_inverse_wallpaper_data",
        store=False,
    )
    image_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)
    wallpaper_file_id = fields.Many2one("dms.file", string="Archivo imagen de fondo", readonly=True, copy=False)
    seo_title = fields.Char(string="Título SEO")
    seo_title_en = fields.Char(string="Título SEO en inglés")
    seo_title_pt = fields.Char(string="Título SEO en portugués")
    seo_description = fields.Text(string="Descripción SEO")
    seo_description_en = fields.Text(string="Descripción SEO en inglés")
    seo_description_pt = fields.Text(string="Descripción SEO en portugués")
    transporte_ids = fields.Many2many(
        "incas.catalogo.transporte",
        "incas_catalogo_transporte_estilo_rel",
        "estilo_id",
        "transporte_id",
        string="Transportes relacionados",
    )
    nro_orden = fields.Integer(string="Nro. orden", default=0)
    active = fields.Boolean(default=True)

    def _auto_init(self):
        self._migrar_columnas_legadas_jsonb()
        return super()._auto_init()

    def _migrar_columnas_legadas_jsonb(self):
        columnas = {
            "name": "varchar",
            "descripcion": "text",
            "seo_title": "varchar",
            "seo_description": "text",
            "name_en": "varchar",
            "descripcion_en": "text",
            "seo_title_en": "varchar",
            "seo_description_en": "text",
            "name_pt": "varchar",
            "descripcion_pt": "text",
            "seo_title_pt": "varchar",
            "seo_description_pt": "text",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_estilo_transporte'
                  AND column_name = %s
                """,
                [columna],
            )
            fila = self.env.cr.fetchone()
            if not fila or fila[0] != "jsonb":
                continue
            self.env.cr.execute(
                f"""
                ALTER TABLE incas_estilo_transporte
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
            for campo in (
                "name",
                "descripcion",
                "seo_title",
                "seo_description",
                "name_en",
                "descripcion_en",
                "seo_title_en",
                "seo_description_en",
                "name_pt",
                "descripcion_pt",
                "seo_title_pt",
                "seo_description_pt",
            ):
                if campo in fila:
                    fila[campo] = self._normalizar_valor_legacy(fila[campo])
        return filas

    def _limpiar_texto_seo(self, valor):
        if not isinstance(valor, str):
            return valor
        valor_limpio = tools.html2plaintext(valor).replace("\xa0", " ")
        valor_limpio = " ".join(valor_limpio.split())
        return valor_limpio or False

    def _sanitizar_campos_seo_en_vals(self, vals):
        for campo in (
            "seo_title",
            "seo_title_en",
            "seo_title_pt",
            "seo_description",
            "seo_description_en",
            "seo_description_pt",
        ):
            if campo in vals:
                vals[campo] = self._limpiar_texto_seo(vals[campo])

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_legadas_jsonb()
        for vals in vals_list:
            self._sanitizar_campos_seo_en_vals(vals)
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._asegurar_carpeta_documental()
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        self._migrar_columnas_legadas_jsonb()
        valores = dict(vals)
        self._sanitizar_campos_seo_en_vals(valores)
        result = super().write(valores)
        if any(campo in valores for campo in ["name", "documento_directory_id"]):
            self._asegurar_carpeta_documental()
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

    def _dms_storage_name(self):
        return "Transportes"

    def _dms_root_directory_name(self):
        return "Tipos de transporte"

    @api.depends("image_file_id")
    def _compute_image_data(self):
        for record in self:
            record.image_data = record.image_file_id.content if record.image_file_id else False

    def _inverse_image_data(self):
        for record in self:
            if not record.image_data:
                if record.image_file_id:
                    record.image_file_id.unlink()
                    record.image_file_id = False
                continue
            archivo = record._guardar_archivo_dms(
                record.image_data,
                "tipo-transporte-imagen",
                archivo_actual=record.image_file_id,
            )
            record.image_file_id = archivo.id

    @api.depends("wallpaper_file_id")
    def _compute_wallpaper_data(self):
        for record in self:
            record.wallpaper_data = record.wallpaper_file_id.content if record.wallpaper_file_id else False

    def _inverse_wallpaper_data(self):
        for record in self:
            if not record.wallpaper_data:
                if record.wallpaper_file_id:
                    record.wallpaper_file_id.unlink()
                    record.wallpaper_file_id = False
                continue
            archivo = record._guardar_archivo_dms(
                record.wallpaper_data,
                "tipo-transporte-fondo",
                archivo_actual=record.wallpaper_file_id,
            )
            record.wallpaper_file_id = archivo.id

    def read(self, fields=None, load="_classic_read"):
        self._migrar_columnas_legadas_jsonb()
        filas = super().read(fields=fields, load=load)
        return self._normalizar_filas_legacy(filas)

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        self._migrar_columnas_legadas_jsonb()
        filas = super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return self._normalizar_filas_legacy(filas)

    def _autocompletar_traducciones_en_vals(self, vals):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("seo_title", "seo_title_en", "seo_title_pt"),
            ("seo_description", "seo_description_en", "seo_description_pt"),
        )
        for base, campo_en, campo_pt in equivalencias:
            valor_base = vals.get(base)
            if not valor_base:
                continue
            if not vals.get(campo_en):
                vals[campo_en] = valor_base
            if not vals.get(campo_pt):
                vals[campo_pt] = valor_base

    def _completar_traducciones_vacias(self):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("seo_title", "seo_title_en", "seo_title_pt"),
            ("seo_description", "seo_description_en", "seo_description_pt"),
        )
        for record in self:
            valores = {}
            for base, campo_en, campo_pt in equivalencias:
                valor_base = record[base]
                if not valor_base:
                    continue
                if not record[campo_en]:
                    valores[campo_en] = valor_base
                if not record[campo_pt]:
                    valores[campo_pt] = valor_base
            if valores:
                record.with_context(skip_autocompletar_traducciones=True).write(valores)

    @api.onchange("name", "descripcion", "seo_title", "seo_description")
    def _onchange_autocompletar_traducciones(self):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("seo_title", "seo_title_en", "seo_title_pt"),
            ("seo_description", "seo_description_en", "seo_description_pt"),
        )
        for record in self:
            for campo in (
                "seo_title",
                "seo_title_en",
                "seo_title_pt",
                "seo_description",
                "seo_description_en",
                "seo_description_pt",
            ):
                record[campo] = record._limpiar_texto_seo(record[campo])
            for base, campo_en, campo_pt in equivalencias:
                valor_base = record[base]
                if not valor_base:
                    continue
                if not record[campo_en]:
                    record[campo_en] = valor_base
                if not record[campo_pt]:
                    record[campo_pt] = valor_base
