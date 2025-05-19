
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Dropdown } from '../components/ui';
import dynamic from 'next/dynamic';

// Import force-graph dynamically to avoid SSR issues
const ForceGraph = dynamic(() => import('../components/ui/HoneycombGraph'), {
  ssr: false,
  loading: () => <div className="text-center p-5">Loading graph visualization...</div>
});

export default function KnowledgeGraphExplorer() {
  const [activeAxis, setActiveAxis] = useState('pillar');
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  // Simulated axes for the sidebar
  const axes = [
    { id: 'pillar', name: 'Pillar Levels (Axis 1)', icon: 'bi-stack' },
    { id: 'sector', name: 'Sectors of Industry (Axis 2)', icon: 'bi-building' },
    { id: 'honeycomb', name: 'Honeycomb (Axis 3)', icon: 'bi-hexagon' },
    { id: 'branch', name: 'Branch (Axis 4)', icon: 'bi-diagram-3' },
    { id: 'node', name: 'Node (Axis 5)', icon: 'bi-circle' },
    { id: 'expert', name: 'Expert Role (Axis 6)', icon: 'bi-person-badge' },
    { id: 'regulatory', name: 'Regulatory (Axis 7)', icon: 'bi-shield' },
    { id: 'compliance', name: 'Compliance (Axis 8)', icon: 'bi-check-circle' },
    { id: 'method', name: 'Method (Axis 9)', icon: 'bi-gear' },
    { id: 'topic', name: 'Topic (Axis 10)', icon: 'bi-bookmark' },
    { id: 'context', name: 'Context (Axis 11)', icon: 'bi-layers' },
    { id: 'location', name: 'Location (Axis 12)', icon: 'bi-geo-alt' },
    { id: 'time', name: 'Time (Axis 13)', icon: 'bi-clock' },
  ];

  useEffect(() => {
    // Fetch graph data based on selected axis
    const fetchGraphData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/graph_data?axis=${activeAxis}`);
        if (response.ok) {
          const data = await response.json();
          setGraphData(data);
        } else {
          console.error('Failed to fetch graph data');
          // Use mock data for demo
          setGraphData({
            nodes: Array.from({ length: 30 }, (_, i) => ({
              id: `node-${i}`,
              name: `Node ${i}`,
              group: Math.floor(i / 5),
              value: 10 + Math.random() * 20
            })),
            links: Array.from({ length: 40 }, (_, i) => ({
              source: `node-${Math.floor(Math.random() * 30)}`,
              target: `node-${Math.floor(Math.random() * 30)}`,
              value: 1 + Math.random() * 5
            }))
          });
        }
      } catch (error) {
        console.error('Error fetching graph data:', error);
        // Use mock data for demo
        setGraphData({
          nodes: Array.from({ length: 30 }, (_, i) => ({
            id: `node-${i}`,
            name: `Node ${i}`,
            group: Math.floor(i / 5),
            value: 10 + Math.random() * 20
          })),
          links: Array.from({ length: 40 }, (_, i) => ({
            source: `node-${Math.floor(Math.random() * 30)}`,
            target: `node-${Math.floor(Math.random() * 30)}`,
            value: 1 + Math.random() * 5
          }))
        });
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [activeAxis]);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  return (
    <Layout>
      <Head>
        <title>Knowledge Graph Explorer - UKG</title>
      </Head>
      
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Left Sidebar - Axis Selector */}
          <div className="col-md-3 col-lg-2 bg-dark border-end border-secondary p-0">
            <div className="p-3 border-bottom border-secondary">
              <h5 className="mb-0">13-Axis Selector</h5>
            </div>
            <div className="axis-list overflow-auto" style={{ maxHeight: 'calc(100vh - 120px)' }}>
              {axes.map(axis => (
                <div 
                  key={axis.id}
                  className={`p-3 border-bottom border-secondary d-flex align-items-center cursor-pointer ${activeAxis === axis.id ? 'bg-primary bg-opacity-10' : ''}`}
                  onClick={() => setActiveAxis(axis.id)}
                >
                  <i className={`${axis.icon} me-2`}></i>
                  <div>{axis.name}</div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Main Content - Graph Visualization */}
          <div className="col-md-9 col-lg-10 p-0 d-flex flex-column">
            {/* Graph Controls */}
            <div className="p-3 border-bottom border-secondary d-flex justify-content-between align-items-center">
              <h4 className="mb-0">Universal Knowledge Graph Explorer - {axes.find(a => a.id === activeAxis)?.name}</h4>
              <div>
                <Button className="me-2" size="sm">
                  <i className="bi bi-zoom-in me-1"></i> Zoom In
                </Button>
                <Button className="me-2" size="sm">
                  <i className="bi bi-zoom-out me-1"></i> Zoom Out
                </Button>
                <Button size="sm">
                  <i className="bi bi-arrow-counterclockwise me-1"></i> Reset
                </Button>
              </div>
            </div>
            
            {/* Graph Visualization */}
            <div className="flex-grow-1 position-relative">
              {loading ? (
                <div className="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center">
                  <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              ) : (
                <ForceGraph 
                  graphData={graphData} 
                  onNodeClick={handleNodeClick}
                />
              )}
              
              {/* Node Context Panel */}
              {selectedNode && (
                <div className="position-absolute top-0 end-0 m-3" style={{ width: '300px', zIndex: 1000 }}>
                  <Card>
                    <Card.Header>
                      <div className="d-flex justify-content-between align-items-center">
                        <Card.Title className="mb-0">Node Details</Card.Title>
                        <Button 
                          variant="text" 
                          size="sm" 
                          onClick={() => setSelectedNode(null)}
                        >
                          <i className="bi bi-x-lg"></i>
                        </Button>
                      </div>
                    </Card.Header>
                    <Card.Body>
                      <h5>{selectedNode.name || selectedNode.id}</h5>
                      <p className="small text-muted">ID: {selectedNode.id}</p>
                      
                      <div className="d-grid gap-2 mt-3">
                        <Dropdown title="Node Actions" className="w-100">
                          <Dropdown.Item>
                            <i className="bi bi-person-fill me-2"></i> Simulate Expert
                          </Dropdown.Item>
                          <Dropdown.Item>
                            <i className="bi bi-search me-2"></i> Run Query
                          </Dropdown.Item>
                          <Dropdown.Item>
                            <i className="bi bi-hexagon-fill me-2"></i> Expand Honeycomb Crosswalk
                          </Dropdown.Item>
                        </Dropdown>
                      </div>
                    </Card.Body>
                  </Card>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
