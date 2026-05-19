from odoo import api, fields, models, tools


class IncasCatalogoDestino(models.Model):
    _name = "incas.catalogo.destino"
    _description = "Catálogo local de destinos"
    _order = "orden_visual, nombre, id"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre", required=True)
    orden_visual = fields.Integer(string="Orden visual", default=100)
    slug = fields.Char(string="Slug", required=True, index=True)
    slug_en = fields.Char(string="Slug en inglés", index=True)
    slug_pt = fields.Char(string="Slug en portugués", index=True)
    descripcion = fields.Html(string="Descripción")
    descripcion_en = fields.Html(string="Descripción en inglés")
    descripcion_pt = fields.Html(string="Descripción en portugués")
    seo_titulo = fields.Char(string="SEO título")
    seo_titulo_en = fields.Char(string="SEO título en inglés")
    seo_titulo_pt = fields.Char(string="SEO título en portugués")
    seo_descripcion = fields.Text(string="SEO descripción")
    seo_descripcion_en = fields.Text(string="SEO descripción en inglés")
    seo_descripcion_pt = fields.Text(string="SEO descripción en portugués")
    titulo_intro = fields.Html(string="Título intro")
    titulo_intro_en = fields.Html(string="Título intro en inglés")
    titulo_intro_pt = fields.Html(string="Título intro en portugués")
    contenido_intro = fields.Html(string="Contenido intro")
    contenido_intro_en = fields.Html(string="Contenido intro en inglés")
    contenido_intro_pt = fields.Html(string="Contenido intro en portugués")
    cinta_principal = fields.Html(string="Cinta principal")
    cinta_principal_en = fields.Html(string="Cinta principal en inglés")
    cinta_principal_pt = fields.Html(string="Cinta principal en portugués")
    cantidad_inicial_catalogo = fields.Integer(string="Cantidad inicial catálogo", default=6)
    imagen = fields.Image(string="Imagen")
    imagen_fondo = fields.Image(string="Imagen de fondo")
    tour_ids = fields.Many2many(
        "incas.tour",
        "incas_catalogo_destino_web_tour_rel",
        "destino_id",
        "tour_id",
        string="Tours",
    )
    subcategoria_tour_ids = fields.One2many(
        "incas.subcategoria.tour",
        "destino_id",
        string="Subcategorías de tour",
    )
    icono_item_ids = fields.One2many(
        "incas.catalogo.destino.icono",
        "destino_id",
        string="Iconos",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("incas_catalogo_destino_slug_unique", "unique(slug)", "El slug del destino ya existe."),
        ("incas_catalogo_destino_slug_en_unique", "unique(slug_en)", "El slug en inglés del destino ya existe."),
        ("incas_catalogo_destino_slug_pt_unique", "unique(slug_pt)", "El slug en portugués del destino ya existe."),
    ]

    def _auto_init(self):
        self._migrar_columnas_seo_a_texto()
        return super()._auto_init()

    def _migrar_columnas_seo_a_texto(self):
        columnas = {
            "seo_titulo": "varchar",
            "seo_titulo_en": "varchar",
            "seo_titulo_pt": "varchar",
            "seo_descripcion": "text",
            "seo_descripcion_en": "text",
            "seo_descripcion_pt": "text",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_catalogo_destino'
                  AND column_name = %s
                """,
                [columna],
            )
            fila = self.env.cr.fetchone()
            if not fila:
                continue
            tipo_actual = fila[0]
            if tipo_actual == "jsonb":
                self.env.cr.execute(
                    f"""
                    ALTER TABLE incas_catalogo_destino
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
                continue
            if tipo_destino == "varchar" and tipo_actual == "text":
                self.env.cr.execute(
                    f"""
                    ALTER TABLE incas_catalogo_destino
                    ALTER COLUMN {columna} TYPE varchar
                    """
                )
            self.env.cr.execute(
                f"""
                UPDATE incas_catalogo_destino
                   SET {columna} = NULLIF(
                       trim(
                           regexp_replace(
                               regexp_replace(COALESCE({columna}, ''), '<[^>]+>', ' ', 'g'),
                               '\\s+',
                               ' ',
                               'g'
                           )
                       ),
                       ''
                   )
                 WHERE {columna} IS NOT NULL
                """
            )

    def _limpiar_texto_seo(self, valor):
        if not isinstance(valor, str):
            return valor
        valor_limpio = tools.html2plaintext(valor).replace("\xa0", " ")
        valor_limpio = " ".join(valor_limpio.split())
        return valor_limpio or False

    def _sanitizar_campos_seo_en_vals(self, vals):
        for campo in (
            "seo_titulo",
            "seo_titulo_en",
            "seo_titulo_pt",
            "seo_descripcion",
            "seo_descripcion_en",
            "seo_descripcion_pt",
        ):
            if campo in vals:
                vals[campo] = self._limpiar_texto_seo(vals[campo])

    def _copiar_traduccion_si_vacia(self, vals, campo_base):
        campo_en = f"{campo_base}_en"
        campo_pt = f"{campo_base}_pt"
        if campo_base not in vals:
            return
        if not vals.get(campo_en):
            vals[campo_en] = vals[campo_base]
        if not vals.get(campo_pt):
            vals[campo_pt] = vals[campo_base]

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_seo_a_texto()
        for vals in vals_list:
            self._sanitizar_campos_seo_en_vals(vals)
            for campo in (
                "slug",
                "descripcion",
                "titulo_intro",
                "contenido_intro",
                "cinta_principal",
                "seo_titulo",
                "seo_descripcion",
            ):
                self._copiar_traduccion_si_vacia(vals, campo)
        return super().create(vals_list)

    def write(self, vals):
        self._migrar_columnas_seo_a_texto()
        valores = dict(vals)
        self._sanitizar_campos_seo_en_vals(valores)
        for campo in (
            "slug",
            "descripcion",
            "titulo_intro",
            "contenido_intro",
            "cinta_principal",
            "seo_titulo",
            "seo_descripcion",
        ):
            if campo not in valores:
                continue
            campo_en = f"{campo}_en"
            campo_pt = f"{campo}_pt"
            if campo_en not in valores and any(not record[campo_en] for record in self):
                valores[campo_en] = valores[campo]
            if campo_pt not in valores and any(not record[campo_pt] for record in self):
                valores[campo_pt] = valores[campo]
        return super().write(valores)

    @api.onchange(
        "slug",
        "descripcion",
        "titulo_intro",
        "contenido_intro",
        "cinta_principal",
        "seo_titulo",
        "seo_descripcion",
    )
    def _onchange_copiar_contenido_es(self):
        for record in self:
            for campo in (
                "seo_titulo",
                "seo_titulo_en",
                "seo_titulo_pt",
                "seo_descripcion",
                "seo_descripcion_en",
                "seo_descripcion_pt",
            ):
                record[campo] = record._limpiar_texto_seo(record[campo])
            for campo in (
                "slug",
                "descripcion",
                "titulo_intro",
                "contenido_intro",
                "cinta_principal",
                "seo_titulo",
                "seo_descripcion",
            ):
                valor = record[campo]
                campo_en = f"{campo}_en"
                campo_pt = f"{campo}_pt"
                if valor and not record[campo_en]:
                    record[campo_en] = valor
                if valor and not record[campo_pt]:
                    record[campo_pt] = valor
