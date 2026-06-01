import html
import json
import os
from urllib.parse import quote
from urllib.error import URLError
from urllib.request import Request, urlopen

from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


def _normalize_text(value):
    return str(value or "").replace("\r\n", "\n").replace("\\n", "\n")


def _html_text(value):
    return html.escape(_normalize_text(value))


def _render_inline_html(node):
    if isinstance(node, str):
        return _html_text(node)
    if not isinstance(node, dict):
        return ""
    if isinstance(node.get("text"), str):
        text = _html_text(node["text"])
        if node.get("code"):
            text = f"<code>{text}</code>"
        if node.get("bold"):
            text = f"<strong>{text}</strong>"
        if node.get("italic"):
            text = f"<em>{text}</em>"
        if node.get("strikethrough"):
            text = f"<s>{text}</s>"
        if node.get("underline"):
            text = f"<u>{text}</u>"
        return text
    children = node.get("children") if isinstance(node.get("children"), list) else node.get("content")
    children = children if isinstance(children, list) else []
    text = "".join(_render_inline_html(child) for child in children)
    if str(node.get("type") or "").lower() == "link" and node.get("url"):
        return f'<a href="{html.escape(str(node.get("url")))}">{text or html.escape(str(node.get("url")))}</a>'
    return text


def _render_list_item_html(node):
    if not isinstance(node, dict):
        return ""
    children = node.get("children") if isinstance(node.get("children"), list) else node.get("content")
    children = children if isinstance(children, list) else []
    if not children:
        text = _render_inline_html(node).strip()
        return f"<li>{text}</li>" if text else ""
    body = []
    for child in children:
        child_type = str(child.get("type") or "").lower() if isinstance(child, dict) else ""
        if child_type in {"paragraph", "heading", "quote", "blockquote", "code", "codeblock", "list", "list-item"}:
            body.append(_render_node_html(child))
        else:
            text = _render_inline_html(child).strip()
            if text:
                body.append(text)
    contenido = "".join(body).strip()
    return f"<li>{contenido}</li>" if contenido else ""


def _render_node_html(node):
    if isinstance(node, str):
        texto = _html_text(node).strip()
        return f"<p>{texto}</p>" if texto else ""
    if not isinstance(node, dict):
        return ""
    node_type = str(node.get("type") or "").lower()
    children = node.get("children") if isinstance(node.get("children"), list) else node.get("content")
    children = children if isinstance(children, list) else []
    if node_type == "paragraph":
        text = "".join(_render_inline_html(child) for child in children).strip()
        return f"<p>{text}</p>" if text else ""
    if node_type == "heading":
        level = min(max(int(node.get("level") or 2), 1), 6)
        text = "".join(_render_inline_html(child) for child in children).strip()
        return f"<h{level}>{text}</h{level}>" if text else ""
    if node_type in {"quote", "blockquote"}:
        body = "".join(_render_node_html(child) for child in children)
        return f"<blockquote>{body}</blockquote>" if body else ""
    if node_type in {"code", "codeblock"}:
        code = node.get("code") if isinstance(node.get("code"), str) else "".join(_render_inline_html(child) for child in children)
        return f"<pre><code>{_html_text(code)}</code></pre>" if code else ""
    if node_type == "image" and isinstance(node.get("image"), dict) and node["image"].get("url"):
        alt = html.escape(str(node["image"].get("alternativeText") or ""))
        url = html.escape(str(node["image"]["url"]))
        return f'<img src="{url}" alt="{alt}" />'
    if node_type == "list":
        ordered = node.get("format") == "ordered" or node.get("listType") == "ordered"
        tag = "ol" if ordered else "ul"
        items = "".join(_render_list_item_html(child) for child in children)
        return f"<{tag}>{items}</{tag}>" if items else ""
    if node_type == "list-item":
        return _render_list_item_html(node)
    if children:
        return "".join(_render_node_html(child) for child in children)
    if isinstance(node.get("text"), str):
        text = _render_inline_html(node).strip()
        return f"<p>{text}</p>" if text else ""
    return ""


def _strapi_richtext_to_html(value):
    if isinstance(value, str):
        texto = _normalize_text(value).strip()
        return texto if "<" in texto else f"<p>{_html_text(texto)}</p>" if texto else ""
    if isinstance(value, list):
        return "".join(_render_node_html(item) for item in value).strip()
    if isinstance(value, dict):
        return _render_node_html(value).strip()
    return ""


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

    def _strapi_endpoint(self):
        return False

    def _strapi_section_key(self):
        return False

    def _strapi_section_model_name(self):
        return False

    def _strapi_section_field_map(self):
        return {}

    def _strapi_base_url(self):
        return (os.getenv("PUBLIC_STRAPI_URL") or "https://api.incasparadise.com").rstrip("/")

    def _strapi_fetch_single_type(self, locale):
        endpoint = self._strapi_endpoint()
        if not endpoint:
            return {}
        url = (
            f"{self._strapi_base_url()}{endpoint}"
            f"?populate[*]=*&locale={quote(locale)}&status=published"
        )
        request = Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except URLError as error:
            raise ValidationError(
                "No se pudo conectar con Strapi.\n"
                f"URL usada: {url}\n"
                "Configure PUBLIC_STRAPI_URL accesible desde Odoo."
            ) from error
        return payload.get("data") or {}

    def action_importar_desde_strapi(self):
        self.ensure_one()
        section_key = self._strapi_section_key()
        section_model_name = self._strapi_section_model_name()
        section_field_map = self._strapi_section_field_map()
        if not section_key or not section_model_name or not section_field_map:
            return False
        section_model = self.env[section_model_name]
        locales = {
            "": "es-PE",
            "_en": "en",
            "_pt": "pt",
        }
        section_parent_field = False
        for nombre, field in section_model._fields.items():
            if getattr(field, "comodel_name", False) == self._name and field.type == "many2one":
                section_parent_field = nombre
                break
        if not section_parent_field:
            return False

        valores_principales = {}
        secciones_por_orden = {}
        for sufijo, locale in locales.items():
            data = self._strapi_fetch_single_type(locale)
            if not data:
                continue
            valores_principales.update(
                {
                    f"titulo{sufijo}": data.get("titulo") or False,
                    f"descripcion{sufijo}": _strapi_richtext_to_html(data.get("descripcion")),
                    f"meta_titulo{sufijo}": data.get("metaTitle") or False,
                    f"meta_descripcion{sufijo}": tools.html2plaintext(_strapi_richtext_to_html(data.get("metaDescription"))).strip() or False,
                }
            )
            for indice, seccion in enumerate(data.get(section_key) or [], start=1):
                valores_seccion = secciones_por_orden.setdefault(
                    indice,
                    {
                        "sequence": indice * 10,
                        section_parent_field: self.id,
                    },
                )
                for campo_strapi, campo_odoo in section_field_map.items():
                    valor = seccion.get(campo_strapi)
                    if campo_odoo.startswith("respuesta") or campo_odoo.startswith("contenido"):
                        valores_seccion[f"{campo_odoo}{sufijo}"] = _strapi_richtext_to_html(valor)
                    else:
                        valores_seccion[f"{campo_odoo}{sufijo}"] = valor or False

        if valores_principales:
            self.write(valores_principales)

        section_records = section_model.search([(section_parent_field, "=", self.id)])
        existentes = {item.sequence: item for item in section_records.sorted(lambda rec: (rec.sequence, rec.id))}
        vistos = section_model.browse()
        for orden in sorted(secciones_por_orden):
            valores = secciones_por_orden[orden]
            sequence = valores["sequence"]
            seccion = existentes.get(sequence)
            if seccion:
                seccion.write(valores)
            else:
                seccion = section_model.create(valores)
            vistos |= seccion
        (section_records - vistos).unlink()

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

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

    def _strapi_endpoint(self):
        return "/api/cancelaciones"

    def _strapi_section_key(self):
        return "secciones"

    def _strapi_section_model_name(self):
        return "incas.cancelacion.seccion"

    def _strapi_section_field_map(self):
        return {
            "titulo": "titulo",
            "contenido": "contenido",
        }


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

    def _strapi_endpoint(self):
        return "/api/preguntas-frecuentes"

    def _strapi_section_key(self):
        return "sections"

    def _strapi_section_model_name(self):
        return "incas.pregunta.frecuente.seccion"

    def _strapi_section_field_map(self):
        return {
            "pregunta": "pregunta",
            "respuesta": "respuesta",
        }


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
