import json

from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


class IncasTour(models.Model):
    _name = "incas.tour"
    _description = "Tour"
    _order = "nombre, id"
    _rec_name = "nombre"
    _inherit = ["incas.dms.asset.mixin"]

    nombre = fields.Char(string="Nombre", required=True)
    nombre_en = fields.Char(string="Nombre en ingles")
    nombre_pt = fields.Char(string="Nombre en portugues")
    servicio_id = fields.Many2one(
        "incas.servicio.catalogo",
        string="Servicio catalogo",
        readonly=True,
        copy=False,
    )
    tipo_tour = fields.Selection(
        [
            ("tour", "Tour"),
            ("small_trip", "Small Trip"),
            ("package", "Package"),
        ],
        string="Tipo de tour",
        required=True,
        default="tour",
    )
    precio_adulto = fields.Float(string="Precio adulto USD")
    precio_nino = fields.Float(string="Precio niño USD")
    descuento = fields.Float(string="Descuento")
    dias = fields.Integer(string="Dias", default=1)
    comentario = fields.Text(string="Comentario")
    observacion = fields.Selection(
        [
            ("corregir", "Corregir"),
            ("arreglar_imagenes", "Arreglar imágenes"),
            ("perfecto", "Perfecto"),
        ],
        string="Observación",
        default="corregir",
    )
    ultimo_editor_id = fields.Many2one(
        "res.users",
        string="Último editor",
        related="write_uid",
        readonly=True,
        store=False,
    )
    ip = fields.Selection(
        [
            ("ip3", "IP 3"),
            ("ip2", "IP 2"),
        ],
        string="IP",
        required=True,
        default="ip3",
    )
    slug = fields.Char(string="Slug", required=True, index=True)
    slug_en = fields.Char(string="Slug en ingles", index=True)
    slug_pt = fields.Char(string="Slug en portugues", index=True)
    meta_titulo = fields.Char(string="Meta titulo")
    meta_titulo_en = fields.Char(string="Meta titulo en ingles")
    meta_titulo_pt = fields.Char(string="Meta titulo en portugues")
    meta_descripcion = fields.Text(string="Meta descripcion")
    meta_descripcion_en = fields.Text(string="Meta descripcion en ingles")
    meta_descripcion_pt = fields.Text(string="Meta descripcion en portugues")
    destacados_titulo = fields.Html(string="Titulo destacados")
    destacados_titulo_en = fields.Html(string="Titulo destacados en ingles")
    destacados_titulo_pt = fields.Html(string="Titulo destacados en portugues")
    destacados_lead = fields.Html(string="Lead destacados")
    destacados_lead_en = fields.Html(string="Lead destacados en ingles")
    destacados_lead_pt = fields.Html(string="Lead destacados en portugues")
    destacados_items_import_json = fields.Text(string="Importar destacados JSON")
    destacados_items_import_json_en = fields.Text(string="Importar destacados JSON en ingles")
    destacados_items_import_json_pt = fields.Text(string="Importar destacados JSON en portugues")
    itinerario_import_json = fields.Text(string="Importar itinerario JSON")
    itinerario_import_json_en = fields.Text(string="Importar itinerario JSON en ingles")
    itinerario_import_json_pt = fields.Text(string="Importar itinerario JSON en portugues")
    incluye_import_json = fields.Text(string="Importar incluidos JSON")
    incluye_import_json_en = fields.Text(string="Importar incluidos JSON en ingles")
    incluye_import_json_pt = fields.Text(string="Importar incluidos JSON en portugues")
    no_incluye_import_json = fields.Text(string="Importar no incluidos JSON")
    no_incluye_import_json_en = fields.Text(string="Importar no incluidos JSON en ingles")
    no_incluye_import_json_pt = fields.Text(string="Importar no incluidos JSON en portugues")
    imagen = fields.Image(
        string="Imagen",
        compute="_compute_imagen",
        inverse="_inverse_imagen",
        store=False,
    )
    imagen_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)
    estilo_ids = fields.Many2many(
        "incas.estilo.viaje",
        "incas_tour_estilo_rel",
        "tour_id",
        "estilo_id",
        string="Estilos de viaje",
    )
    destino_ids = fields.Many2many(
        "incas.catalogo.destino",
        "incas_tour_destino_rel",
        "tour_id",
        "destino_id",
        string="Destinos",
    )
    subcategoria_destino_id = fields.Many2one(
        "incas.subcategoria.destino",
        string="Subcategoría de destino",
        ondelete="set null",
    )
    destacado_item_ids = fields.One2many(
        "incas.tour.destacado",
        "tour_id",
        string="Items destacados",
    )
    itinerario_item_ids = fields.One2many(
        "incas.tour.itinerario",
        "tour_id",
        string="Items itinerario",
    )
    incluye_item_ids = fields.One2many(
        "incas.tour.incluido",
        "tour_id",
        string="Incluidos",
    )
    no_incluye_item_ids = fields.One2many(
        "incas.tour.no.incluido",
        "tour_id",
        string="No incluidos",
    )
    horario_ids = fields.One2many(
        "incas.tour.horario",
        "tour_id",
        string="Horarios",
    )
    imagen_destacada_ids = fields.One2many(
        "incas.tour.imagen.destacada",
        "tour_id",
        string="Imagenes destacadas",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("incas_tour_slug_unique", "unique(slug)", "El slug del tour ya existe."),
        ("incas_tour_slug_en_unique", "unique(slug_en)", "El slug en ingles del tour ya existe."),
        ("incas_tour_slug_pt_unique", "unique(slug_pt)", "El slug en portugues del tour ya existe."),
        ("incas_tour_servicio_unique", "unique(servicio_id)", "El tour ya esta vinculado a un servicio."),
    ]

    def _auto_init(self):
        self._migrar_columnas_meta_a_texto()
        res = super()._auto_init()
        self.env.cr.execute(
            """
            UPDATE incas_tour
               SET ip = 'ip3'
             WHERE ip IS NULL
            """
        )
        return res

    def _migrar_columnas_meta_a_texto(self):
        columnas = {
            "meta_titulo": "varchar",
            "meta_titulo_en": "varchar",
            "meta_titulo_pt": "varchar",
            "meta_descripcion": "text",
            "meta_descripcion_en": "text",
            "meta_descripcion_pt": "text",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_tour'
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
                    ALTER TABLE incas_tour
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
                    ALTER TABLE incas_tour
                    ALTER COLUMN {columna} TYPE varchar
                    """
                )
            self.env.cr.execute(
                f"""
                UPDATE incas_tour
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

    def _copiar_traduccion_si_vacia(self, vals, campo_base):
        campo_en = f"{campo_base}_en"
        campo_pt = f"{campo_base}_pt"
        if campo_base not in vals:
            return
        if not vals.get(campo_en):
            vals[campo_en] = vals[campo_base]
        if not vals.get(campo_pt):
            vals[campo_pt] = vals[campo_base]

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

    def _aplicar_itinerario_importado(self):
        itinerario_model = self.env["incas.tour.itinerario"]
        for record in self:
            items_por_orden = {}
            for sufijo, campo in (
                ("", "itinerario_import_json"),
                ("_en", "itinerario_import_json_en"),
                ("_pt", "itinerario_import_json_pt"),
            ):
                for indice, item in enumerate(record._cargar_json_importacion(record[campo]), start=1):
                    if not isinstance(item, dict):
                        continue
                    orden = int(item.get("orden") or indice)
                    valores = items_por_orden.setdefault(
                        orden,
                        {
                            "sequence": orden * 10,
                            "tour_id": record.id,
                            "titulo": False,
                            "titulo_en": False,
                            "titulo_pt": False,
                            "descripcion": False,
                            "descripcion_en": False,
                            "descripcion_pt": False,
                        },
                    )
                    valores[f"titulo{sufijo}"] = item.get("titulo") or False
                    valores[f"descripcion{sufijo}"] = item.get("descripcion") or False

            record.itinerario_item_ids.unlink()
            for orden in sorted(items_por_orden):
                itinerario_model.create(items_por_orden[orden])

    def _aplicar_destacados_importados(self):
        destacado_model = self.env["incas.tour.destacado"]
        for record in self:
            items_por_orden = {}
            for sufijo, campo in (
                ("", "destacados_items_import_json"),
                ("_en", "destacados_items_import_json_en"),
                ("_pt", "destacados_items_import_json_pt"),
            ):
                for indice, item in enumerate(record._cargar_json_importacion(record[campo]), start=1):
                    if not isinstance(item, dict):
                        continue
                    orden = int(item.get("orden") or indice)
                    valores = items_por_orden.setdefault(
                        orden,
                        {
                            "sequence": orden * 10,
                            "tour_id": record.id,
                            "titulo": False,
                            "titulo_en": False,
                            "titulo_pt": False,
                            "contenido": False,
                            "contenido_en": False,
                            "contenido_pt": False,
                        },
                    )
                    valores[f"titulo{sufijo}"] = item.get("titulo") or False
                    valores[f"contenido{sufijo}"] = item.get("contenido") or item.get("descripcion") or False

            record.destacado_item_ids.unlink()
            for orden in sorted(items_por_orden):
                destacado_model.create(items_por_orden[orden])

    def _aplicar_lista_importada(self, campo_es, campo_en, campo_pt, modelo):
        item_model = self.env[modelo]
        for record in self:
            items_por_orden = {}
            for sufijo, campo in (
                ("", campo_es),
                ("_en", campo_en),
                ("_pt", campo_pt),
            ):
                for indice, item in enumerate(record._cargar_json_importacion(record[campo]), start=1):
                    if not isinstance(item, dict):
                        continue
                    orden = int(item.get("orden") or indice)
                    valores = items_por_orden.setdefault(
                        orden,
                        {
                            "sequence": orden * 10,
                            "tour_id": record.id,
                            "titulo": False,
                            "titulo_en": False,
                            "titulo_pt": False,
                        },
                    )
                    valores[f"titulo{sufijo}"] = item.get("texto") or item.get("titulo") or False

            if modelo == "incas.tour.incluido":
                record.incluye_item_ids.unlink()
            else:
                record.no_incluye_item_ids.unlink()
            for orden in sorted(items_por_orden):
                item_model.create(items_por_orden[orden])

    def _sanitizar_campos_meta_en_vals(self, vals):
        for campo in (
            "meta_titulo",
            "meta_titulo_en",
            "meta_titulo_pt",
            "meta_descripcion",
            "meta_descripcion_en",
            "meta_descripcion_pt",
        ):
            if campo in vals:
                vals[campo] = self._limpiar_texto_seo(vals[campo])

    def _dms_storage_name(self):
        return "Tours"

    def _dms_root_directory_name(self):
        return "Tours"

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
                "imagen-tour",
                archivo_actual=record.imagen_file_id,
            )
            record.imagen_file_id = archivo.id

    @api.onchange(
        "nombre",
        "slug",
        "meta_titulo",
        "meta_descripcion",
        "destacados_titulo",
        "destacados_lead",
    )
    def _onchange_copiar_campos_es(self):
        for record in self:
            if record.subcategoria_destino_id and record.destino_ids and record.subcategoria_destino_id.destino_id not in record.destino_ids:
                record.subcategoria_destino_id = False
            for campo in (
                "meta_titulo",
                "meta_titulo_en",
                "meta_titulo_pt",
                "meta_descripcion",
                "meta_descripcion_en",
                "meta_descripcion_pt",
            ):
                record[campo] = record._limpiar_texto_seo(record[campo])
            for campo in (
                "nombre",
                "slug",
                "meta_titulo",
                "meta_descripcion",
                "destacados_titulo",
                "destacados_lead",
            ):
                valor = record[campo]
                campo_en = f"{campo}_en"
                campo_pt = f"{campo}_pt"
                if valor and not record[campo_en]:
                    record[campo_en] = valor
                if valor and not record[campo_pt]:
                    record[campo_pt] = valor

    @api.constrains("subcategoria_destino_id", "destino_ids")
    def _check_subcategoria_destino(self):
        for record in self:
            if record.subcategoria_destino_id and record.subcategoria_destino_id.destino_id not in record.destino_ids:
                raise ValidationError("La subcategoría de destino debe pertenecer a uno de los destinos del tour.")

    def _copiar_imagenes_destacadas_desde_itinerario(self, si_vacio=False):
        for record in self:
            if si_vacio and record.imagen_destacada_ids:
                continue
            imagenes = record.itinerario_item_ids.mapped("imagen_ids").sorted(lambda item: (item.sequence, item.id))
            record.imagen_destacada_ids.unlink()
            if not imagenes:
                continue
            valores = []
            for indice, imagen in enumerate(imagenes, start=1):
                if not imagen.imagen:
                    continue
                valores.append(
                    {
                        "tour_id": record.id,
                        "sequence": indice * 10,
                        "imagen": imagen.imagen,
                    }
                )
            if valores:
                self.env["incas.tour.imagen.destacada"].create(valores)

    def action_copiar_imagenes_destacadas(self):
        self._copiar_imagenes_destacadas_desde_itinerario(si_vacio=False)
        return True

    def _json_dump(self, value):
        if not value:
            return False
        return json.dumps(value, ensure_ascii=False, indent=2)

    def name_get(self):
        return [(record.id, record.nombre or f"Tour {record.id}") for record in self]

    def _serializar_destinos(self):
        self.ensure_one()
        return [
            {
                "id": destino.id,
                "slug": destino.slug,
                "nombre": destino.nombre,
            }
            for destino in self.destino_ids.sorted(lambda item: (item.orden_visual, item.nombre or "", item.id))
        ]

    def _serializar_estilos(self):
        self.ensure_one()
        return [
            {
                "id": estilo.id,
                "slug": estilo.slug,
                "name": estilo.name,
                "description": estilo.description,
            }
            for estilo in self.estilo_ids.sorted(lambda item: (item.display_order, item.name or "", item.id))
        ]

    def _serializar_destacados(self):
        self.ensure_one()
        return [
            {
                "title": item.titulo,
                "description": item.contenido,
            }
            for item in self.destacado_item_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if item.titulo or item.contenido
        ]

    def _serializar_itinerarios(self):
        self.ensure_one()
        valores = []
        for item in self.itinerario_item_ids.sorted(lambda rec: (rec.sequence, rec.id)):
            imagenes = [{"url": imagen.imagen} for imagen in item.imagen_ids.sorted(lambda rec: (rec.sequence, rec.id)) if imagen.imagen]
            valores.append(
                {
                    "title": item.titulo,
                    "description": item.descripcion,
                    "image": imagenes[0] if imagenes else False,
                    "includes": [],
                }
            )
        return valores

    def _serializar_horarios(self):
        self.ensure_one()
        return [
            {
                "title": "",
                "horaEntrada": horario.horario_inicial or "",
                "horaSalida": horario.horario_final or "",
            }
            for horario in self.horario_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if horario.horario_inicial or horario.horario_final
        ]

    def _serializar_items_lista(self, items):
        return [
            {"text": item.titulo}
            for item in items.sorted(lambda rec: (rec.sequence, rec.id))
            if item.titulo
        ]

    def _serializar_imagenes_destacadas(self):
        self.ensure_one()
        return [
            {"url": imagen.imagen}
            for imagen in self.imagen_destacada_ids.sorted(lambda rec: (rec.sequence, rec.id))
            if imagen.imagen
        ]

    def _valores_snapshot_operativo(self):
        self.ensure_one()
        destinos = self._serializar_destinos()
        return {
            "destino_slug": destinos[0]["slug"] if destinos else False,
            "destinos_data": self._json_dump(destinos),
            "estilos_data": self._json_dump(self._serializar_estilos()),
            "duration_days": 0,
            "hero_title": False,
            "hero_description": False,
            "hero_slide_images_data": False,
            "highlights_title": self.destacados_titulo,
            "highlights_question": False,
            "highlights_lead": self.destacados_lead,
            "highlights_items_data": self._json_dump(self._serializar_destacados()),
            "featured_images_data": self._json_dump(self._serializar_imagenes_destacadas()),
            "itinerary_title": False,
            "itinerary_items_data": self._json_dump(self._serializar_itinerarios()),
            "schedule_title": False,
            "schedule_items_data": self._json_dump(self._serializar_horarios()),
            "included_title": False,
            "included_items_data": self._json_dump(self._serializar_items_lista(self.incluye_item_ids)),
            "excluded_title": False,
            "excluded_items_data": self._json_dump(self._serializar_items_lista(self.no_incluye_item_ids)),
            "faq_title": False,
            "faq_items_data": False,
        }

    def _preparar_valores_servicio_catalogo(self):
        self.ensure_one()
        return {
            "name": self.nombre,
            "tipo_servicio": "tour",
            "tipo_tour": self.tipo_tour,
            "estilo_transporte_id": False,
            "precio_adulto": self.precio_adulto or 0,
            "precio_nino": self.precio_nino or 0,
            "descuento": self.descuento or 0,
            "ip": self.ip or "ip3",
            "slug": self.slug,
            "active": self.active,
        }

    def _sincronizar_servicio_operativo(self):
        service_model = self.env["incas.servicio.catalogo"].sudo()
        horario_model = self.env["incas.horario.opcion"].sudo()
        for record in self:
            service_vals = record._preparar_valores_servicio_catalogo()
            servicio = record.servicio_id.sudo()
            if servicio:
                servicio.write(service_vals)
            else:
                servicio = service_model.create(service_vals)
                record.with_context(skip_catalog_sync=True).write({"servicio_id": servicio.id})
            horarios_existentes = horario_model.search([("servicio_id", "=", servicio.id)])
            vistos = self.env["incas.horario.opcion"]
            for indice, horario in enumerate(record.horario_ids.sorted(lambda rec: (rec.sequence, rec.id)), start=1):
                nombre = " - ".join(valor for valor in [horario.horario_inicial or "", horario.horario_final or ""] if valor)
                if not nombre:
                    continue
                valores = {
                    "name": nombre,
                    "sequence": indice * 10,
                    "servicio_id": servicio.id,
                }
                horario_existente = horarios_existentes.filtered(lambda item: item.name == nombre)[:1]
                if horario_existente:
                    horario_existente.write(valores)
                    vistos |= horario_existente
                else:
                    vistos |= horario_model.create(valores)
            (horarios_existentes - vistos).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_meta_a_texto()
        for vals in vals_list:
            self._sanitizar_campos_meta_en_vals(vals)
            for campo in (
                "nombre",
                "slug",
                "meta_titulo",
                "meta_descripcion",
                "destacados_titulo",
                "destacados_lead",
            ):
                self._copiar_traduccion_si_vacia(vals, campo)
        records = super().create(vals_list)
        records._asegurar_carpeta_documental()
        for record, vals in zip(records, vals_list):
            if any(campo in vals for campo in ("destacados_items_import_json", "destacados_items_import_json_en", "destacados_items_import_json_pt")):
                record._aplicar_destacados_importados()
            if any(campo in vals for campo in ("itinerario_import_json", "itinerario_import_json_en", "itinerario_import_json_pt")):
                record._aplicar_itinerario_importado()
            if any(campo in vals for campo in ("incluye_import_json", "incluye_import_json_en", "incluye_import_json_pt")):
                record._aplicar_lista_importada(
                    "incluye_import_json",
                    "incluye_import_json_en",
                    "incluye_import_json_pt",
                    "incas.tour.incluido",
                )
            if any(campo in vals for campo in ("no_incluye_import_json", "no_incluye_import_json_en", "no_incluye_import_json_pt")):
                record._aplicar_lista_importada(
                    "no_incluye_import_json",
                    "no_incluye_import_json_en",
                    "no_incluye_import_json_pt",
                    "incas.tour.no.incluido",
                )
        records._copiar_imagenes_destacadas_desde_itinerario(si_vacio=True)
        records._sincronizar_servicio_operativo()
        return records

    def write(self, vals):
        self._migrar_columnas_meta_a_texto()
        if self.env.context.get("skip_catalog_sync"):
            return super().write(vals)
        valores = dict(vals)
        self._sanitizar_campos_meta_en_vals(valores)
        for campo in (
            "nombre",
            "slug",
            "meta_titulo",
            "meta_descripcion",
            "destacados_titulo",
            "destacados_lead",
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
        if any(campo in valores for campo in ("destacados_items_import_json", "destacados_items_import_json_en", "destacados_items_import_json_pt")):
            self._aplicar_destacados_importados()
        if any(campo in valores for campo in ("itinerario_import_json", "itinerario_import_json_en", "itinerario_import_json_pt")):
            self._aplicar_itinerario_importado()
        if any(campo in valores for campo in ("incluye_import_json", "incluye_import_json_en", "incluye_import_json_pt")):
            self._aplicar_lista_importada(
                "incluye_import_json",
                "incluye_import_json_en",
                "incluye_import_json_pt",
                "incas.tour.incluido",
            )
        if any(campo in valores for campo in ("no_incluye_import_json", "no_incluye_import_json_en", "no_incluye_import_json_pt")):
            self._aplicar_lista_importada(
                "no_incluye_import_json",
                "no_incluye_import_json_en",
                "no_incluye_import_json_pt",
                "incas.tour.no.incluido",
            )
        if any(campo in valores for campo in ("nombre", "slug", "documento_directory_id")):
            self._asegurar_carpeta_documental()
        self._copiar_imagenes_destacadas_desde_itinerario(si_vacio=True)
        self._sincronizar_servicio_operativo()
        return result

    def unlink(self):
        return super().unlink()
