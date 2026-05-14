from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IncasCatalogoTransporteTarifa(models.Model):
    _name = "incas.catalogo.transporte.tarifa"
    _description = "Tarifa de transporte por vehículo"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    transporte_id = fields.Many2one(
        "incas.catalogo.transporte",
        string="Transporte",
        required=True,
        ondelete="cascade",
    )
    vehiculo_id = fields.Many2one(
        "incas.catalogo.vehiculo",
        string="Vehículo",
        required=True,
        ondelete="restrict",
    )
    precio_adulto_usd = fields.Float(string="Precio adulto USD", required=True, default=0)
    precio_nino_usd = fields.Float(string="Precio niño USD", default=0)
    descuento = fields.Float(string="Descuento", default=0)
    active = fields.Boolean(default=True)

    _incas_catalogo_transporte_tarifa_unique = models.Constraint(
        "UNIQUE(transporte_id, vehiculo_id)",
        "Ya existe una tarifa para este vehículo dentro del transporte.",
    )

    @api.constrains("precio_adulto_usd", "precio_nino_usd", "descuento")
    def _check_valores(self):
        for record in self:
            if record.precio_adulto_usd < 0 or record.precio_nino_usd < 0:
                raise ValidationError("Los precios no pueden ser negativos.")
            if record.descuento < 0 or record.descuento > 100:
                raise ValidationError("El descuento debe estar entre 0 y 100.")
