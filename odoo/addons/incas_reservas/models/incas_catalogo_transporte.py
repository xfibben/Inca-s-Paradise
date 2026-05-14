import json

from odoo import api, fields, models


class IncasCatalogoTransporte(models.Model):
    _name = "incas.catalogo.transporte"
    _description = "Catálogo local de transportes"
    _inherits = {"incas.servicio.catalogo": "servicio_id"}
    _order = "name"

    servicio_id = fields.Many2one("incas.servicio.catalogo", string="Servicio base", required=True, ondelete="cascade")
    image_data = fields.Text(string="Imagen")
    wallpaper_data = fields.Text(string="Wallpaper")
    destino_origen_data = fields.Text(string="Destino origen")
    destino_llegada_data = fields.Text(string="Destino llegada")
    modelo_vehiculo = fields.Char(string="Modelo de vehículo")
    estilo_transporte_ids = fields.Many2many(
        "incas.estilo.transporte",
        "incas_catalogo_transporte_estilo_rel",
        "transporte_id",
        "estilo_id",
        string="Tipos de transporte",
    )
    tarifa_ids = fields.One2many(
        "incas.catalogo.transporte.tarifa",
        "transporte_id",
        string="Tarifas por vehículo",
    )
    vehiculo_ids = fields.Many2many(
        "incas.catalogo.vehiculo",
        string="Vehículos",
        compute="_compute_vehiculo_ids",
    )
    duracion_viaje = fields.Char(string="Duración del viaje")
    distancia = fields.Char(string="Distancia")
    descripcion_origen = fields.Text(string="Descripción origen")
    descripcion_llegada = fields.Text(string="Descripción llegada")
    descripcion = fields.Text(string="Descripción")
    included_title = fields.Char(string="Included title")
    included_items_data = fields.Text(string="Included items")
    excluded_title = fields.Char(string="Excluded title")
    excluded_items_data = fields.Text(string="Excluded items")
    tipos_transporte_data = fields.Text(
        string="Tipos de transporte",
        compute="_compute_legacy_transport_data",
        store=True,
    )
    seo_title = fields.Char(string="SEO title")
    seo_description = fields.Text(string="SEO description")
    precios_data = fields.Text(
        string="Precios por vehículo",
        compute="_compute_legacy_transport_data",
        store=True,
    )

    _sql_constraints = [
        ("incas_catalogo_transporte_servicio_unique", "unique(servicio_id)", "El transporte ya está vinculado a un servicio."),
    ]

    @api.depends("tarifa_ids.vehiculo_id", "servicio_id")
    def _compute_vehiculo_ids(self):
        for record in self:
            if record.tarifa_ids:
                record.vehiculo_ids = record.tarifa_ids.mapped("vehiculo_id")
            else:
                record.vehiculo_ids = self.env["incas.catalogo.vehiculo"]

    @api.depends(
        "estilo_transporte_ids.name",
        "estilo_transporte_ids.slug",
        "estilo_transporte_ids.descripcion",
        "tarifa_ids.sequence",
        "tarifa_ids.vehiculo_id.nombre",
        "tarifa_ids.vehiculo_id.descripcion",
        "tarifa_ids.vehiculo_id.imagen",
        "tarifa_ids.vehiculo_id.caracteristica_ids.titulo",
        "tarifa_ids.vehiculo_id.caracteristica_ids.descripcion",
        "tarifa_ids.precio_adulto_usd",
        "tarifa_ids.precio_nino_usd",
        "tarifa_ids.descuento",
    )
    def _compute_legacy_transport_data(self):
        for record in self:
            tipos = []
            for estilo in record.estilo_transporte_ids.sorted(lambda item: (item.nro_orden, item.name or "")):
                tipos.append(
                    {
                        "nombre": estilo.name,
                        "slug": estilo.slug,
                        "descripcion": estilo.descripcion,
                    }
                )
            precios = []
            for tarifa in record.tarifa_ids.sorted(lambda item: (item.sequence, item.id)):
                precios.append(
                    {
                        "precioAdulto": tarifa.precio_adulto_usd or 0,
                        "precioNino": tarifa.precio_nino_usd or 0,
                        "descuento": tarifa.descuento or 0,
                        "vehiculo": [
                            {
                                "nombre": tarifa.vehiculo_id.nombre,
                                "descripcion": tarifa.vehiculo_id.descripcion,
                                "imagen": self._json_lista(tarifa.vehiculo_id.imagen),
                                "features": [
                                    {
                                        "title": caracteristica.titulo,
                                        "description": caracteristica.descripcion,
                                    }
                                    for caracteristica in tarifa.vehiculo_id.caracteristica_ids.sorted(
                                        lambda item: (item.sequence, item.id)
                                    )
                                ],
                            }
                        ],
                    }
                )
            record.tipos_transporte_data = json.dumps(tipos, ensure_ascii=False, indent=2) if tipos else False
            record.precios_data = json.dumps(precios, ensure_ascii=False, indent=2) if precios else False

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)

    def _json_lista(self, valor):
        if not valor:
            return []
        try:
            data = json.loads(valor)
            return data if isinstance(data, list) else [data]
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
