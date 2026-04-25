import json

from odoo import fields, models


class IncasCatalogoTour(models.Model):
    _name = "incas.catalogo.tour"
    _description = "Catálogo local de tours"
    _inherits = {"incas.servicio.catalogo": "servicio_id"}
    _order = "name"

    servicio_id = fields.Many2one("incas.servicio.catalogo", string="Servicio base", required=True, ondelete="cascade")
    destination_slug = fields.Char(string="Destination slug")
    destinos_data = fields.Text(string="Destinos")
    estilos_data = fields.Text(string="Estilos")
    meta_title = fields.Char(string="Meta title")
    meta_description = fields.Text(string="Meta description")
    seo_title = fields.Char(string="SEO title")
    seo_description = fields.Text(string="SEO description")
    seo_keywords = fields.Char(string="SEO keywords")
    seo_canonical_url = fields.Char(string="SEO canonical url")
    seo_no_index = fields.Boolean(string="SEO no index")
    og_title = fields.Char(string="OG title")
    og_description = fields.Text(string="OG description")
    og_image_data = fields.Text(string="OG image")
    twitter_title = fields.Char(string="Twitter title")
    twitter_description = fields.Text(string="Twitter description")
    twitter_image_data = fields.Text(string="Twitter image")
    hero_title = fields.Char(string="Hero title")
    hero_description = fields.Text(string="Hero description")
    hero_slide_images_data = fields.Text(string="Hero slide images")
    highlights_title = fields.Char(string="Highlights title")
    highlights_lead = fields.Text(string="Highlights lead")
    highlights_question = fields.Char(string="Highlights question")
    highlights_cta_label = fields.Char(string="Highlights CTA label")
    highlights_cta_url = fields.Char(string="Highlights CTA URL")
    highlights_items_data = fields.Text(string="Highlights items")
    featured_title = fields.Char(string="Featured title")
    featured_images_data = fields.Text(string="Featured images")
    itinerary_title = fields.Char(string="Itinerary title")
    itinerary_item_label = fields.Char(string="Itinerary item label")
    itinerary_expand_label = fields.Char(string="Itinerary expand label")
    itinerary_collapse_label = fields.Char(string="Itinerary collapse label")
    itinerary_items_data = fields.Text(string="Itinerary items")
    schedule_title = fields.Char(string="Schedule title")
    schedule_items_data = fields.Text(string="Schedule items")
    included_title = fields.Char(string="Included title")
    included_items_data = fields.Text(string="Included items")
    excluded_title = fields.Char(string="Excluded title")
    excluded_items_data = fields.Text(string="Excluded items")
    faq_title = fields.Char(string="FAQ title")
    faq_items_data = fields.Text(string="FAQ items")
    show_in_styles = fields.Boolean(string="Mostrar en styles")
    duration_days = fields.Integer(string="Duración en días")

    _sql_constraints = [
        ("incas_catalogo_tour_servicio_unique", "unique(servicio_id)", "El tour ya está vinculado a un servicio."),
    ]

    def action_sync_from_strapi(self):
        self.env["incas.servicio.catalogo"].sync_from_strapi()
        return True

    def _json_legible(self, valor):
        if not valor:
            return False
        return json.dumps(valor, ensure_ascii=False, indent=2)
