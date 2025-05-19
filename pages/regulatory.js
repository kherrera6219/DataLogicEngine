
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import RegulatoryOctopus from '../components/ui/RegulatoryOctopus';
import { Card, Button } from '../components/ui';

export default function RegulatoryPage() {
  const [frameworks, setFrameworks] = useState([]);
  const [selectedFrameworkId, setSelectedFrameworkId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [nodeDetails, setNodeDetails] = useState(null);

  useEffect(() => {
    // Fetch mega regulatory frameworks on component mount
    fetchMegaFrameworks();
  }, []);

  const fetchMegaFrameworks = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/regulatory/frameworks?node_level=mega');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch frameworks: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setFrameworks(data.frameworks || []);
        if (data.frameworks && data.frameworks.length > 0) {
          setSelectedFrameworkId(data.frameworks[0].uid);
        }
      } else {
        setError(data.message || 'Failed to load regulatory frameworks');
      }
    } catch (err) {
      setError(err.message || 'An error occurred while fetching the frameworks');
      console.error('Error fetching frameworks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFrameworkChange = (e) => {
    setSelectedFrameworkId(e.target.value);
    setNodeDetails(null);
  };

  const handleNodeClick = (node) => {
    setNodeDetails(node);
  };

  const closeNodeDetails = () => {
    setNodeDetails(null);
  };

  return (
    <Layout>
      <Head>
        <title>Regulatory Frameworks - UKG</title>
      </Head>

      <div className="container my-4">
        <h1 className="mb-4">Regulatory Frameworks</h1>
        <p className="lead mb-4">
          The Regulatory Framework axis (Axis 6) manages regulatory frameworks, compliance requirements, 
          and legal structures with an octopus-style branch mapping.
        </p>

        <div className="row mb-4">
          <div className="col-md-4">
            <Card>
              <Card.Header>
                <Card.Title>Select Framework</Card.Title>
              </Card.Header>
              <Card.Body>
                {loading && <div className="text-center"><div className="spinner-border" role="status"></div></div>}
                
                {error && <div className="alert alert-danger">{error}</div>}
                
                {!loading && !error && (
                  <div className="mb-3">
                    <label className="form-label">Mega Framework</label>
                    <select 
                      className="form-select" 
                      value={selectedFrameworkId} 
                      onChange={handleFrameworkChange}
                    >
                      {frameworks.length === 0 && (
                        <option value="">No frameworks available</option>
                      )}
                      {frameworks.map((framework) => (
                        <option key={framework.uid} value={framework.uid}>
                          {framework.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="d-grid gap-2">
                  <Button variant="primary" onClick={fetchMegaFrameworks}>
                    Refresh Frameworks
                  </Button>
                </div>
              </Card.Body>
            </Card>

            {nodeDetails && (
              <Card className="mt-3">
                <Card.Header className="bg-info text-white">
                  <div className="d-flex justify-content-between align-items-center">
                    <Card.Title className="mb-0">Node Details</Card.Title>
                    <Button variant="close" onClick={closeNodeDetails} />
                  </div>
                </Card.Header>
                <Card.Body>
                  <h5>{nodeDetails.label}</h5>
                  <p className="text-muted">{nodeDetails.description}</p>
                  
                  <div className="mt-3">
                    <h6>Properties:</h6>
                    <ul className="list-group">
                      {nodeDetails.node_level && (
                        <li className="list-group-item d-flex justify-content-between">
                          <span>Level:</span>
                          <span className="badge bg-primary">{nodeDetails.node_level}</span>
                        </li>
                      )}
                      {nodeDetails.framework_type && (
                        <li className="list-group-item d-flex justify-content-between">
                          <span>Type:</span>
                          <span>{nodeDetails.framework_type}</span>
                        </li>
                      )}
                      {nodeDetails.issuing_authority && (
                        <li className="list-group-item d-flex justify-content-between">
                          <span>Authority:</span>
                          <span>{nodeDetails.issuing_authority}</span>
                        </li>
                      )}
                      {nodeDetails.effective_date && (
                        <li className="list-group-item d-flex justify-content-between">
                          <span>Effective Date:</span>
                          <span>{new Date(nodeDetails.effective_date).toLocaleDateString()}</span>
                        </li>
                      )}
                      {nodeDetails.criticality && (
                        <li className="list-group-item d-flex justify-content-between">
                          <span>Criticality:</span>
                          <span className={`badge bg-${
                            nodeDetails.criticality === 'high' ? 'danger' :
                            nodeDetails.criticality === 'medium' ? 'warning' : 'info'
                          }`}>
                            {nodeDetails.criticality}
                          </span>
                        </li>
                      )}
                    </ul>
                  </div>
                </Card.Body>
              </Card>
            )}
          </div>

          <div className="col-md-8">
            <Card>
              <Card.Header>
                <Card.Title>Octopus Structure</Card.Title>
              </Card.Header>
              <Card.Body>
                {selectedFrameworkId ? (
                  <RegulatoryOctopus 
                    frameworkUid={selectedFrameworkId}
                    onNodeClick={handleNodeClick}
                  />
                ) : (
                  <div className="text-center p-4">
                    Please select a regulatory framework
                  </div>
                )}
              </Card.Body>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}
