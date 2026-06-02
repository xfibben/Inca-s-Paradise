import { Button } from '@strapi/design-system';
import { Download } from '@strapi/icons';
import { useIntl } from 'react-intl';
import { useParams } from 'react-router-dom';

const MODEL_UID = 'api::cancelaciones.cancelaciones';
const DEFAULT_STATUS = 'published';

export const CancelacionesExportButton = () => {
  const { formatMessage } = useIntl();
  const { slug } = useParams();

  if (slug !== MODEL_UID) {
    return null;
  }

  const handleExport = () => {
    const params = new URLSearchParams({
      status: DEFAULT_STATUS,
    });

    window.open(`/api/cancelaciones/export-csv?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <Button variant="secondary" startIcon={<Download />} onClick={handleExport}>
      {formatMessage({
        id: 'cancelaciones.export.csv',
        defaultMessage: 'Exportar CSV',
      })}
    </Button>
  );
};
