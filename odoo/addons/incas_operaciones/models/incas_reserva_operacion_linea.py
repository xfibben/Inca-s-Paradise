from odoo import fields, models


class IncasReservaOperacionLinea(models.Model):
    _name = "incas.reserva.operacion.linea"
    _description = "Linea operativa de reserva"
    _order = "fecha asc, sequence asc, id asc"

    sequence = fields.Integer(string="Secuencia", default=10)
    reserva_id = fields.Many2one("incas.reserva", string="Reserva", required=True, ondelete="cascade", index=True)
    origen_tipo = fields.Char(string="Origen tipo", index=True)
    origen_clave = fields.Char(string="Origen clave", index=True)
    fecha = fields.Date(string="Fecha", required=True, index=True)
    agencia = fields.Char(string="Agencia/Operador")
    proveedor = fields.Char(string="Proveedor")
    guia = fields.Char(string="Guia")
    asistencia = fields.Char(string="Asistencia")
    estado_operacion = fields.Char(string="Estado")
    nro_pasajeros = fields.Integer(string="Nro pasajeros")
    horario = fields.Char(string="Horario")
    lugar_recojo = fields.Char(string="Lugar de recojo")
    servicio = fields.Text(string="Servicio")
    tipo_servicio = fields.Char(string="Tipo de servicio")
    hotel_nombre = fields.Text(string="Nombre hotel")
    extras = fields.Text(string="Extras")
    saldo_pagar = fields.Float(string="Saldo a pagar")
    saldo_cobrar = fields.Float(string="Saldo a cobrar")
    pagado = fields.Char(string="Pagado")
    observacion = fields.Text(string="Observacion")
    seguimiento = fields.Text(string="Seguimiento")
