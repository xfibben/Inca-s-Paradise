from odoo import api, fields, models


class IncasTour(models.Model):
    _name = "incas.tour"
    _description = "Tour"
    _order = "nombre, id"
    _inherit = ["incas.dms.asset.mixin"]

    nombre = fields.Char(string="Nombre", required=True)
    nombre_en = fields.Char(string="Nombre en inglés")
    nombre_pt = fields.Char(string="Nombre en portugués")
    slug = fields.Char(string="Slug", required=True, index=True)
    slug_en = fields.Char(string="Slug en inglés", index=True)
    slug_pt = fields.Char(string="Slug en portugués", index=True)
    meta_titulo = fields.Html(string="Meta título")
    meta_titulo_en = fields.Html(string="Meta título en inglés")
    meta_titulo_pt = fields.Html(string="Meta título en portugués")
    meta_descripcion = fields.Html(string="Meta descripción")
    meta_descripcion_en = fields.Html(string="Meta descripción en inglés")
    meta_descripcion_pt = fields.Html(string="Meta descripción en portugués")
    destacados_titulo = fields.Html(string="Título destacados")
    destacados_titulo_en = fields.Html(string="Título destacados en inglés")
    destacados_titulo_pt = fields.Html(string="Título destacados en portugués")
    destacados_lead = fields.Html(string="Lead destacados")
    destacados_lead_en = fields.Html(string="Lead destacados en inglés")
    destacados_lead_pt = fields.Html(string="Lead destacados en portugués")
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
    imagen = fields.Image(
        string="Imagen",
        compute="_compute_imagen",
        inverse="_inverse_imagen",
        store=False,
    )
    imagen_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)
    estilo_ids = fields.Many2many(
        "incas.estilo.tour",
        "incas_tour_estilo_rel",
        "tour_id",
        "estilo_id",
        string="Estilos",
    )
    destino_ids = fields.Many2many(
        "incas.catalogo.destino",
        "incas_tour_destino_rel",
        "tour_id",
        "destino_id",
        string="Destinos",
    )
    destacado_item_ids = fields.One2many(
        "incas.tour.destacado",
        "tour_id",
        string="Highlights items",
    )
    itinerario_item_ids = fields.One2many(
        "incas.tour.itinerario",
        "tour_id",
        string="Itinerary items",
    )
    incluye_item_ids = fields.One2many(
        "incas.tour.incluido",
        "tour_id",
        string="Included",
    )
    no_incluye_item_ids = fields.One2many(
        "incas.tour.no.incluido",
        "tour_id",
        string="Not included",
    )
    horario_ids = fields.One2many(
        "incas.tour.horario",
        "tour_id",
        string="Horarios",
    )
    imagen_destacada_ids = fields.One2many(
        "incas.tour.imagen.destacada",
        "tour_id",
        string="Featured images",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("incas_tour_slug_unique", "unique(slug)", "El slug del tour ya existe."),
        ("incas_tour_slug_en_unique", "unique(slug_en)", "El slug en inglés del tour ya existe."),
        ("incas_tour_slug_pt_unique", "unique(slug_pt)", "El slug en portugués del tour ya existe."),
    ]

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
        for vals in vals_list:
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
        records._copiar_imagenes_destacadas_desde_itinerario(si_vacio=True)
        return records

    def write(self, vals):
        valores = dict(vals)
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
        if any(campo in valores for campo in ("nombre", "slug", "documento_directory_id")):
            self._asegurar_carpeta_documental()
        self._copiar_imagenes_destacadas_desde_itinerario(si_vacio=True)
        return result

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

    def _copiar_imagenes_destacadas_desde_itinerario(self, si_vacio=False):
        for record in self:
            if si_vacio and record.imagen_destacada_ids:
                continue
            imagenes = record.itinerario_item_ids.mapped("imagen_ids").sorted(lambda item: (item.sequence, item.id))
            if not imagenes:
                continue
            record.imagen_destacada_ids.unlink()
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
