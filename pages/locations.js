import Head from 'next/head';
import Layout from '../components/Layout';
import LocationMap from '../components/ui/LocationMap';
import { useEffect, useState } from 'react';
import { Spinner } from '@fluentui/react-components';
import Text from '../components/ui/Text';
import { makeStyles } from '@fluentui/react-components';

const useStyles = makeStyles({
  page: {
    display: 'grid',
    gap: '24px',
  },
});

export default function LocationsPage() {
  const styles = useStyles();
  const [initialLocations, setInitialLocations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchInitialLocations() {
      try {
        const response = await fetch('/api/locations');
        const data = await response.json();

        if (data.success) {
          setInitialLocations(data.locations || []);
        } else {
          setError(data.error || 'Failed to fetch locations');
        }
      } catch (err) {
        setError('Error loading locations: ' + err.message);
      } finally {
        setIsLoading(false);
      }
    }

    fetchInitialLocations();
  }, []);

  return (
    <Layout>
      <Head>
        <title>UKG - Location Management (Axis 12)</title>
        <meta name="description" content="Universal Knowledge Graph Location Management" />
      </Head>

      <div className={styles.page}>
        <div>
          <Text fontSize="3xl" fontWeight="bold">
            Location intelligence (Axis 12)
          </Text>
          <Text color="muted">
            Monitor global coverage, regional readiness, and operational telemetry across all registered locations.
          </Text>
        </div>

        {error ? (
          <Text color="danger">{error}</Text>
        ) : isLoading ? (
          <Spinner size="large" label="Loading location data" />
        ) : (
          <LocationMap initialLocations={initialLocations} />
        )}
      </div>
    </Layout>
  );
}
