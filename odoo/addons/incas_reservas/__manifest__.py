{
    "name": "Inca's Paradise Reservas",
    "summary": "Gestión interna de cotizaciones, reservas y pasajeros",
    "version": "19.0.1.0.0",
    "category": "Inca's Paradise",
    "author": "Inca's Paradise",
    "license": "LGPL-3",
    "depends": ["incas_core"],
    "data": [
        "security/ir.model.access.csv",
        "data/incas_reservas_sequence.xml",
        "views/incas_servicio_catalogo_views.xml",
        "views/incas_cotizacion_views.xml",
        "views/incas_reserva_views.xml",
        "views/incas_pasajero_views.xml",
    ],
    "application": False,
    "installable": True,
}
