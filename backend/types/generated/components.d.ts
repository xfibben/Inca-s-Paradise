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
    label: Schema.Attribute.String & Schema.Attribute.Required;
  };
}

declare module '@strapi/strapi' {
  export module Public {
    export interface ComponentSchemas {
      'destinos.icon-item': DestinosIconItem;
    }
  }
}
