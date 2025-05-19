
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import HoneycombGraph from '../components/ui/HoneycombGraph';
import { Card, Button, Input, Dropdown } from '../components/ui';

export default function HoneycombPage() {
  const [sectors, setSectors] = useState([]);
  const [pillars, setPillars] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [selectedNodeType, setSelectedNodeType] = useState('sector');
  const [honeycombData, setHoneycombData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maxConnections, setMaxConnections] = useState(30);

  useEffect(() => {
    // Fetch sectors and pillars on component mount
    fetchSectors();
    fetchPillars();
  }, []);

  const fetchSectors = async () => {
    try {
      const response = await fetch('/api/sectors');
      if (response.ok) {
        const data = await response.json();
        setSectors(data);
      }
    } catch (error) {
      console.error('Error fetching sectors:', error);
      setError('Failed to load sectors. Please try again.');
    }
  };

  const fetchPillars = async () => {
    try {
      const response = await fetch('/api/pillars');
      if (response.ok) {
        const data = await response.json();
        setPillars(data);
      }
    } catch (error) {
      console.error('Error fetching pillars:', error);
      setError('Failed to load pillars. Please try again.');
    }
  };

  const generateHoneycomb = async () => {
    if (!selectedNodeId) {
      setError('Please select a node first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/honeycomb/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_uid: selectedNodeId,
          max_connections: parseInt(maxConnections)
        })
      });

      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        setHoneycombData(data);
      } else {
        setError(data.message || 'Failed to generate honeycomb. Please try again.');
      }
    } catch (error) {
      console.error('Error generating honeycomb:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateSectorCrosswalk = async () => {
    if (!selectedNodeId) {
      setError('Please select a sector first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/honeycomb/sector-crosswalk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sector_id: selectedNodeId
        })
      });

      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        setHoneycombData(data);
      } else {
        setError(data.message || 'Failed to generate sector crosswalk. Please try again.');
      }
    } catch (error) {
      console.error('Error generating sector crosswalk:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeTypeChange = (e) => {
    setSelectedNodeType(e.target.value);
    setSelectedNodeId('');
  };

  return (
    <Layout>
      <Head>
        <title>Honeycomb System - UKG</title>
      </Head>

      <div className="container my-4">
        <h1 className="mb-4">Honeycomb System</h1>
        <p className="lead mb-4">
          The Honeycomb System enables multi-directional crosswalking between industry sectors,
          pillar levels, and other axes within the knowledge graph.
        </p>

        <div className="row mb-4">
          <div className="col-md-4">
            <Card>
              <Card.Header>
                <Card.Title>Generate Honeycomb</Card.Title>
              </Card.Header>
              <Card.Body>
                <div className="mb-3">
                  <label className="form-label">Node Type</label>
                  <select 
                    className="form-select" 
                    value={selectedNodeType} 
                    onChange={handleNodeTypeChange}
                  >
                    <option value="sector">Sector</option>
                    <option value="pillar">Pillar Level</option>
                  </select>
                </div>

                <div className="mb-3">
                  <label className="form-label">Select {selectedNodeType === 'sector' ? 'Sector' : 'Pillar Level'}</label>
                  <select 
                    className="form-select" 
                    value={selectedNodeId} 
                    onChange={(e) => setSelectedNodeId(e.target.value)}
                  >
                    <option value="">Select...</option>
                    {selectedNodeType === 'sector' 
                      ? sectors.map(sector => (
                          <option key={sector.id} value={sector.uid}>
                            {sector.name || sector.label}
                          </option>
                        ))
                      : pillars.map(pillar => (
                          <option key={pillar.id} value={pillar.uid}>
                            {pillar.name || pillar.pillar_id}
                          </option>
                        ))
                    }
                  </select>
                </div>

                <div className="mb-3">
                  <label className="form-label">Max Connections</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={maxConnections} 
                    onChange={(e) => setMaxConnections(e.target.value)}
                    min="5"
                    max="100"
                  />
                </div>

                <div className="d-grid gap-2">
                  <Button 
                    onClick={generateHoneycomb} 
                    disabled={loading || !selectedNodeId}
                    className="btn btn-primary"
                  >
                    {loading ? 'Generating...' : 'Generate Honeycomb'}
                  </Button>
                  
                  {selectedNodeType === 'sector' && (
                    <Button 
                      onClick={generateSectorCrosswalk} 
                      disabled={loading || !selectedNodeId}
                      className="btn btn-secondary"
                    >
                      {loading ? 'Processing...' : 'Generate Pillar Crosswalk'}
                    </Button>
                  )}
                </div>

                {error && (
                  <div className="alert alert-danger mt-3">
                    {error}
                  </div>
                )}
              </Card.Body>
            </Card>

            {honeycombData && (
              <Card className="mt-3">
                <Card.Header>
                  <Card.Title>Honeycomb Stats</Card.Title>
                </Card.Header>
                <Card.Body>
                  <p><strong>Center Node:</strong> {honeycombData.center_node?.name || honeycombData.sector?.name}</p>
                  <p><strong>Connections:</strong> {honeycombData.connection_count}</p>
                  <p><strong>Status:</strong> {honeycombData.status}</p>
                </Card.Body>
              </Card>
            )}
          </div>

          <div className="col-md-8">
            <Card>
              <Card.Header>
                <Card.Title>Honeycomb Visualization</Card.Title>
              </Card.Header>
              <Card.Body>
                <div className="honeycomb-visualization">
                  <HoneycombGraph 
                    data={honeycombData} 
                    centerNodeId={selectedNodeId}
                    width={700} 
                    height={500} 
                  />
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>

        {honeycombData && honeycombData.connections_created && honeycombData.connections_created.length > 0 && (
          <Card className="mt-4">
            <Card.Header>
              <Card.Title>Connection Details</Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>Target Node</th>
                      <th>Axis</th>
                      <th>Connection Type</th>
                      <th>Strength</th>
                    </tr>
                  </thead>
                  <tbody>
                    {honeycombData.connections_created.map((conn, index) => (
                      <tr key={index}>
                        <td>
                          {conn.target?.name || conn.target?.label || 
                           conn.pillar?.name || conn.pillar?.pillar_id || 
                           conn.sublevel?.name || conn.sublevel?.id || 'Unknown'}
                        </td>
                        <td>{conn.axis || conn.target?.axis_number || 'N/A'}</td>
                        <td>{conn.connection_type}</td>
                        <td>{typeof conn.strength === 'number' ? conn.strength.toFixed(2) : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card.Body>
          </Card>
        )}
      </div>
    </Layout>
  );
}
