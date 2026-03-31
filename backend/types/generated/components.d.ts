import type { Schema, Struct } from '@strapi/strapi';

export interface DestinosIconItem extends Struct.ComponentSchema {
  collectionName: 'components_destinos_icon_items';
  info: {
    description: 'Elemento visual de beneficios para la seccion introductoria';
    displayName: 'Icon Item';
  };
  attributes: {
    description: Schema.Attribute.String;
    icon: Schema.Attribute.Media<'images'>;
    iconAlt: Schema.Attribute.String;
    iconKey: Schema.Attribute.String;
    label: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface DestinosSharedIcon extends Struct.ComponentSchema {
  collectionName: 'components_destinos_shared_icons';
  info: {
    description: 'Icono compartido entre idiomas para destino detalle';
    displayName: 'Shared Icon';
  };
  attributes: {
    icon: Schema.Attribute.Media<'images'>;
    iconAlt: Schema.Attribute.String;
    iconKey: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface LegalTermsSection extends Struct.ComponentSchema {
  collectionName: 'components_legal_terms_sections';
  info: {
    description: 'Secci\u00F3n de t\u00E9rminos con t\u00EDtulo y texto';
    displayName: 'Terms Section';
  };
  attributes: {
    text: Schema.Attribute.RichText & Schema.Attribute.Required;
    title: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursDescriptionDetailItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_description_detail_items';
  info: {
    description: 'Bloque de texto expandido de la seccion descripcion';
    displayName: 'Description Detail Item';
  };
  attributes: {
    text: Schema.Attribute.Text & Schema.Attribute.Required;
    title: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursFaqItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_faq_items';
  info: {
    description: 'Pregunta y respuesta para FAQ del tour';
    displayName: 'FAQ Item';
  };
  attributes: {
    answer: Schema.Attribute.Text & Schema.Attribute.Required;
    question: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursFeaturedImageItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_featured_image_items';
  info: {
    description: 'Imagen para la seccion destacado';
    displayName: 'Featured Image Item';
  };
  attributes: {
    alt: Schema.Attribute.String;
    image: Schema.Attribute.Media<'images'> &
      Schema.Attribute.Required &
      Schema.Attribute.SetPluginOptions<{
        i18n: {
          localized: false;
        };
      }>;
  };
}

export interface ToursHighlightItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_highlight_items';
  info: {
    description: 'Item de beneficios del bloque principal del tour';
    displayName: 'Highlight Item';
  };
  attributes: {
    description: Schema.Attribute.Text;
    title: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursInclusionItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_inclusion_items';
  info: {
    description: 'Item para seccion incluido/no incluido';
    displayName: 'Inclusion Item';
  };
  attributes: {
    icon: Schema.Attribute.String;
    text: Schema.Attribute.Text & Schema.Attribute.Required;
  };
}

export interface ToursItineraryIncludeItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_itinerary_include_items';
  info: {
    description: 'Texto de incluye del item de itinerario';
    displayName: 'Itinerary Include Item';
  };
  attributes: {
    text: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursItineraryItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_itinerary_items';
  info: {
    description: 'Dia/actividad del itinerario detallado';
    displayName: 'Itinerary Item';
  };
  attributes: {
    description: Schema.Attribute.RichText;
    highlight: Schema.Attribute.Text;
    image: Schema.Attribute.Media<'images', true> &
      Schema.Attribute.SetPluginOptions<{
        i18n: {
          localized: false;
        };
      }>;
    imageAlt: Schema.Attribute.String;
    includes: Schema.Attribute.Component<'tours.itinerary-include-item', true>;
    optional: Schema.Attribute.Text;
    title: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursReviewBrandItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_review_brand_items';
  info: {
    description: 'Marca de resenas para la banda de 5 estrellas';
    displayName: 'Review Brand Item';
  };
  attributes: {
    label: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface ToursScheduleItem extends Struct.ComponentSchema {
  collectionName: 'components_tours_schedule_items';
  info: {
    description: 'Bloque de horario/turno del tour';
    displayName: 'Schedule Item';
  };
  attributes: {
    content: Schema.Attribute.RichText & Schema.Attribute.Required;
    title: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

export interface TransportePrecioVehiculo extends Struct.ComponentSchema {
  collectionName: 'components_transporte_precio_vehiculos';
  info: {
    description: 'Precio de un veh\u00EDculo para una ruta de transporte';
    displayName: 'Precio Veh\u00EDculo';
  };
  attributes: {
    descuento: Schema.Attribute.Decimal &
      Schema.Attribute.SetMinMax<
        {
          min: 0;
        },
        number
      > &
      Schema.Attribute.DefaultTo<0>;
    precioAdulto: Schema.Attribute.Decimal &
      Schema.Attribute.Required &
      Schema.Attribute.SetMinMax<
        {
          min: 0;
        },
        number
      >;
    precioNino: Schema.Attribute.Decimal &
      Schema.Attribute.SetMinMax<
        {
          min: 0;
        },
        number
      >;
    vehiculo: Schema.Attribute.Relation<'manyToMany', 'api::vehiculo.vehiculo'>;
  };
}

declare module '@strapi/strapi' {
  export module Public {
    export interface ComponentSchemas {
      'destinos.icon-item': DestinosIconItem;
      'destinos.shared-icon': DestinosSharedIcon;
      'legal.terms-section': LegalTermsSection;
      'tours.description-detail-item': ToursDescriptionDetailItem;
      'tours.faq-item': ToursFaqItem;
      'tours.featured-image-item': ToursFeaturedImageItem;
      'tours.highlight-item': ToursHighlightItem;
      'tours.inclusion-item': ToursInclusionItem;
      'tours.itinerary-include-item': ToursItineraryIncludeItem;
      'tours.itinerary-item': ToursItineraryItem;
      'tours.review-brand-item': ToursReviewBrandItem;
      'tours.schedule-item': ToursScheduleItem;
      'transporte.precio-vehiculo': TransportePrecioVehiculo;
    }
  }
}
