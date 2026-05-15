import json

from odoo import api, fields, models


class IncasCatalogoTransporte(models.Model):
    _name = "incas.catalogo.transporte"
    _description = "Catálogo local de transportes"
    _inherits = {"incas.servicio.catalogo": "servicio_id"}
    _order = "name"

    servicio_id = fields.Many2one("incas.servicio.catalogo", string="Servicio base", required=True, ondelete="cascade")
    name_en = fields.Char(string="Nombre en inglés")
    name_pt = fields.Char(string="Nombre en portugués")
    image_data = fields.Image(string="Imagen")
    wallpaper_data = fields.Image(string="Imagen de fondo")
    destino_origen_data = fields.Text(string="Destino origen")
    destino_origen_data_en = fields.Text(string="Destino origen en inglés")
    destino_origen_data_pt = fields.Text(string="Destino origen en portugués")
    destino_llegada_data = fields.Text(string="Destino llegada")
    destino_llegada_data_en = fields.Text(string="Destino llegada en inglés")
    destino_llegada_data_pt = fields.Text(string="Destino llegada en portugués")
    modelo_vehiculo = fields.Char(string="Modelo de vehículo")
    estilo_transporte_ids = fields.Many2many(
        "incas.estilo.transporte",
        "incas_catalogo_transporte_estilo_rel",
        "transporte_id",
        "estilo_id",
        string="Tipos de transporte",
    )
    tarifa_ids = fields.One2many(
        "incas.catalogo.transporte.tarifa",
        "transporte_id",
        string="Tarifas por vehículo",
    )
    duracion_viaje = fields.Char(string="Duración del viaje")
    distancia = fields.Char(string="Distancia")
    descripcion_origen = fields.Html(string="Descripción origen")
    descripcion_llegada = fields.Html(string="Descripción llegada")
    descripcion = fields.Html(string="Descripción")
    descripcion_en = fields.Html(string="Descripción en inglés")
    descripcion_pt = fields.Html(string="Descripción en portugués")
    incluye_ids = fields.One2many(
        "incas.catalogo.transporte.incluye",
        "transporte_id",
        string="Incluye",
    )
    included_items_data = fields.Text(string="Items de incluye", compute="_compute_listas_legacy", store=True)
    no_incluye_ids = fields.One2many(
        "incas.catalogo.transporte.no.incluye",
        "transporte_id",
        string="No incluye",
    )
    excluded_items_data = fields.Text(string="Items de no incluye", compute="_compute_listas_legacy", store=True)
    tipos_transporte_data = fields.Text(
        string="Tipos de transporte",
        compute="_compute_legacy_transport_data",
        store=True,
    )
    seo_title = fields.Char(string="Título SEO")
    seo_title_en = fields.Char(string="Título SEO en inglés")
    seo_title_pt = fields.Char(string="Título SEO en portugués")
    seo_description = fields.Text(string="Descripción SEO")
    seo_description_en = fields.Text(string="Descripción SEO en inglés")
    seo_description_pt = fields.Text(string="Descripción SEO en portugués")
    precios_data = fields.Text(
        string="Precios por vehículo",
        compute="_compute_legacy_transport_data",
        store=True,
    )

    _sql_constraints = [
        ("incas_catalogo_transporte_servicio_unique", "unique(servicio_id)", "El transporte ya está vinculado a un servicio."),
    ]

    def _auto_init(self):
        self._migrar_columnas_legadas_jsonb()
        return super()._auto_init()

    def _migrar_columnas_legadas_jsonb(self):
        columnas = {
            "descripcion": "text",
            "descripcion_en": "text",
            "descripcion_pt": "text",
            "destino_origen_data": "text",
            "destino_origen_data_en": "text",
            "destino_origen_data_pt": "text",
            "destino_llegada_data": "text",
            "destino_llegada_data_en": "text",
            "destino_llegada_data_pt": "text",
            "seo_title": "varchar",
            "seo_title_en": "varchar",
            "seo_title_pt": "varchar",
            "seo_description": "text",
            "seo_description_en": "text",
            "seo_description_pt": "text",
            "name_en": "varchar",
            "name_pt": "varchar",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_catalogo_transporte'
                  AND column_name = %s
                """,
                [columna],
            )
            fila = self.env.cr.fetchone()
            if not fila or fila[0] != "jsonb":
                continue
            self.env.cr.execute(
                f"""
                ALTER TABLE incas_catalogo_transporte
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
                "name_en",
                "name_pt",
                "descripcion",
                "descripcion_en",
                "descripcion_pt",
                "destino_origen_data",
                "destino_origen_data_en",
                "destino_origen_data_pt",
                "destino_llegada_data",
                "destino_llegada_data_en",
                "destino_llegada_data_pt",
                "seo_title",
                "seo_title_en",
                "seo_title_pt",
                "seo_description",
                "seo_description_en",
                "seo_description_pt",
            ):
                if campo in fila:
                    fila[campo] = self._normalizar_valor_legacy(fila[campo])
        return filas

    @api.depends(
        "estilo_transporte_ids.name",
        "estilo_transporte_ids.slug",
        "estilo_transporte_ids.descripcion",
        "tarifa_ids.sequence",
        "tarifa_ids.vehiculo_id.nombre",
        "tarifa_ids.vehiculo_id.descripcion",
        "tarifa_ids.vehiculo_id.imagen",
        "tarifa_ids.vehiculo_id.caracteristica_ids.titulo",
        "tarifa_ids.vehiculo_id.caracteristica_ids.descripcion",
        "tarifa_ids.precio_adulto_usd",
        "tarifa_ids.precio_nino_usd",
        "tarifa_ids.descuento",
    )
    def _compute_legacy_transport_data(self):
        for record in self:
            tipos = []
            for estilo in record.estilo_transporte_ids.sorted(lambda item: (item.nro_orden, item.name or "")):
                tipos.append(
                    {
                        "nombre": estilo.name,
                        "slug": estilo.slug,
                        "descripcion": estilo.descripcion,
                    }
                )
            precios = []
            for tarifa in record.tarifa_ids.sorted(lambda item: (item.sequence, item.id)):
                precios.append(
                    {
                        "precioAdulto": tarifa.precio_adulto_usd or 0,
                        "precioNino": tarifa.precio_nino_usd or 0,
                        "descuento": tarifa.descuento or 0,
                        "vehiculo": [
                            {
                                "nombre": tarifa.vehiculo_id.nombre,
                                "descripcion": tarifa.vehiculo_id.descripcion,
                                "imagen": self._json_lista(tarifa.vehiculo_id.imagen),
                                "features": [
                                    {
                                        "title": caracteristica.titulo,
                                        "description": caracteristica.descripcion,
                                    }
                                    for caracteristica in tarifa.vehiculo_id.caracteristica_ids.sorted(
                                        lambda item: (item.sequence, item.id)
                                    )
                                ],
                            }
                        ],
                    }
                )
            record.tipos_transporte_data = json.dumps(tipos, ensure_ascii=False, indent=2) if tipos else False
            record.precios_data = json.dumps(precios, ensure_ascii=False, indent=2) if precios else False

    @api.depends(
        "incluye_ids.sequence",
        "incluye_ids.texto",
        "incluye_ids.texto_en",
        "incluye_ids.texto_pt",
        "no_incluye_ids.sequence",
        "no_incluye_ids.texto",
        "no_incluye_ids.texto_en",
        "no_incluye_ids.texto_pt",
    )
    def _compute_listas_legacy(self):
        for record in self:
            incluye = []
            for item in record.incluye_ids.sorted(lambda x: (x.sequence, x.id)):
                incluye.append(
                    {
                        "texto": item.texto,
                        "texto_en": item.texto_en,
                        "texto_pt": item.texto_pt,
                    }
                )
            no_incluye = []
            for item in record.no_incluye_ids.sorted(lambda x: (x.sequence, x.id)):
                no_incluye.append(
                    {
                        "texto": item.texto,
                        "texto_en": item.texto_en,
                        "texto_pt": item.texto_pt,
                    }
                )
            record.included_items_data = json.dumps(incluye, ensure_ascii=False, indent=2) if incluye else False
            record.excluded_items_data = json.dumps(no_incluye, ensure_ascii=False, indent=2) if no_incluye else False

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)

    def _json_lista(self, valor):
        if not valor:
            return []
        try:
            data = json.loads(valor)
            return data if isinstance(data, list) else [data]
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_legadas_jsonb()
        servicio_model = self.env["incas.servicio.catalogo"]
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
            if vals.get("servicio_id"):
                continue
            servicio_vals = {
                "tipo_servicio": "transporte",
                "name": vals.get("name"),
                "slug": vals.get("slug"),
                "active": vals.get("active", True),
            }
            servicio = servicio_model.create(servicio_vals)
            vals["servicio_id"] = servicio.id
        records = super().create(vals_list)
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        self._migrar_columnas_legadas_jsonb()
        result = super().write(vals)
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

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
            ("destino_origen_data", "destino_origen_data_en", "destino_origen_data_pt"),
            ("destino_llegada_data", "destino_llegada_data_en", "destino_llegada_data_pt"),
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
            ("destino_origen_data", "destino_origen_data_en", "destino_origen_data_pt"),
            ("destino_llegada_data", "destino_llegada_data_en", "destino_llegada_data_pt"),
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

    @api.onchange("name", "descripcion", "destino_origen_data", "destino_llegada_data", "seo_title", "seo_description")
    def _onchange_autocompletar_traducciones(self):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("destino_origen_data", "destino_origen_data_en", "destino_origen_data_pt"),
            ("destino_llegada_data", "destino_llegada_data_en", "destino_llegada_data_pt"),
            ("seo_title", "seo_title_en", "seo_title_pt"),
            ("seo_description", "seo_description_en", "seo_description_pt"),
        )
        for record in self:
            for base, campo_en, campo_pt in equivalencias:
                valor_base = record[base]
                if not valor_base:
                    continue
                if not record[campo_en]:
                    record[campo_en] = valor_base
                if not record[campo_pt]:
                    record[campo_pt] = valor_base
