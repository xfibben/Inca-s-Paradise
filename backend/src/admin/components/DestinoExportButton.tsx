import { Button } from '@strapi/design-system';
import { Download } from '@strapi/icons';
import { useIntl } from 'react-intl';
import { useParams } from 'react-router-dom';

const DESTINO_MODEL_UID = 'api::destino-detalle.destino-detalle';
const DEFAULT_STATUS = 'published';

export const DestinoExportButton = () => {
  const { formatMessage } = useIntl();
  const { slug } = useParams();

  if (slug !== DESTINO_MODEL_UID) {
    return null;
  }

  const handleExport = () => {
    const params = new URLSearchParams({
      format: 'odoo',
      status: DEFAULT_STATUS,
    });

    window.open(`/api/destino-detalles/export-csv?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <Button variant="secondary" startIcon={<Download />} onClick={handleExport}>
      {formatMessage({
        id: 'destino-detalle.export.csv',
        defaultMessage: 'Exportar destinos CSV',
      })}
    </Button>
  );
};
