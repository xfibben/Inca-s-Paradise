import { Button } from '@strapi/design-system';
import { Download } from '@strapi/icons';
import { useIntl } from 'react-intl';
import { useParams } from 'react-router-dom';

const TOUR_MODEL_UID = 'api::tour-detalle.tour-detalle';
const DEFAULT_LOCALE = 'es-PE';
const DEFAULT_STATUS = 'published';

export const TourExportButton = () => {
  const { formatMessage } = useIntl();
  const { slug } = useParams();

  if (slug !== TOUR_MODEL_UID) {
    return null;
  }

  const handleExport = () => {
    const params = new URLSearchParams({
      locale: DEFAULT_LOCALE,
      status: DEFAULT_STATUS,
    });

    window.open(`/api/tour-detalles/export-csv?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <Button variant="secondary" startIcon={<Download />} onClick={handleExport}>
      {formatMessage({
        id: 'tour-detalle.export.csv',
        defaultMessage: 'Exportar CSV',
      })}
    </Button>
  );
};
