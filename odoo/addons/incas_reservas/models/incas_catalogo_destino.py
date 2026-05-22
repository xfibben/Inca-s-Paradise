import json

from odoo import api, fields, models, tools


class IncasCatalogoDestino(models.Model):
    _name = "incas.catalogo.destino"
    _description = "Catálogo local de destinos"
    _order = "orden_visual, nombre, id"
    _rec_name = "nombre"

    nombre = fields.Char(string="Nombre", required=True)
    nombre_en = fields.Char(string="Nombre en inglés")
    nombre_pt = fields.Char(string="Nombre en portugués")
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
    iconos_import_json = fields.Text(string="Importar iconos JSON")
    iconos_import_json_en = fields.Text(string="Importar iconos JSON en inglés")
    iconos_import_json_pt = fields.Text(string="Importar iconos JSON en portugués")
    imagen = fields.Image(string="Imagen")
    imagen_fondo = fields.Image(string="Imagen de fondo")
    tour_ids = fields.Many2many(
        "incas.tour",
        "incas_tour_destino_rel",
        "destino_id",
        "tour_id",
        string="Tours",
    )
    subcategoria_destino_ids = fields.One2many(
        "incas.subcategoria.destino",
        "destino_id",
        string="Subcategorías de destino",
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
        self._migrar_relacion_tours_legada()
        self._migrar_columnas_seo_a_texto()
        return super()._auto_init()

    def _migrar_relacion_tours_legada(self):
        self.env.cr.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'incas_catalogo_destino_web_tour_rel'
            )
            """
        )
        fila = self.env.cr.fetchone()
        if not fila or not fila[0]:
            return
        self.env.cr.execute(
            """
            INSERT INTO incas_tour_destino_rel (tour_id, destino_id)
            SELECT rel.tour_id, rel.destino_id
            FROM incas_catalogo_destino_web_tour_rel rel
            WHERE NOT EXISTS (
                SELECT 1
                FROM incas_tour_destino_rel actual
                WHERE actual.tour_id = rel.tour_id
                  AND actual.destino_id = rel.destino_id
            )
            """
        )

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

    def _cargar_json_importacion(self, valor):
        if not valor:
            return []
        if isinstance(valor, list):
            return valor
        try:
            data = json.loads(valor)
            return data if isinstance(data, list) else []
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    def _aplicar_iconos_importados(self):
        icono_model = self.env["incas.catalogo.destino.icono"]
        for record in self:
            items_por_orden = {}
            for sufijo, campo in (
                ("", "iconos_import_json"),
                ("_en", "iconos_import_json_en"),
                ("_pt", "iconos_import_json_pt"),
            ):
                for indice, item in enumerate(record._cargar_json_importacion(record[campo]), start=1):
                    if not isinstance(item, dict):
                        continue
                    orden = int(item.get("orden") or indice)
                    valores = items_por_orden.setdefault(
                        orden,
                        {
                            "sequence": orden * 10,
                            "destino_id": record.id,
                            "titulo": False,
                            "titulo_en": False,
                            "titulo_pt": False,
                        },
                    )
                    valores[f"titulo{sufijo}"] = item.get("titulo") or item.get("texto") or False

            record.icono_item_ids.unlink()
            for orden in sorted(items_por_orden):
                icono_model.create(items_por_orden[orden])

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
                "nombre",
                "slug",
                "descripcion",
                "titulo_intro",
                "contenido_intro",
                "cinta_principal",
                "seo_titulo",
                "seo_descripcion",
            ):
                self._copiar_traduccion_si_vacia(vals, campo)
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if any(campo in vals for campo in ("iconos_import_json", "iconos_import_json_en", "iconos_import_json_pt")):
                record._aplicar_iconos_importados()
        return records

    def write(self, vals):
        self._migrar_columnas_seo_a_texto()
        valores = dict(vals)
        self._sanitizar_campos_seo_en_vals(valores)
        for campo in (
            "nombre",
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
        result = super().write(valores)
        if any(campo in valores for campo in ("iconos_import_json", "iconos_import_json_en", "iconos_import_json_pt")):
            self._aplicar_iconos_importados()
        return result

    @api.onchange(
        "nombre",
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
                "nombre",
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
