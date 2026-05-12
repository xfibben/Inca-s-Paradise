{
    "name": "Inca's Paradise Documentos",
    "summary": "Integración documental DMS para el back office de Inca's Paradise",
    "version": "19.0.1.0.0",
    "category": "Inca's Paradise",
    "author": "Inca's Paradise",
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
    "depends": ["incas_core", "dms"],
    "data": [
        "security/incas_documentos_security.xml",
        "views/incas_documentos_dms_overrides.xml",
        "views/incas_documentos_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "incas_documentos/static/src/js/attachment.esm.js",
            "incas_documentos/static/src/js/dms_file_actions.esm.js",
            "incas_documentos/static/src/js/dms_file_upload.esm.js",
            "incas_documentos/static/src/xml/dms_file_upload.xml",
        ],
    },
    "application": False,
    "installable": True,
}
