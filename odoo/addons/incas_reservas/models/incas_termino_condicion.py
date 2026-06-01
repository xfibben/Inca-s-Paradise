from odoo import api, fields, models, tools


class IncasTerminoCondicion(models.Model):
    _name = "incas.termino.condicion"
    _description = "Terminos y condiciones"
    _order = "id desc"
    _rec_name = "titulo"

    titulo = fields.Char(string="Titulo", required=True)
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    slug = fields.Char(string="Slug", required=True, default="terminos", index=True)
    descripcion = fields.Html(string="Descripcion")
    descripcion_en = fields.Html(string="Descripcion en ingles")
    descripcion_pt = fields.Html(string="Descripcion en portugues")
    seo_titulo = fields.Char(string="SEO titulo")
    seo_titulo_en = fields.Char(string="SEO titulo en ingles")
    seo_titulo_pt = fields.Char(string="SEO titulo en portugues")
    seo_descripcion = fields.Text(string="SEO descripcion")
    seo_descripcion_en = fields.Text(string="SEO descripcion en ingles")
    seo_descripcion_pt = fields.Text(string="SEO descripcion en portugues")
    seccion_ids = fields.One2many(
        "incas.termino.condicion.seccion",
        "termino_id",
        string="Secciones",
    )
    active = fields.Boolean(string="Activo", default=True)

    _sql_constraints = [
        ("incas_termino_condicion_slug_unique", "unique(slug)", "El slug ya existe."),
    ]

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

    def _autocompletar_traducciones_en_vals(self, vals):
        equivalencias = (
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("seo_titulo", "seo_titulo_en", "seo_titulo_pt"),
            ("seo_descripcion", "seo_descripcion_en", "seo_descripcion_pt"),
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
            ("seo_titulo", "seo_titulo_en", "seo_titulo_pt"),
            ("seo_descripcion", "seo_descripcion_en", "seo_descripcion_pt"),
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

    @api.onchange("titulo", "descripcion", "seo_titulo", "seo_descripcion")
    def _onchange_autocompletar_traducciones(self):
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
            if record.titulo and not record.titulo_en:
                record.titulo_en = record.titulo
            if record.titulo and not record.titulo_pt:
                record.titulo_pt = record.titulo
            if record.descripcion and not record.descripcion_en:
                record.descripcion_en = record.descripcion
            if record.descripcion and not record.descripcion_pt:
                record.descripcion_pt = record.descripcion
            if record.seo_titulo and not record.seo_titulo_en:
                record.seo_titulo_en = record.seo_titulo
            if record.seo_titulo and not record.seo_titulo_pt:
                record.seo_titulo_pt = record.seo_titulo
            if record.seo_descripcion and not record.seo_descripcion_en:
                record.seo_descripcion_en = record.seo_descripcion
            if record.seo_descripcion and not record.seo_descripcion_pt:
                record.seo_descripcion_pt = record.seo_descripcion

class IncasTerminoCondicionSeccion(models.Model):
    _name = "incas.termino.condicion.seccion"
    _description = "Seccion de terminos y condiciones"
    _order = "sequence, id"
    _rec_name = "titulo"

    sequence = fields.Integer(string="Orden", default=10)
    termino_id = fields.Many2one(
        "incas.termino.condicion",
        string="Terminos y condiciones",
        required=True,
        ondelete="cascade",
    )
    titulo = fields.Char(string="Titulo")
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    texto_html = fields.Html(string="Contenido")
    texto_html_en = fields.Html(string="Contenido en ingles")
    texto_html_pt = fields.Html(string="Contenido en portugues")

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
