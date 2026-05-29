{
    "name": "Inca's Paradise Operaciones",
    "summary": "Seguimiento operativo y control de actividades",
    "version": "19.0.1.0.0",
    "category": "Inca's Paradise",
    "author": "Inca's Paradise",
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
    "depends": ["incas_core", "incas_reservas", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/incas_operaciones_sync.xml",
        "views/incas_reserva_operaciones_views.xml",
        "views/incas_agenda_evento_views.xml",
        "views/mail_activity_views.xml",
    ],
    "application": False,
    "installable": True,
}
