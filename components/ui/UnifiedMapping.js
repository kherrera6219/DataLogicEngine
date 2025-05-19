
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Table, Alert, Badge } from 'react-bootstrap';

const UnifiedMapping = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchType, setSearchType] = useState('nuremberg');
  const [searchValue, setSearchValue] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  
  // Coordinate search state
  const [coordinates, setCoordinates] = useState(Array(13).fill(0));
  const [distanceThreshold, setDistanceThreshold] = useState(0.2);
  
  // Fetch system status on load
  useEffect(() => {
    fetchSystemStatus();
  }, []);
  
  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/unified/status');
      const data = await response.json();
      setSystemStatus(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch system status');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleCoordinateChange = (index, value) => {
    const newCoordinates = [...coordinates];
    newCoordinates[index] = parseFloat(value) || 0;
    setCoordinates(newCoordinates);
  };
  
  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      let response;
      
      if (searchType === 'coordinates') {
        response = await fetch('/api/unified/coordinates', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            coordinates,
            distance_threshold: distanceThreshold
          }),
        });
        
        const data = await response.json();
        if (data.status === 'success') {
          setSearchResults(data.nearby_nodes || []);
        } else {
          setError(data.message || 'Search failed');
        }
      } else if (searchType === 'nuremberg') {
        response = await fetch(`/api/unified/nuremberg/${searchValue}`);
        const data = await response.json();
        
        if (data.status === 'success') {
          setSearchResults(data.nodes || []);
        } else {
          setError(data.message || 'Search failed');
        }
      } else if (searchType === 'samgov') {
        response = await fetch(`/api/unified/samgov/${searchValue}`);
        const data = await response.json();
        
        if (data.status === 'success') {
          setSearchResults(data.nodes || []);
        } else {
          setError(data.message || 'Search failed');
        }
      }
    } catch (err) {
      setError('Search failed: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container className="mt-4">
      <h1 className="mb-4">Unified Mapping System</h1>
      <p className="lead">
        13D coordinate system for precise data localization using Nuremberg numbering
        and SAM.gov naming conventions with NASA space mapping inspiration.
      </p>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header as="h5">System Status</Card.Header>
            <Card.Body>
              {loading && !systemStatus ? (
                <p>Loading system status...</p>
              ) : systemStatus ? (
                <>
                  <p>
                    <strong>Status:</strong>{' '}
                    <Badge bg={systemStatus.system_status === 'active' ? 'success' : 'warning'}>
                      {systemStatus.system_status}
                    </Badge>
                  </p>
                  
                  {systemStatus.node_stats && (
                    <div>
                      <h6>Node Statistics</h6>
                      <ul>
                        <li>Total Nodes: {systemStatus.node_stats.total_nodes}</li>
                        <li>Nuremberg Mapped: {systemStatus.node_stats.nuremberg_mapped_nodes}</li>
                        <li>SAM.gov Mapped: {systemStatus.node_stats.samgov_mapped_nodes}</li>
                        <li>Coordinate Mapped: {systemStatus.node_stats.coordinates_mapped_nodes}</li>
                      </ul>
                    </div>
                  )}
                  
                  <p className="mt-2 mb-0 text-muted small">
                    Last updated: {new Date(systemStatus.timestamp).toLocaleString()}
                  </p>
                </>
              ) : (
                <p>No system status available</p>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card>
            <Card.Header as="h5">Search Options</Card.Header>
            <Card.Body>
              <Form onSubmit={handleSearch}>
                <Form.Group className="mb-3">
                  <Form.Label>Search Type</Form.Label>
                  <Form.Select 
                    value={searchType} 
                    onChange={(e) => setSearchType(e.target.value)}
                  >
                    <option value="nuremberg">Nuremberg Code</option>
                    <option value="samgov">SAM.gov Name</option>
                    <option value="coordinates">13D Coordinates</option>
                  </Form.Select>
                </Form.Group>
                
                {searchType !== 'coordinates' ? (
                  <Form.Group className="mb-3">
                    <Form.Label>
                      {searchType === 'nuremberg' ? 'Nuremberg Code' : 'SAM.gov Name'}
                    </Form.Label>
                    <Form.Control
                      type="text"
                      value={searchValue}
                      onChange={(e) => setSearchValue(e.target.value)}
                      placeholder={searchType === 'nuremberg' ? '100-1234' : 'KNW_PillarLevel'}
                    />
                  </Form.Group>
                ) : (
                  <>
                    <Form.Group className="mb-3">
                      <Form.Label>13D Coordinates</Form.Label>
                      <Row>
                        {coordinates.map((coord, index) => (
                          <Col md={4} key={index} className="mb-2">
                            <Form.Label className="small">Axis {index + 1}</Form.Label>
                            <Form.Control
                              type="number"
                              step="0.1"
                              min="-1"
                              max="1"
                              value={coord}
                              onChange={(e) => handleCoordinateChange(index, e.target.value)}
                            />
                          </Col>
                        ))}
                      </Row>
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Distance Threshold</Form.Label>
                      <Form.Control
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="1.0"
                        value={distanceThreshold}
                        onChange={(e) => setDistanceThreshold(parseFloat(e.target.value) || 0.2)}
                      />
                    </Form.Group>
                  </>
                )}
                
                <Button variant="primary" type="submit" disabled={loading}>
                  {loading ? 'Searching...' : 'Search'}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Row>
        <Col>
          <Card>
            <Card.Header as="h5">Search Results</Card.Header>
            <Card.Body>
              {searchResults.length > 0 ? (
                <Table responsive striped>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Nuremberg Code</th>
                      <th>SAM.gov Name</th>
                      <th>Axis</th>
                      {searchType === 'coordinates' && <th>Distance</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((item, index) => {
                      // Handle the different result formats
                      const node = searchType === 'coordinates' ? item.node : item;
                      
                      return (
                        <tr key={index}>
                          <td>{node.id || node.uid || '-'}</td>
                          <td>{node.name || '-'}</td>
                          <td>{node.nuremberg_code || '-'}</td>
                          <td>{node.samgov_name || '-'}</td>
                          <td>{node.axis_number || '-'}</td>
                          {searchType === 'coordinates' && <td>{item.distance.toFixed(4)}</td>}
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              ) : (
                <p>No results found</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default UnifiedMapping;
