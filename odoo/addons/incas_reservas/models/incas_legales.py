from odoo import api, fields, models, tools


class IncasLegalMixin(models.AbstractModel):
    _name = "incas.legal.mixin"
    _description = "Base legal multiidioma"

    def _limpiar_texto_seo(self, valor):
        if not isinstance(valor, str):
            return valor
        valor_limpio = tools.html2plaintext(valor).replace("\xa0", " ")
        valor_limpio = " ".join(valor_limpio.split())
        return valor_limpio or False

    def _sanitizar_campos_seo_en_vals(self, vals):
        for campo in self._campos_seo():
            if campo in vals:
                vals[campo] = self._limpiar_texto_seo(vals[campo])

    def _campos_seo(self):
        return ()

    def _equivalencias_traduccion(self):
        return ()

    def _autocompletar_traducciones_en_vals(self, vals):
        for base, campo_en, campo_pt in self._equivalencias_traduccion():
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
            for base, campo_en, campo_pt in record._equivalencias_traduccion():
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


class IncasPolitica(models.Model):
    _name = "incas.politica"
    _description = "Politicas"
    _inherit = ["incas.legal.mixin"]
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
    seccion_ids = fields.One2many("incas.politica.seccion", "politica_id", string="Secciones")
    active = fields.Boolean(string="Activo", default=True)

    def _campos_seo(self):
        return (
            "meta_titulo",
            "meta_titulo_en",
            "meta_titulo_pt",
            "meta_descripcion",
            "meta_descripcion_en",
            "meta_descripcion_pt",
        )

    def _equivalencias_traduccion(self):
        return (
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("meta_titulo", "meta_titulo_en", "meta_titulo_pt"),
            ("meta_descripcion", "meta_descripcion_en", "meta_descripcion_pt"),
        )


class IncasPoliticaSeccion(models.Model):
    _name = "incas.politica.seccion"
    _description = "Seccion de politica"
    _inherit = ["incas.legal.mixin"]
    _order = "sequence, id"
    _rec_name = "titulo"

    sequence = fields.Integer(string="Orden", default=10)
    politica_id = fields.Many2one("incas.politica", string="Politica", required=True, ondelete="cascade")
    titulo = fields.Char(string="Titulo")
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    contenido = fields.Html(string="Contenido")
    contenido_en = fields.Html(string="Contenido en ingles")
    contenido_pt = fields.Html(string="Contenido en portugues")

    def _equivalencias_traduccion(self):
        return (
            ("titulo", "titulo_en", "titulo_pt"),
            ("contenido", "contenido_en", "contenido_pt"),
        )


class IncasCancelacion(models.Model):
    _name = "incas.cancelacion"
    _description = "Cancelaciones"
    _inherit = ["incas.legal.mixin"]
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
    seccion_ids = fields.One2many("incas.cancelacion.seccion", "cancelacion_id", string="Secciones")
    active = fields.Boolean(string="Activo", default=True)

    def _campos_seo(self):
        return (
            "meta_titulo",
            "meta_titulo_en",
            "meta_titulo_pt",
            "meta_descripcion",
            "meta_descripcion_en",
            "meta_descripcion_pt",
        )

    def _equivalencias_traduccion(self):
        return (
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("meta_titulo", "meta_titulo_en", "meta_titulo_pt"),
            ("meta_descripcion", "meta_descripcion_en", "meta_descripcion_pt"),
        )


class IncasCancelacionSeccion(models.Model):
    _name = "incas.cancelacion.seccion"
    _description = "Seccion de cancelacion"
    _inherit = ["incas.legal.mixin"]
    _order = "sequence, id"
    _rec_name = "titulo"

    sequence = fields.Integer(string="Orden", default=10)
    cancelacion_id = fields.Many2one("incas.cancelacion", string="Cancelacion", required=True, ondelete="cascade")
    titulo = fields.Char(string="Titulo")
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    contenido = fields.Html(string="Contenido")
    contenido_en = fields.Html(string="Contenido en ingles")
    contenido_pt = fields.Html(string="Contenido en portugues")

    def _equivalencias_traduccion(self):
        return (
            ("titulo", "titulo_en", "titulo_pt"),
            ("contenido", "contenido_en", "contenido_pt"),
        )


class IncasPreguntaFrecuente(models.Model):
    _name = "incas.pregunta.frecuente"
    _description = "Preguntas frecuentes"
    _inherit = ["incas.legal.mixin"]
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
    seccion_ids = fields.One2many("incas.pregunta.frecuente.seccion", "pregunta_frecuente_id", string="Secciones")
    active = fields.Boolean(string="Activo", default=True)

    def _campos_seo(self):
        return (
            "meta_titulo",
            "meta_titulo_en",
            "meta_titulo_pt",
            "meta_descripcion",
            "meta_descripcion_en",
            "meta_descripcion_pt",
        )

    def _equivalencias_traduccion(self):
        return (
            ("titulo", "titulo_en", "titulo_pt"),
            ("descripcion", "descripcion_en", "descripcion_pt"),
            ("meta_titulo", "meta_titulo_en", "meta_titulo_pt"),
            ("meta_descripcion", "meta_descripcion_en", "meta_descripcion_pt"),
        )


class IncasPreguntaFrecuenteSeccion(models.Model):
    _name = "incas.pregunta.frecuente.seccion"
    _description = "Seccion de preguntas frecuentes"
    _inherit = ["incas.legal.mixin"]
    _order = "sequence, id"
    _rec_name = "pregunta"

    sequence = fields.Integer(string="Orden", default=10)
    pregunta_frecuente_id = fields.Many2one(
        "incas.pregunta.frecuente",
        string="Preguntas frecuentes",
        required=True,
        ondelete="cascade",
    )
    pregunta = fields.Char(string="Pregunta")
    pregunta_en = fields.Char(string="Pregunta en ingles")
    pregunta_pt = fields.Char(string="Pregunta en portugues")
    respuesta = fields.Html(string="Respuesta")
    respuesta_en = fields.Html(string="Respuesta en ingles")
    respuesta_pt = fields.Html(string="Respuesta en portugues")

    def _equivalencias_traduccion(self):
        return (
            ("pregunta", "pregunta_en", "pregunta_pt"),
            ("respuesta", "respuesta_en", "respuesta_pt"),
        )
