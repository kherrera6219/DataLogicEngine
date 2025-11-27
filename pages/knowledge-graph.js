
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

  const kpiCards = [
    { label: 'Overall compliance', value: '92%', icon: 'shield-check', tone: 'success' },
    { label: 'Active graph nodes', value: '3.4k', icon: 'diagram-3', tone: 'info' },
    { label: 'Open issues', value: '6', icon: 'exclamation-triangle', tone: 'warning' },
    { label: 'Last audit', value: '2h ago', icon: 'clock-history', tone: 'secondary' }
  ];

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

      <section className="mesh-hero text-white p-4 rounded-4 mb-4">
        <div className="d-flex justify-content-between flex-wrap gap-3 align-items-start">
          <div>
            <p className="section-title mb-1">Knowledge Graph Explorer</p>
            <h2 className="mb-2">13-axis navigation + compliance dashboard</h2>
            <p className="mb-0 text-white-50">Switch between force-directed, honeycomb, spiderweb, and timeline layouts while tracking real-time compliance signals.</p>
          </div>
          <div className="d-flex gap-2 flex-wrap">
            <Button variant="primary">
              <i className="bi bi-chat-dots me-2"></i> Open chat copilot
            </Button>
            <Button variant="outline">
              <i className="bi bi-shield-check me-2"></i> Open compliance dashboard
            </Button>
          </div>
        </div>
        <div className="row row-cols-2 row-cols-md-4 g-3 mt-3">
          {kpiCards.map((kpi) => (
            <div key={kpi.label} className="col">
              <div className="glass-panel p-3 h-100">
                <div className="d-flex justify-content-between align-items-center">
                  <span className="text-white-50 small">{kpi.label}</span>
                  <i className={`bi bi-${kpi.icon} text-${kpi.tone}`}></i>
                </div>
                <h4 className="mb-0">{kpi.value}</h4>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="glass-panel p-3 mb-3">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
          <div className="d-flex gap-2 flex-wrap">
            <span className="pill"><i className="bi bi-diagram-3"></i> Axis: {axes.find(a => a.id === activeAxis)?.name}</span>
            <span className="pill"><i className="bi bi-clock-history"></i> Timeline overlay</span>
            <span className="pill"><i className="bi bi-hexagon"></i> Honeycomb crosswalk</span>
          </div>
          <div className="d-flex gap-2">
            <Button size="sm" variant="secondary"><i className="bi bi-zoom-in me-2"></i>Zoom in</Button>
            <Button size="sm" variant="secondary"><i className="bi bi-zoom-out me-2"></i>Zoom out</Button>
            <Button size="sm" variant="secondary"><i className="bi bi-arrow-counterclockwise me-2"></i>Reset</Button>
          </div>
        </div>
      </div>

      <div className="container-fluid h-100">
        <div className="row h-100 g-3">
          {/* Left Sidebar - Axis Selector */}
          <div className="col-md-3 col-lg-2">
            <div className="glass-panel h-100 overflow-auto" style={{ maxHeight: 'calc(100vh - 260px)' }}>
              <div className="p-3 border-bottom border-secondary">
                <h6 className="mb-0">13-Axis Selector</h6>
              </div>
              <div className="axis-list">
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
          </div>

          {/* Main Content - Graph Visualization */}
          <div className="col-md-9 col-lg-7 d-flex flex-column">
            <div className="glass-panel flex-grow-1 position-relative">
              <div className="p-3 border-bottom border-secondary d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Universal Knowledge Graph - {axes.find(a => a.id === activeAxis)?.name}</h5>
                <div className="d-flex gap-2">
                  <Button size="sm" variant="secondary">2D</Button>
                  <Button size="sm" variant="secondary">3D</Button>
                  <Button size="sm" variant="secondary">Heatmap</Button>
                </div>
              </div>
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

          <div className="col-lg-3 d-flex flex-column gap-3">
            <div className="glass-panel p-3">
              <h6 className="mb-2">Compliance pulse</h6>
              <p className="text-white-50 mb-2">Live metrics from SOC 2, regulatory spiderweb, and honeycomb overlays.</p>
              <div className="d-grid gap-2">
                <div className="d-flex justify-content-between"><span>Open issues</span><strong>6</strong></div>
                <div className="d-flex justify-content-between"><span>Critical</span><strong>2</strong></div>
                <div className="d-flex justify-content-between"><span>Pending exports</span><strong>4</strong></div>
                <Button variant="outline">
                  <i className="bi bi-file-earmark-arrow-down me-2"></i> Export SOC 2 report
                </Button>
              </div>
            </div>

            <div className="glass-panel p-3">
              <h6 className="mb-2">Timeline (Axis 13)</h6>
              <p className="text-white-50 small">Most recent changes in graph topology.</p>
              <ul className="list-unstyled small mb-0">
                <li className="mb-2"><i className="bi bi-clock-history me-2 text-primary"></i>Node fused in Healthcare sector</li>
                <li className="mb-2"><i className="bi bi-clock-history me-2 text-primary"></i>Compliance control updated for Axis 7</li>
                <li className="mb-0"><i className="bi bi-clock-history me-2 text-primary"></i>New honeycomb edge added</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
