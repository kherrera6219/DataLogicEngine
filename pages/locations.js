
import Head from 'next/head';
import Layout from '../components/Layout';
import LocationMap from '../components/ui/LocationMap';
import { useEffect, useState } from 'react';

export default function LocationsPage() {
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

      <div className="container-fluid mt-4 mb-5">
        {error ? (
          <div className="alert alert-danger">
            <i className="bi bi-exclamation-triangle me-2"></i>
            {error}
          </div>
        ) : isLoading ? (
          <div className="text-center my-5">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Loading location data...</p>
          </div>
        ) : (
          <LocationMap initialLocations={initialLocations} />
        )}
      </div>
    </Layout>
  );
}
