from odoo import api, fields, models


class IncasSubcategoriaDestino(models.Model):
    _name = "incas.subcategoria.destino"
    _description = "Subcategoría de destino"
    _order = "sequence, nombre, id"
    _rec_name = "nombre"

    sequence = fields.Integer(string="Secuencia", default=10)
    nombre = fields.Char(string="Nombre", required=True)
    nombre_en = fields.Char(string="Nombre en inglés")
    nombre_pt = fields.Char(string="Nombre en portugués")
    destino_id = fields.Many2one(
        "incas.catalogo.destino",
        string="Destino",
        required=True,
        ondelete="cascade",
    )
    tour_ids = fields.One2many(
        "incas.tour",
        "subcategoria_destino_id",
        string="Tours",
    )
    tour_count = fields.Integer(string="Tours", compute="_compute_tour_count")
    legacy_subcategoria_tour_id = fields.Integer(string="ID legado", readonly=True, copy=False, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "incas_subcategoria_destino_legacy_unique",
            "unique(legacy_subcategoria_tour_id)",
            "La subcategoría legada ya fue migrada.",
        ),
    ]

    def _auto_init(self):
        res = super()._auto_init()
        self._migrar_desde_subcategoria_tour_legada()
        return res

    def _migrar_desde_subcategoria_tour_legada(self):
        self.env.cr.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'incas_subcategoria_tour'
            )
            """
        )
        fila = self.env.cr.fetchone()
        if not fila or not fila[0]:
            return

        self.env.cr.execute(
            """
            SELECT legacy.id, legacy.sequence, legacy.nombre, legacy.destino_id, legacy.active
            FROM incas_subcategoria_tour legacy
            WHERE NOT EXISTS (
                SELECT 1
                FROM incas_subcategoria_destino actual
                WHERE actual.legacy_subcategoria_tour_id = legacy.id
            )
            ORDER BY legacy.id
            """
        )
        for legacy_id, sequence, nombre, destino_id, active in self.env.cr.fetchall():
            nueva = self.create(
                {
                    "sequence": sequence or 10,
                    "nombre": nombre,
                    "nombre_en": nombre,
                    "nombre_pt": nombre,
                    "destino_id": destino_id,
                    "legacy_subcategoria_tour_id": legacy_id,
                    "active": active,
                }
            )
            self.env.cr.execute(
                """
                UPDATE incas_tour
                   SET subcategoria_destino_id = %s
                 WHERE subcategoria_destino_id IS NULL
                   AND id IN (
                       SELECT rel.tour_id
                       FROM incas_subcategoria_tour_web_tour_rel rel
                       WHERE rel.subcategoria_id = %s
                   )
                """,
                [nueva.id, legacy_id],
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

    @api.depends("tour_ids")
    def _compute_tour_count(self):
        for record in self:
            record.tour_count = len(record.tour_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._copiar_traduccion_si_vacia(vals, "nombre")
        return super().create(vals_list)

    def write(self, vals):
        valores = dict(vals)
        if "nombre" in valores:
            if "nombre_en" not in valores and any(not record.nombre_en for record in self):
                valores["nombre_en"] = valores["nombre"]
            if "nombre_pt" not in valores and any(not record.nombre_pt for record in self):
                valores["nombre_pt"] = valores["nombre"]
        return super().write(valores)

    @api.onchange("nombre")
    def _onchange_copiar_nombre_es(self):
        for record in self:
            if record.nombre and not record.nombre_en:
                record.nombre_en = record.nombre
            if record.nombre and not record.nombre_pt:
                record.nombre_pt = record.nombre
