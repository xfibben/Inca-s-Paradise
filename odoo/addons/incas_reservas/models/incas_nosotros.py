from odoo import api, fields, models, tools


class IncasNosotros(models.Model):
    _name = "incas.nosotros"
    _description = "Nosotros"
    _order = "id desc"
    _rec_name = "titulo"

    titulo = fields.Char(string="Titulo", required=True)
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    descripcion = fields.Html(string="Descripcion")
    descripcion_en = fields.Html(string="Descripcion en ingles")
    descripcion_pt = fields.Html(string="Descripcion en portugues")
    meta_titulo = fields.Char(string="Meta titulo")
    meta_titulo_en = fields.Char(string="Meta titulo en ingles")
    meta_titulo_pt = fields.Char(string="Meta titulo en portugues")
    meta_descripcion = fields.Text(string="Meta descripcion")
    meta_descripcion_en = fields.Text(string="Meta descripcion en ingles")
    meta_descripcion_pt = fields.Text(string="Meta descripcion en portugues")
    seccion_ids = fields.One2many(
        "incas.nosotros.seccion",
        "nosotros_id",
        string="Secciones",
    )
    active = fields.Boolean(string="Activo", default=True)

    def _limpiar_texto_seo(self, valor):
        if not isinstance(valor, str):
            return valor
        valor_limpio = tools.html2plaintext(valor).replace("\xa0", " ")
        valor_limpio = " ".join(valor_limpio.split())
        return valor_limpio or False

    def _sanitizar_campos_seo_en_vals(self, vals):
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

    def _autocompletar_traducciones_en_vals(self, vals):
        equivalencias = (
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("meta_titulo", "meta_titulo_en", "meta_titulo_pt"),
            ("meta_descripcion", "meta_descripcion_en", "meta_descripcion_pt"),
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
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("meta_titulo", "meta_titulo_en", "meta_titulo_pt"),
            ("meta_descripcion", "meta_descripcion_en", "meta_descripcion_pt"),
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitizar_campos_seo_en_vals(vals)
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        valores = dict(vals)
        self._sanitizar_campos_seo_en_vals(valores)
        result = super().write(valores)
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result

    @api.onchange("titulo", "descripcion", "meta_titulo", "meta_descripcion")
    def _onchange_autocompletar_traducciones(self):
        for record in self:
            for campo in (
                "meta_titulo",
                "meta_titulo_en",
                "meta_titulo_pt",
                "meta_descripcion",
                "meta_descripcion_en",
                "meta_descripcion_pt",
            ):
                record[campo] = record._limpiar_texto_seo(record[campo])
            if record.titulo and not record.titulo_en:
                record.titulo_en = record.titulo
            if record.titulo and not record.titulo_pt:
                record.titulo_pt = record.titulo
            if record.descripcion and not record.descripcion_en:
                record.descripcion_en = record.descripcion
            if record.descripcion and not record.descripcion_pt:
                record.descripcion_pt = record.descripcion
            if record.meta_titulo and not record.meta_titulo_en:
                record.meta_titulo_en = record.meta_titulo
            if record.meta_titulo and not record.meta_titulo_pt:
                record.meta_titulo_pt = record.meta_titulo
            if record.meta_descripcion and not record.meta_descripcion_en:
                record.meta_descripcion_en = record.meta_descripcion
            if record.meta_descripcion and not record.meta_descripcion_pt:
                record.meta_descripcion_pt = record.meta_descripcion


class IncasNosotrosSeccion(models.Model):
    _name = "incas.nosotros.seccion"
    _description = "Seccion de nosotros"
    _order = "sequence, id"
    _rec_name = "titulo"

    sequence = fields.Integer(string="Orden", default=10)
    nosotros_id = fields.Many2one(
        "incas.nosotros",
        string="Nosotros",
        required=True,
        ondelete="cascade",
    )
    titulo = fields.Char(string="Titulo")
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    texto_html = fields.Html(string="Contenido")
    texto_html_en = fields.Html(string="Contenido en ingles")
    texto_html_pt = fields.Html(string="Contenido en portugues")
    imagen = fields.Image(string="Imagen")

    def _autocompletar_traducciones_en_vals(self, vals):
        equivalencias = (
            ("titulo", "titulo_en", "titulo_pt"),
            ("texto_html", "texto_html_en", "texto_html_pt"),
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
        for record in self:
            valores = {}
            for base, campo_en, campo_pt in (
                ("titulo", "titulo_en", "titulo_pt"),
                ("texto_html", "texto_html_en", "texto_html_pt"),
            ):
                valor_base = record[base]
                if not valor_base:
                    continue
                if not record[campo_en]:
                    valores[campo_en] = valor_base
                if not record[campo_pt]:
                    valores[campo_pt] = valor_base
            if valores:
                record.with_context(skip_autocompletar_traducciones=True).write(valores)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
        records = super().create(vals_list)
        records._completar_traducciones_vacias()
        return records

    def write(self, vals):
        valores = dict(vals)
        result = super().write(valores)
        if not self.env.context.get("skip_autocompletar_traducciones"):
            self._completar_traducciones_vacias()
        return result
