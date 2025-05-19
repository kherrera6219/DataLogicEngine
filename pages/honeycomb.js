
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Dropdown, Input, Label, Textarea } from '../components/ui';
import dynamic from 'next/dynamic';

// Import honeycomb component dynamically to avoid SSR issues
const HoneycombGraph = dynamic(() => import('../components/ui/HoneycombGraph'), {
  ssr: false,
  loading: () => <div className="text-center p-5">Loading honeycomb visualization...</div>
});

export default function HoneycombPage() {
  const [activeView, setActiveView] = useState('honeycomb');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedHoneycomb, setSelectedHoneycomb] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Simulated honeycomb patterns
  const honeycombPatterns = [
    { id: 'hc1', name: 'Federal Acquisition Regulation', count: 53 },
    { id: 'hc2', name: 'Defense Federal Acquisition Regulation', count: 42 },
    { id: 'hc3', name: 'Contract Performance', count: 38 },
    { id: 'hc4', name: 'Cost Accounting Standards', count: 27 },
    { id: 'hc5', name: 'Procurement Integrity', count: 31 },
  ];

  useEffect(() => {
    // Fetch graph data if a honeycomb is selected
    if (selectedHoneycomb) {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        // Mock data
        setGraphData({
          nodes: Array.from({ length: 20 }, (_, i) => ({
            id: `node-${i}`,
            name: `${selectedHoneycomb.name} Node ${i}`,
            group: Math.floor(i / 4),
            value: 5 + Math.random() * 15
          })),
          links: Array.from({ length: 30 }, (_, i) => ({
            source: `node-${Math.floor(Math.random() * 20)}`,
            target: `node-${Math.floor(Math.random() * 20)}`,
            value: 1 + Math.random() * 3
          }))
        });
        setLoading(false);
      }, 1000);
    }
  }, [selectedHoneycomb]);

  const filteredHoneycombs = honeycombPatterns.filter(h => 
    h.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      <Head>
        <title>Honeycomb Analysis - UKG</title>
      </Head>
      
      <div className="container-fluid py-4">
        <div className="row mb-4">
          <div className="col-12">
            <Card>
              <Card.Header>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title>Honeycomb Pattern Analysis</Card.Title>
                  <div>
                    <Button 
                      className={`me-2 ${activeView === 'honeycomb' ? 'active' : ''}`}
                      onClick={() => setActiveView('honeycomb')}
                    >
                      <i className="bi bi-hexagon me-1"></i> Honeycomb View
                    </Button>
                    <Button 
                      className={activeView === 'table' ? 'active' : ''}
                      onClick={() => setActiveView('table')}
                    >
                      <i className="bi bi-table me-1"></i> Table View
                    </Button>
                  </div>
                </div>
              </Card.Header>
              <Card.Body>
                <p className="lead">
                  Analyze honeycomb patterns in the 13-Axis Universal Knowledge Graph to identify relationships and insights.
                </p>
                
                <div className="row mt-4">
                  <div className="col-md-4">
                    <div className="mb-3">
                      <Label htmlFor="honeycombSearch">Search Honeycomb Patterns</Label>
                      <Input
                        id="honeycombSearch"
                        placeholder="Search by name or keyword..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                    
                    <div className="list-group honeycomb-list" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                      {filteredHoneycombs.map(honeycomb => (
                        <button
                          key={honeycomb.id}
                          className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center ${selectedHoneycomb?.id === honeycomb.id ? 'active' : ''}`}
                          onClick={() => setSelectedHoneycomb(honeycomb)}
                        >
                          <div>
                            <h6 className="mb-1">{honeycomb.name}</h6>
                            <small>Honeycomb ID: {honeycomb.id}</small>
                          </div>
                          <span className="badge bg-primary rounded-pill">{honeycomb.count}</span>
                        </button>
                      ))}
                      
                      {filteredHoneycombs.length === 0 && (
                        <div className="text-center p-3">
                          <i className="bi bi-search fs-4"></i>
                          <p className="mt-2">No honeycomb patterns found matching your search</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="col-md-8">
                    {selectedHoneycomb ? (
                      <div>
                        <h4>{selectedHoneycomb.name}</h4>
                        <div className="d-flex mb-3">
                          <span className="badge bg-info me-2">Axis 3: Honeycomb</span>
                          <span className="badge bg-secondary me-2">Nodes: {selectedHoneycomb.count}</span>
                          <Dropdown title="Actions" className="ms-auto">
                            <Dropdown.Item>
                              <i className="bi bi-download me-2"></i> Export Pattern
                            </Dropdown.Item>
                            <Dropdown.Item>
                              <i className="bi bi-share me-2"></i> Share Analysis
                            </Dropdown.Item>
                            <Dropdown.Item>
                              <i className="bi bi-plus-circle me-2"></i> Create New Pattern
                            </Dropdown.Item>
                          </Dropdown>
                        </div>
                        
                        {activeView === 'honeycomb' ? (
                          <div className="honeycomb-visualization" style={{ height: '400px', border: '1px solid #333', borderRadius: '4px', position: 'relative' }}>
                            {loading ? (
                              <div className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center">
                                <div className="spinner-border text-primary" role="status">
                                  <span className="visually-hidden">Loading...</span>
                                </div>
                              </div>
                            ) : (
                              <HoneycombGraph 
                                graphData={graphData}
                                honeycombMode={true}
                              />
                            )}
                          </div>
                        ) : (
                          <div className="table-responsive">
                            <table className="table table-hover">
                              <thead>
                                <tr>
                                  <th>Node ID</th>
                                  <th>Name</th>
                                  <th>Connections</th>
                                  <th>Category</th>
                                  <th>Actions</th>
                                </tr>
                              </thead>
                              <tbody>
                                {graphData && graphData.nodes.map((node, index) => (
                                  <tr key={node.id}>
                                    <td>{node.id}</td>
                                    <td>{node.name}</td>
                                    <td>{graphData.links.filter(l => l.source === node.id || l.target === node.id).length}</td>
                                    <td>Group {node.group}</td>
                                    <td>
                                      <Button size="sm" variant="link">View</Button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="d-flex flex-column align-items-center justify-content-center" style={{ height: '400px' }}>
                        <i className="bi bi-hexagon fs-1 text-secondary mb-3"></i>
                        <h5>Select a Honeycomb Pattern</h5>
                        <p className="text-muted">Choose a honeycomb pattern from the list to view its details and visualization</p>
                      </div>
                    )}
                  </div>
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
}
