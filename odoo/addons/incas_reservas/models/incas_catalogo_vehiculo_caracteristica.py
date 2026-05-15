from odoo import api, fields, models


class IncasCatalogoVehiculoCaracteristica(models.Model):
    _name = "incas.catalogo.vehiculo.caracteristica"
    _description = "Característica de vehículo"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    vehiculo_id = fields.Many2one(
        "incas.catalogo.vehiculo",
        string="Vehículo",
        required=True,
        ondelete="cascade",
    )
    titulo = fields.Char(string="Título", required=True, default="Nueva característica")
    descripcion = fields.Html(string="Descripción")
    titulo_en = fields.Char(string="Título en inglés")
    descripcion_en = fields.Html(string="Descripción en inglés")
    titulo_pt = fields.Char(string="Título en portugués")
    descripcion_pt = fields.Html(string="Descripción en portugués")

    def _auto_init(self):
        self._migrar_columnas_legadas_jsonb()
        return super()._auto_init()

    def _migrar_columnas_legadas_jsonb(self):
        columnas = {
            "titulo": "varchar",
            "descripcion": "text",
            "titulo_en": "varchar",
            "descripcion_en": "text",
            "titulo_pt": "varchar",
            "descripcion_pt": "text",
        }
        for columna, tipo_destino in columnas.items():
            self.env.cr.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'incas_catalogo_vehiculo_caracteristica'
                  AND column_name = %s
                """,
                [columna],
            )
            fila = self.env.cr.fetchone()
            if not fila or fila[0] != "jsonb":
                continue
            self.env.cr.execute(
                f"""
                ALTER TABLE incas_catalogo_vehiculo_caracteristica
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
            for campo in ("titulo", "descripcion", "titulo_en", "descripcion_en", "titulo_pt", "descripcion_pt"):
                if campo in fila:
                    fila[campo] = self._normalizar_valor_legacy(fila[campo])
        return filas

    @api.model_create_multi
    def create(self, vals_list):
        self._migrar_columnas_legadas_jsonb()
        for vals in vals_list:
            self._autocompletar_traducciones_en_vals(vals)
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
        titulo_base = vals.get("titulo")
        descripcion_base = vals.get("descripcion")
        if titulo_base:
            for campo in ("titulo_en", "titulo_pt"):
                if not vals.get(campo):
                    vals[campo] = titulo_base
        if descripcion_base:
            for campo in ("descripcion_en", "descripcion_pt"):
                if not vals.get(campo):
                    vals[campo] = descripcion_base

    def _completar_traducciones_vacias(self):
        for record in self:
            valores = {}
            if record.titulo:
                for campo in ("titulo_en", "titulo_pt"):
                    if not record[campo]:
                        valores[campo] = record.titulo
            if record.descripcion:
                for campo in ("descripcion_en", "descripcion_pt"):
                    if not record[campo]:
                        valores[campo] = record.descripcion
            if valores:
                record.with_context(skip_autocompletar_traducciones=True).write(valores)

    @api.onchange("titulo", "descripcion")
    def _onchange_autocompletar_traducciones(self):
        for record in self:
            if record.titulo:
                for campo in ("titulo_en", "titulo_pt"):
                    if not record[campo]:
                        record[campo] = record.titulo
            if record.descripcion:
                for campo in ("descripcion_en", "descripcion_pt"):
                    if not record[campo]:
                        record[campo] = record.descripcion
