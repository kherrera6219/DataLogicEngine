
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import PillarMapping from '../components/ui/PillarMapping';
import { Card, Button, Input, Text } from '../components/ui';

export default function PillarsPage() {
  const [pillars, setPillars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch all pillars
    const fetchPillars = async () => {
      try {
        const response = await fetch('/api/pillars/');
        if (response.ok) {
          const data = await response.json();
          setPillars(data);
        } else {
          setError('Failed to fetch pillars');
        }
      } catch (err) {
        setError(`Error fetching pillars: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchPillars();
  }, []);

  return (
    <Layout>
      <Head>
        <title>UKG - Knowledge Pillar System</title>
        <meta name="description" content="Universal Knowledge Graph Pillar Level Management" />
      </Head>

      <div className="container-fluid my-4">
        <div className="row">
          <div className="col-12">
            <h1 className="mb-4">Knowledge Pillar System (Axis 1)</h1>
            
            {error && (
              <div className="alert alert-danger">{error}</div>
            )}
            
            {loading ? (
              <div className="d-flex justify-content-center my-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              <>
                <Card className="mb-4">
                  <Card.Header>
                    <Card.Title>Pillar Levels Overview</Card.Title>
                  </Card.Header>
                  <Card.Body>
                    <div className="row">
                      {pillars.map(pillar => (
                        <div key={pillar.id} className="col-md-4 col-sm-6 mb-3">
                          <Card>
                            <Card.Body>
                              <div className="d-flex justify-content-between">
                                <h5 className="mb-1">{pillar.id}</h5>
                                <Button 
                                  size="sm" 
                                  variant="outline-primary"
                                  href={`/pillars?id=${pillar.id}`}
                                >
                                  Map
                                </Button>
                              </div>
                              <Text fontWeight="bold">{pillar.label || pillar.name}</Text>
                              <Text fontSize="sm">{pillar.description}</Text>
                              <Text fontSize="xs" className="text-muted mt-2">
                                Sublevels: {pillar.sublevels && Array.isArray(pillar.sublevels) ? 
                                  pillar.sublevels.length : 
                                  Object.keys(pillar.sublevels || {}).length || 0}
                              </Text>
                            </Card.Body>
                          </Card>
                        </div>
                      ))}
                    </div>
                  </Card.Body>
                </Card>
                
                <div className="my-5">
                  <h2 className="mb-4">Dynamic Pillar Mapping Engine</h2>
                  <PillarMapping initialPillarId={undefined} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
