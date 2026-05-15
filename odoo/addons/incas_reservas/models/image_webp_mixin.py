import base64
from io import BytesIO

from PIL import Image

from odoo import models


class IncasImageWebpMixin(models.AbstractModel):
    _name = "incas.image.webp.mixin"
    _description = "Mixin para convertir imágenes a webp"

    def _convertir_a_webp_en_vals(self, vals, campos_imagen):
        for campo in campos_imagen:
            if vals.get(campo):
                vals[campo] = self._imagen_a_webp(vals[campo])

    def _imagen_a_webp(self, valor):
        if not valor:
            return valor
        imagen_bytes = base64.b64decode(valor)
        with Image.open(BytesIO(imagen_bytes)) as imagen:
            modo = "RGBA" if "A" in imagen.getbands() else "RGB"
            buffer = BytesIO()
            imagen.convert(modo).save(buffer, format="WEBP")
        return base64.b64encode(buffer.getvalue())
