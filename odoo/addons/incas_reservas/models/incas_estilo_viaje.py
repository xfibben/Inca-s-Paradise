from odoo import api, fields, models


class IncasEstiloViaje(models.Model):
    _name = "incas.estilo.viaje"
    _description = "Estilo de viaje"
    _order = "display_order, name, id"
    _inherit = ["incas.dms.asset.mixin"]

    name = fields.Char(string="Nombre", required=True)
    name_en = fields.Char(string="Nombre en ingles")
    name_pt = fields.Char(string="Nombre en portugues")
    slug = fields.Char(string="Slug", required=True, index=True)
    slug_en = fields.Char(string="Slug en ingles", index=True)
    slug_pt = fields.Char(string="Slug en portugues", index=True)
    description = fields.Html(string="Descripcion")
    description_en = fields.Html(string="Descripcion en ingles")
    description_pt = fields.Html(string="Descripcion en portugues")
    middle_title = fields.Html(string="Titulo medio")
    middle_title_en = fields.Html(string="Titulo medio en ingles")
    middle_title_pt = fields.Html(string="Titulo medio en portugues")
    middle_description = fields.Html(string="Descripcion media")
    middle_description_en = fields.Html(string="Descripcion media en ingles")
    middle_description_pt = fields.Html(string="Descripcion media en portugues")
    image = fields.Image(
        string="Imagen",
        compute="_compute_image",
        inverse="_inverse_image",
        store=False,
    )
    image_file_id = fields.Many2one("dms.file", string="Archivo imagen", readonly=True, copy=False)
    seo_title = fields.Char(string="Titulo SEO")
    seo_title_en = fields.Char(string="Titulo SEO en ingles")
    seo_title_pt = fields.Char(string="Titulo SEO en portugues")
    seo_description = fields.Text(string="Descripcion SEO")
    seo_description_en = fields.Text(string="Descripcion SEO en ingles")
    seo_description_pt = fields.Text(string="Descripcion SEO en portugues")
    display_order = fields.Integer(string="Orden de visualizacion", default=100)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("incas_estilo_viaje_slug_unique", "unique(slug)", "El slug del estilo ya existe."),
        ("incas_estilo_viaje_slug_en_unique", "unique(slug_en)", "El slug en ingles del estilo ya existe."),
        ("incas_estilo_viaje_slug_pt_unique", "unique(slug_pt)", "El slug en portugues del estilo ya existe."),
    ]

    def _dms_storage_name(self):
        return "Tours"

    def _dms_root_directory_name(self):
        return "Estilos de viaje"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._asegurar_carpeta_documental()
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(campo in vals for campo in ("name", "documento_directory_id")):
            self._asegurar_carpeta_documental()
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

    def _autocompletar_traducciones_en_vals(self, vals):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("slug", "slug_en", "slug_pt"),
            ("description", "description_en", "description_pt"),
            ("middle_title", "middle_title_en", "middle_title_pt"),
            ("middle_description", "middle_description_en", "middle_description_pt"),
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
            ("slug", "slug_en", "slug_pt"),
            ("description", "description_en", "description_pt"),
            ("middle_title", "middle_title_en", "middle_title_pt"),
            ("middle_description", "middle_description_en", "middle_description_pt"),
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

    @api.depends("image_file_id")
    def _compute_image(self):
        for record in self:
            record.image = record.image_file_id.content if record.image_file_id else False

    def _inverse_image(self):
        for record in self:
            if not record.image:
                if record.image_file_id:
                    record.image_file_id.unlink()
                    record.image_file_id = False
                continue
            archivo = record._guardar_archivo_dms(
                record.image,
                "estilo-viaje-imagen",
                archivo_actual=record.image_file_id,
            )
            record.image_file_id = archivo.id

    @api.onchange(
        "name",
        "slug",
        "description",
        "middle_title",
        "middle_description",
        "seo_title",
        "seo_description",
    )
    def _onchange_autocompletar_traducciones(self):
        equivalencias = (
            ("name", "name_en", "name_pt"),
            ("slug", "slug_en", "slug_pt"),
            ("description", "description_en", "description_pt"),
            ("middle_title", "middle_title_en", "middle_title_pt"),
            ("middle_description", "middle_description_en", "middle_description_pt"),
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
