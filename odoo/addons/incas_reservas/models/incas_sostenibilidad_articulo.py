from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class IncasSostenibilidadArticulo(models.Model):
    _name = "incas.sostenibilidad.articulo"
    _description = "Articulo de sostenibilidad"
    _order = "fecha_publicacion desc, sequence, id desc"
    _rec_name = "titulo"

    titulo = fields.Char(string="Titulo", required=True)
    titulo_en = fields.Char(string="Titulo en ingles")
    titulo_pt = fields.Char(string="Titulo en portugues")
    titulo_fr = fields.Char(string="Titulo en frances")
    titulo_it = fields.Char(string="Titulo en italiano")
    contenido_html = fields.Html(string="Contenido HTML")
    contenido_html_en = fields.Html(string="Contenido HTML en ingles")
    contenido_html_pt = fields.Html(string="Contenido HTML en portugues")
    contenido_html_fr = fields.Html(string="Contenido HTML en frances")
    contenido_html_it = fields.Html(string="Contenido HTML en italiano")
    slug = fields.Char(string="Slug", required=True, index=True)
    slug_en = fields.Char(string="Slug en ingles", index=True)
    slug_pt = fields.Char(string="Slug en portugues", index=True)
    slug_fr = fields.Char(string="Slug en frances", index=True)
    slug_it = fields.Char(string="Slug en italiano", index=True)
    seo_titulo = fields.Char(string="SEO titulo")
    seo_titulo_en = fields.Char(string="SEO titulo en ingles")
    seo_titulo_pt = fields.Char(string="SEO titulo en portugues")
    seo_titulo_fr = fields.Char(string="SEO titulo en frances")
    seo_titulo_it = fields.Char(string="SEO titulo en italiano")
    seo_descripcion = fields.Text(string="SEO descripcion")
    seo_descripcion_en = fields.Text(string="SEO descripcion en ingles")
    seo_descripcion_pt = fields.Text(string="SEO descripcion en portugues")
    seo_descripcion_fr = fields.Text(string="SEO descripcion en frances")
    seo_descripcion_it = fields.Text(string="SEO descripcion en italiano")
    mostrar_en_portada = fields.Boolean(string="Mostrar en portada")
    tour_ids = fields.Many2many(
        "incas.tour",
        "incas_sostenibilidad_articulo_tour_rel",
        "articulo_id",
        "tour_id",
        string="Tours relacionados",
    )
    tour_ids_en = fields.Many2many(
        "incas.tour",
        "incas_sostenibilidad_articulo_tour_en_rel",
        "articulo_id",
        "tour_id",
        string="Tours relacionados en ingles",
    )
    tour_ids_pt = fields.Many2many(
        "incas.tour",
        "incas_sostenibilidad_articulo_tour_pt_rel",
        "articulo_id",
        "tour_id",
        string="Tours relacionados en portugues",
    )
    tour_ids_fr = fields.Many2many(
        "incas.tour",
        "incas_sostenibilidad_articulo_tour_fr_rel",
        "articulo_id",
        "tour_id",
        string="Tours relacionados en frances",
    )
    tour_ids_it = fields.Many2many(
        "incas.tour",
        "incas_sostenibilidad_articulo_tour_it_rel",
        "articulo_id",
        "tour_id",
        string="Tours relacionados en italiano",
    )
    destino_ids = fields.Many2many(
        "incas.catalogo.destino",
        "incas_sostenibilidad_articulo_destino_rel",
        "articulo_id",
        "destino_id",
        string="Destinos",
    )
    etiqueta_ids = fields.Many2many(
        "incas.sostenibilidad.etiqueta",
        "incas_sostenibilidad_articulo_etiqueta_rel",
        "articulo_id",
        "etiqueta_id",
        string="Etiquetas",
    )
    imagen_portada = fields.Image(string="Imagen portada")
    fecha_publicacion = fields.Date(string="Fecha publicacion", default=fields.Date.context_today, required=True)
    sequence = fields.Integer(string="Orden", default=10)
    active = fields.Boolean(string="Activo", default=True)
    portada_requiere_confirmacion = fields.Boolean(string="Requiere confirmacion de portada", compute="_compute_estado_portada")
    portada_resumen = fields.Text(string="Resumen portada", compute="_compute_estado_portada")

    _sql_constraints = [
        ("incas_sostenibilidad_articulo_slug_unique", "unique(slug)", "El slug en español ya existe."),
        ("incas_sostenibilidad_articulo_slug_en_unique", "unique(slug_en)", "El slug en ingles ya existe."),
        ("incas_sostenibilidad_articulo_slug_pt_unique", "unique(slug_pt)", "El slug en portugues ya existe."),
        ("incas_sostenibilidad_articulo_slug_fr_unique", "unique(slug_fr)", "El slug en frances ya existe."),
        ("incas_sostenibilidad_articulo_slug_it_unique", "unique(slug_it)", "El slug en italiano ya existe."),
    ]

    def _limpiar_texto_seo(self, valor):
        if not isinstance(valor, str):
            return valor
        valor_limpio = tools.html2plaintext(valor).replace("\xa0", " ")
        valor_limpio = " ".join(valor_limpio.split())
        return valor_limpio or False

    def _articulos_portada_actuales(self):
        return self.search(
            [("mostrar_en_portada", "=", True), ("active", "=", True)],
            order="fecha_publicacion asc, create_date asc, id asc",
        )

    def _articulos_portada_excluyendo_actual(self):
        return self.search(
            [("mostrar_en_portada", "=", True), ("active", "=", True), ("id", "not in", self.ids)],
            order="fecha_publicacion asc, create_date asc, id asc",
        )

    def _mensaje_reemplazo_portada(self, articulos_portada=None):
        articulos = articulos_portada or self._articulos_portada_excluyendo_actual()
        if len(articulos) < 3:
            return False
        nombres = ", ".join(articulos[:3].mapped("titulo"))
        antiguo = articulos[0]
        return _(
            "Ya hay 3 blogs marcados para portada: %(nombres)s. "
            "Si aceptas, se quitara de portada el mas antiguo: %(antiguo)s."
        ) % {
            "nombres": nombres,
            "antiguo": antiguo.titulo,
        }

    def _sanitizar_campos_seo_en_vals(self, vals):
        for campo in (
            "seo_titulo",
            "seo_titulo_en",
            "seo_titulo_pt",
            "seo_titulo_fr",
            "seo_titulo_it",
            "seo_descripcion",
            "seo_descripcion_en",
            "seo_descripcion_pt",
            "seo_descripcion_fr",
            "seo_descripcion_it",
        ):
            if campo in vals:
                vals[campo] = self._limpiar_texto_seo(vals[campo])

    def _copiar_traducciones_si_vacias(self, vals, campo_base):
        if campo_base not in vals:
            return
        valor_base = vals[campo_base]
        for sufijo in ("_en", "_pt", "_fr", "_it"):
            campo = f"{campo_base}{sufijo}"
            if not vals.get(campo):
                vals[campo] = valor_base

    def _propagar_traducciones_faltantes_en_write(self, vals):
        for campo in ("titulo", "contenido_html", "slug", "seo_titulo", "seo_descripcion"):
            if campo not in vals:
                continue
            for sufijo in ("_en", "_pt", "_fr", "_it"):
                campo_trad = f"{campo}{sufijo}"
                if campo_trad not in vals and any(not record[campo_trad] for record in self):
                    vals[campo_trad] = vals[campo]

    def _propagar_tours_relacionados_faltantes_en_write(self, vals):
        if "tour_ids" not in vals:
            return
        for sufijo in ("_en", "_pt", "_fr", "_it"):
            campo = f"tour_ids{sufijo}"
            if campo not in vals and any(not record[campo] for record in self):
                vals[campo] = vals["tour_ids"]

    def _normalizar_etiquetas_en_vals(self, vals):
        if "etiqueta_ids" not in vals:
            return
        etiqueta_model = self.env["incas.sostenibilidad.etiqueta"]
        comandos = []
        for comando in vals["etiqueta_ids"]:
            if not isinstance(comando, (list, tuple)) or not comando:
                comandos.append(comando)
                continue
            tipo = comando[0]
            if tipo == 0 and len(comando) > 2 and isinstance(comando[2], dict):
                data = dict(comando[2])
                if "name" in data:
                    data["name"] = etiqueta_model._normalizar_nombre(data["name"])
                comandos.append((0, 0, data))
                continue
            if tipo == 1 and len(comando) > 2 and isinstance(comando[2], dict):
                data = dict(comando[2])
                if "name" in data:
                    data["name"] = etiqueta_model._normalizar_nombre(data["name"])
                comandos.append((1, comando[1], data))
                continue
            comandos.append(comando)
        vals["etiqueta_ids"] = comandos

    def _validar_limite_portada(self, vals):
        if not vals.get("mostrar_en_portada"):
            return
        if self.env.context.get("sostenibilidad_confirmar_portada"):
            return
        # Evita que entren mas de 3 por save directo o importacion.
        articulos = self._articulos_portada_excluyendo_actual()
        if len(articulos) >= 3:
            raise ValidationError(self._mensaje_reemplazo_portada(articulos))

    def _activar_en_portada(self):
        self.ensure_one()
        articulos = self._articulos_portada_excluyendo_actual()
        if len(articulos) >= 3:
            # Siempre sale el mas antiguo para mantener solo 3 en portada.
            articulos[0].sudo().write({"mostrar_en_portada": False})
        if not self.mostrar_en_portada:
            super(IncasSostenibilidadArticulo, self).write({"mostrar_en_portada": True})

    @api.depends("mostrar_en_portada", "active", "fecha_publicacion")
    def _compute_estado_portada(self):
        for record in self:
            record.portada_requiere_confirmacion = False
            record.portada_resumen = False
            if not record.mostrar_en_portada:
                continue
            articulos = record._articulos_portada_excluyendo_actual()
            if len(articulos) >= 3:
                record.portada_requiere_confirmacion = True
                record.portada_resumen = record._mensaje_reemplazo_portada(articulos)

    def action_abrir_confirmacion_portada(self):
        self.ensure_one()
        articulos = self._articulos_portada_excluyendo_actual()
        if len(articulos) < 3:
            self._activar_en_portada()
            return {"type": "ir.actions.client", "tag": "reload"}
        wizard = self.env["incas.sostenibilidad.portada.wizard"].create(
            {
                "articulo_id": self.id,
                "articulo_antiguo_id": articulos[0].id,
                "mensaje": self._mensaje_reemplazo_portada(articulos),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Confirmar reemplazo en portada",
            "res_model": "incas.sostenibilidad.portada.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitizar_campos_seo_en_vals(vals)
            self._normalizar_etiquetas_en_vals(vals)
            for campo in ("titulo", "contenido_html", "slug", "seo_titulo", "seo_descripcion", "tour_ids"):
                self._copiar_traducciones_si_vacias(vals, campo)
            self._validar_limite_portada(vals)
        return super().create(vals_list)

    def write(self, vals):
        valores = dict(vals)
        self._sanitizar_campos_seo_en_vals(valores)
        self._normalizar_etiquetas_en_vals(valores)
        self._propagar_traducciones_faltantes_en_write(valores)
        self._propagar_tours_relacionados_faltantes_en_write(valores)
        self._validar_limite_portada(valores)
        return super().write(valores)

    @api.onchange("titulo", "contenido_html", "slug", "seo_titulo", "seo_descripcion", "tour_ids", "etiqueta_ids")
    def _onchange_copiar_contenido_es(self):
        for record in self:
            for campo in (
                "seo_titulo",
                "seo_titulo_en",
                "seo_titulo_pt",
                "seo_titulo_fr",
                "seo_titulo_it",
                "seo_descripcion",
                "seo_descripcion_en",
                "seo_descripcion_pt",
                "seo_descripcion_fr",
                "seo_descripcion_it",
            ):
                record[campo] = record._limpiar_texto_seo(record[campo])
            for etiqueta in record.etiqueta_ids:
                etiqueta.name = etiqueta.name.upper() if etiqueta.name else etiqueta.name
            for campo in ("titulo", "contenido_html", "slug", "seo_titulo", "seo_descripcion", "tour_ids"):
                valor = record[campo]
                for sufijo in ("_en", "_pt", "_fr", "_it"):
                    campo_trad = f"{campo}{sufijo}"
                    if valor and not record[campo_trad]:
                        record[campo_trad] = valor

    @api.onchange("mostrar_en_portada")
    def _onchange_mostrar_en_portada(self):
        for record in self:
            if not record.mostrar_en_portada:
                continue
            articulos = record._articulos_portada_excluyendo_actual()
            if len(articulos) < 3:
                continue
            record.mostrar_en_portada = False
            record.portada_requiere_confirmacion = True
            record.portada_resumen = record._mensaje_reemplazo_portada(articulos)
            return {
                "warning": {
                    "title": _("Limite de blogs en portada"),
                    "message": record.portada_resumen,
                }
            }
