from odoo import api, fields, models


class IncasProveedor(models.Model):
    _name = "incas.proveedor"
    _description = "Proveedor"
    _order = "name"

    name = fields.Char(string="Proveedor", required=True)
    partner_id = fields.Many2one("res.partner", string="Contacto relacionado", ondelete="set null")
    contact_name = fields.Char(string="Contacto principal")
    email = fields.Char(string="Correo electronico")
    phone = fields.Char(string="Telefono")
    mobile = fields.Char(string="Celular")
    website = fields.Char(string="Sitio web")
    tipo_proveedor = fields.Selection(
        [
            ("hotel", "Hotel"),
            ("transporte", "Transporte"),
            ("tour", "Tour"),
            ("alimentacion", "Alimentacion"),
            ("documentacion", "Documentacion"),
            ("operacion", "Operacion"),
            ("otro", "Otro"),
        ],
        string="Tipo de proveedor",
        required=True,
        default="otro",
    )
    street = fields.Char(string="Direccion")
    street2 = fields.Char(string="Direccion 2")
    city = fields.Char(string="Ciudad")
    state_id = fields.Many2one("res.country.state", string="Provincia/Estado")
    zip = fields.Char(string="Codigo postal")
    country_id = fields.Many2one("res.country", string="Pais")
    notes = fields.Text(string="Notas")
    active = fields.Boolean(default=True)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for record in self:
            partner = record.partner_id
            if not partner:
                continue
            record.name = partner.name or record.name
            record.contact_name = partner.name or False
            record.email = partner.email or False
            record.phone = partner.phone or False
            record.mobile = partner.mobile or False
            record.website = partner.website or False
            record.street = partner.street or False
            record.street2 = partner.street2 or False
            record.city = partner.city or False
            record.state_id = partner.state_id
            record.zip = partner.zip or False
            record.country_id = partner.country_id
