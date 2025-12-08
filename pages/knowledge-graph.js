
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Dropdown } from '../components/ui';
import dynamic from 'next/dynamic';
import ProductHeader from '../components/ProductHeader';

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
  const [nodeTab, setNodeTab] = useState('summary');
  const [layoutMode, setLayoutMode] = useState('force');
  const [selectedFramework, setSelectedFramework] = useState('SOC 2');
  const [selectedPersona, setSelectedPersona] = useState('Compliance Officer');
  const [selectedTimeRange, setSelectedTimeRange] = useState('Last 7d');

  const kpiCards = [
    { label: 'Overall compliance', value: '92%', icon: 'shield-check', tone: 'success' },
    { label: 'Active graph nodes', value: '3.4k', icon: 'diagram-3', tone: 'info' },
    { label: 'Open issues', value: '6', icon: 'exclamation-triangle', tone: 'warning' },
    { label: 'Last audit', value: '2h ago', icon: 'clock-history', tone: 'secondary' }
  ];

  const regulatoryFilters = ['SOC 2', 'NIST', 'HIPAA'];
  const personaPresets = ['Compliance Officer', 'Procurement Lead', 'Researcher'];
  const timeRanges = ['Last 24h', 'Last 7d', 'Last 30d'];

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

      <ProductHeader
        title="Knowledge Graph Explorer"
        subtitle="Split-view navigation across force, honeycomb, and timeline layouts with compliance overlays"
        breadcrumbs={[{ label: 'Graph' }, { label: 'Explorer' }]}
        actions={[
          { label: 'Open chat', icon: 'chat-dots', href: '/chat' },
          { label: 'Compliance dashboard', icon: 'shield-check', href: '/compliance-dashboard' }
        ]}
      />

      <div className="glass-panel p-3 rounded-4 mb-3">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
          <div className="d-flex gap-2 flex-wrap">
            {kpiCards.map((kpi) => (
              <div key={kpi.label} className="metric-chip">
                <i className={`bi bi-${kpi.icon} me-1 text-${kpi.tone}`}></i>{kpi.label}: {kpi.value}
              </div>
            ))}
          </div>
          <div className="d-flex gap-2 flex-wrap">
            {['force', 'honeycomb', 'timeline'].map((layout) => (
              <button
                key={layout}
                className={`btn btn-sm rounded-pill ${layoutMode === layout ? 'btn-primary' : 'btn-outline-light'}`}
                onClick={() => setLayoutMode(layout)}
              >
                <i className={`bi bi-${layout === 'honeycomb' ? 'hexagon' : layout === 'timeline' ? 'clock-history' : 'diagram-3'} me-1`}></i>
                {layout.charAt(0).toUpperCase() + layout.slice(1)} view
              </button>
            ))}
          </div>
        </div>
      </div>

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
                <h6 className="mb-1">Filters</h6>
                <small className="text-white-50">Axis, persona, regulatory, and time</small>
              </div>
              <div className="p-3 border-bottom border-secondary">
                <p className="section-title mb-2">Axis</p>
                <div className="d-grid gap-2">
                  {axes.map(axis => (
                    <button
                      key={axis.id}
                      className={`btn btn-sm w-100 text-start ${activeAxis === axis.id ? 'btn-primary' : 'btn-outline-light'}`}
                      onClick={() => setActiveAxis(axis.id)}
                    >
                      <i className={`${axis.icon} me-2`}></i>{axis.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3 border-bottom border-secondary">
                <p className="section-title mb-2">Regulatory</p>
                <div className="d-grid gap-2">
                  {regulatoryFilters.map((filter) => (
                    <button
                      key={filter}
                      className={`btn btn-sm rounded-pill ${selectedFramework === filter ? 'btn-success' : 'btn-outline-light'}`}
                      onClick={() => setSelectedFramework(filter)}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3 border-bottom border-secondary">
                <p className="section-title mb-2">Personas</p>
                <div className="d-grid gap-2">
                  {personaPresets.map((persona) => (
                    <button
                      key={persona}
                      className={`btn btn-sm rounded-pill ${selectedPersona === persona ? 'btn-info' : 'btn-outline-light'}`}
                      onClick={() => setSelectedPersona(persona)}
                    >
                      <i className="bi bi-person-badge me-1"></i>{persona}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3">
                <p className="section-title mb-2">Time</p>
                <div className="d-grid gap-2">
                  {timeRanges.map((range) => (
                    <button
                      key={range}
                      className={`btn btn-sm rounded-pill ${selectedTimeRange === range ? 'btn-warning' : 'btn-outline-light'}`}
                      onClick={() => setSelectedTimeRange(range)}
                    >
                      <i className="bi bi-clock-history me-1"></i>{range}
                    </button>
                  ))}
                </div>
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
              <div className="p-3 border-bottom border-secondary">
                <div className="d-flex gap-2 flex-wrap">
                  {['Force', 'Honeycomb', 'Timeline'].map((layout) => (
                    <div key={layout} className={`glass-border p-2 rounded-3 ${layoutMode === layout.toLowerCase() ? 'border-primary' : ''}`} style={{ minWidth: '120px' }}>
                      <div className="d-flex align-items-center gap-2 mb-1">
                        <i className={`bi bi-${layout === 'Honeycomb' ? 'hexagon' : layout === 'Timeline' ? 'clock-history' : 'diagram-3'}`}></i>
                        <strong className="small mb-0">{layout}</strong>
                      </div>
                      <small className="text-white-50">Preview layout and transitions.</small>
                    </div>
                  ))}
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

                        <div className="d-flex gap-2 mb-3 flex-wrap">
                          {['summary', 'evidence', 'compliance'].map((tab) => (
                            <button
                              key={tab}
                              className={`btn btn-sm rounded-pill ${nodeTab === tab ? 'btn-primary' : 'btn-outline-light'}`}
                              onClick={() => setNodeTab(tab)}
                            >
                              {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                          ))}
                        </div>

                        {nodeTab === 'summary' && (
                          <p className="small text-muted">Quick synopsis of relationships, parent branches, and honeycomb overlays.</p>
                        )}
                        {nodeTab === 'evidence' && (
                          <ul className="small text-muted">
                            <li>Linked documents and provenance</li>
                            <li>Recent changes on timeline overlay</li>
                          </ul>
                        )}
                        {nodeTab === 'compliance' && (
                          <div className="d-grid gap-2">
                            <span className="badge bg-success">Aligned to {selectedFramework}</span>
                            <span className="badge bg-warning text-dark">2 open issues</span>
                          </div>
                        )}

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
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h6 className="mb-0">Insights & hand-offs</h6>
                <span className="badge bg-primary bg-opacity-25 text-primary">Live</span>
              </div>
              <p className="text-white-50 small mb-2">Breadcrumb trail and quick pivots back to chat or exports.</p>
              <div className="d-flex flex-wrap gap-2 mb-3">
                <span className="pill"><i className="bi bi-diagram-3"></i> {activeAxis}</span>
                <span className="pill"><i className="bi bi-shield-lock"></i> {selectedFramework}</span>
                <span className="pill"><i className="bi bi-people"></i> {selectedPersona}</span>
              </div>
              <div className="d-grid gap-2">
                <Button variant="primary"><i className="bi bi-chat-dots me-2"></i>Send to chat</Button>
                <Button variant="outline"><i className="bi bi-file-earmark-text me-2"></i>Generate export</Button>
              </div>
            </div>

            <div className="glass-panel p-3">
              <h6 className="mb-2">Legend</h6>
              <div className="d-grid gap-2 small text-white-50">
                <div className="d-flex justify-content-between align-items-center">
                  <span><i className="bi bi-circle-fill text-success me-1"></i> Low risk</span>
                  <span className="badge bg-success">OK</span>
                </div>
                <div className="d-flex justify-content-between align-items-center">
                  <span><i className="bi bi-circle-fill text-warning me-1"></i> Needs review</span>
                  <span className="badge bg-warning text-dark">Watch</span>
                </div>
                <div className="d-flex justify-content-between align-items-center">
                  <span><i className="bi bi-circle-fill text-danger me-1"></i> Critical</span>
                  <span className="badge bg-danger">Act</span>
                </div>
              </div>
              <div className="mt-3">
                <h6 className="mb-1">Timeline</h6>
                <p className="text-white-50 small mb-2">Zoom controls and mini-map for temporal overlays.</p>
                <div className="d-flex gap-2">
                  <Button size="sm" variant="secondary"><i className="bi bi-zoom-in me-1"></i>Zoom</Button>
                  <Button size="sm" variant="secondary"><i className="bi bi-map me-1"></i>Mini-map</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
