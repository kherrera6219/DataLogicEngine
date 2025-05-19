
import React, { useState } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button, Input, Dropdown, Textarea } from '../components/ui';
import dynamic from 'next/dynamic';

// Import RegulatoryOctopus component dynamically to avoid SSR issues
const RegulatoryOctopus = dynamic(() => import('../components/ui/RegulatoryOctopus'), {
  ssr: false,
  loading: () => <div className="text-center p-5">Loading regulatory visualization...</div>
});

export default function RegulatoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFramework, setSelectedFramework] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Simulated regulatory frameworks
  const frameworks = [
    { id: 'far', name: 'Federal Acquisition Regulation (FAR)', category: 'Federal', lastUpdated: '2025-01-15' },
    { id: 'dfars', name: 'Defense Federal Acquisition Regulation Supplement', category: 'Defense', lastUpdated: '2024-11-30' },
    { id: 'cfe', name: 'Code of Federal Ethics', category: 'Ethics', lastUpdated: '2024-09-22' },
    { id: 'itar', name: 'International Traffic in Arms Regulations', category: 'International', lastUpdated: '2024-10-05' },
    { id: 'cmmc', name: 'Cybersecurity Maturity Model Certification', category: 'Security', lastUpdated: '2025-02-20' },
    { id: 'sow', name: 'Statement of Work Guidelines', category: 'Contracts', lastUpdated: '2024-12-10' },
    { id: 'ndaa', name: 'National Defense Authorization Act', category: 'Defense', lastUpdated: '2025-01-02' },
  ];
  
  const filteredFrameworks = frameworks.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      <Head>
        <title>Regulatory Frameworks - UKG</title>
      </Head>
      
      <div className="container-fluid py-4">
        <div className="row mb-4">
          <div className="col-12">
            <Card>
              <Card.Header>
                <Card.Title>Regulatory Framework Explorer (Axis 6)</Card.Title>
              </Card.Header>
              <Card.Body>
                <p className="lead">
                  Navigate through regulatory frameworks, their interconnections, and compliance requirements within the Universal Knowledge Graph.
                </p>
                
                <div className="row mt-4">
                  <div className="col-md-4">
                    <div className="mb-3">
                      <Input
                        placeholder="Search frameworks..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        icon="bi-search"
                      />
                    </div>
                    
                    <div className="list-group" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                      {filteredFrameworks.map(framework => (
                        <button
                          key={framework.id}
                          className={`list-group-item list-group-item-action ${selectedFramework?.id === framework.id ? 'active' : ''}`}
                          onClick={() => setSelectedFramework(framework)}
                        >
                          <div className="d-flex w-100 justify-content-between">
                            <h6 className="mb-1">{framework.name}</h6>
                            <span className="badge bg-secondary">{framework.category}</span>
                          </div>
                          <small>Last updated: {framework.lastUpdated}</small>
                        </button>
                      ))}
                      
                      {filteredFrameworks.length === 0 && (
                        <div className="text-center p-3">
                          <i className="bi bi-search fs-4"></i>
                          <p className="mt-2">No frameworks found matching your search</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="col-md-8">
                    {selectedFramework ? (
                      <>
                        <div className="d-flex justify-content-between align-items-center mb-3">
                          <h4>{selectedFramework.name}</h4>
                          <Dropdown title="Actions">
                            <Dropdown.Item>
                              <i className="bi bi-download me-2"></i> Export Framework
                            </Dropdown.Item>
                            <Dropdown.Item>
                              <i className="bi bi-share me-2"></i> Share
                            </Dropdown.Item>
                            <Dropdown.Item>
                              <i className="bi bi-star me-2"></i> Add to Favorites
                            </Dropdown.Item>
                          </Dropdown>
                        </div>
                        
                        <div className="d-flex mb-4">
                          <span className="badge bg-secondary me-2">{selectedFramework.category}</span>
                          <span className="badge bg-info me-2">Last Updated: {selectedFramework.lastUpdated}</span>
                        </div>
                        
                        <ul className="nav nav-tabs mb-4">
                          <li className="nav-item">
                            <a 
                              className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`}
                              href="#"
                              onClick={(e) => { e.preventDefault(); setActiveTab('overview'); }}
                            >
                              Overview
                            </a>
                          </li>
                          <li className="nav-item">
                            <a 
                              className={`nav-link ${activeTab === 'sections' ? 'active' : ''}`}
                              href="#"
                              onClick={(e) => { e.preventDefault(); setActiveTab('sections'); }}
                            >
                              Sections
                            </a>
                          </li>
                          <li className="nav-item">
                            <a 
                              className={`nav-link ${activeTab === 'visualization' ? 'active' : ''}`}
                              href="#"
                              onClick={(e) => { e.preventDefault(); setActiveTab('visualization'); }}
                            >
                              Visualization
                            </a>
                          </li>
                          <li className="nav-item">
                            <a 
                              className={`nav-link ${activeTab === 'crosswalk' ? 'active' : ''}`}
                              href="#"
                              onClick={(e) => { e.preventDefault(); setActiveTab('crosswalk'); }}
                            >
                              Crosswalk
                            </a>
                          </li>
                        </ul>
                        
                        {activeTab === 'overview' && (
                          <div className="overview-tab">
                            <div className="card mb-3">
                              <div className="card-body">
                                <h5 className="card-title">Description</h5>
                                <p className="card-text">
                                  {selectedFramework.id === 'far' ? 
                                    'The Federal Acquisition Regulation (FAR) is the primary regulation for use by all executive agencies in their acquisition of supplies and services with appropriated funds.' :
                                    'This regulatory framework provides guidelines, regulations, and compliance requirements for government and industry operations.'}
                                </p>
                              </div>
                            </div>
                            
                            <div className="card mb-3">
                              <div className="card-body">
                                <h5 className="card-title">Key Information</h5>
                                <div className="row">
                                  <div className="col-md-6">
                                    <ul className="list-unstyled">
                                      <li><strong>ID:</strong> {selectedFramework.id.toUpperCase()}</li>
                                      <li><strong>Category:</strong> {selectedFramework.category}</li>
                                      <li><strong>Last Updated:</strong> {selectedFramework.lastUpdated}</li>
                                    </ul>
                                  </div>
                                  <div className="col-md-6">
                                    <ul className="list-unstyled">
                                      <li><strong>Authority:</strong> Federal Government</li>
                                      <li><strong>Enforcement:</strong> Mandatory</li>
                                      <li><strong>Version:</strong> 2025.1</li>
                                    </ul>
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            <div className="card">
                              <div className="card-body">
                                <h5 className="card-title">Related Frameworks</h5>
                                <div className="list-group list-group-flush">
                                  {frameworks.filter(f => f.id !== selectedFramework.id)
                                    .slice(0, 3)
                                    .map(framework => (
                                      <button 
                                        key={framework.id}
                                        className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                                        onClick={() => setSelectedFramework(framework)}
                                      >
                                        {framework.name}
                                        <span className="badge bg-secondary">{framework.category}</span>
                                      </button>
                                    ))
                                  }
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {activeTab === 'sections' && (
                          <div className="sections-tab">
                            <div className="accordion" id="sectionsAccordion">
                              <div className="accordion-item">
                                <h2 className="accordion-header" id="headingOne">
                                  <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                                    Part 1: General Information
                                  </button>
                                </h2>
                                <div id="collapseOne" className="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#sectionsAccordion">
                                  <div className="accordion-body">
                                    <p>This section provides general information about the regulatory framework, including purpose, scope, and definitions.</p>
                                    <ul className="list-group list-group-flush">
                                      <li className="list-group-item">1.1 Purpose</li>
                                      <li className="list-group-item">1.2 Scope</li>
                                      <li className="list-group-item">1.3 Definitions</li>
                                      <li className="list-group-item">1.4 Applicability</li>
                                    </ul>
                                  </div>
                                </div>
                              </div>
                              <div className="accordion-item">
                                <h2 className="accordion-header" id="headingTwo">
                                  <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                                    Part 2: Requirements
                                  </button>
                                </h2>
                                <div id="collapseTwo" className="accordion-collapse collapse" aria-labelledby="headingTwo" data-bs-parent="#sectionsAccordion">
                                  <div className="accordion-body">
                                    <p>This section outlines the specific requirements and regulations that must be followed.</p>
                                    <ul className="list-group list-group-flush">
                                      <li className="list-group-item">2.1 General Requirements</li>
                                      <li className="list-group-item">2.2 Technical Requirements</li>
                                      <li className="list-group-item">2.3 Documentation Requirements</li>
                                      <li className="list-group-item">2.4 Compliance Requirements</li>
                                    </ul>
                                  </div>
                                </div>
                              </div>
                              <div className="accordion-item">
                                <h2 className="accordion-header" id="headingThree">
                                  <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                                    Part 3: Procedures
                                  </button>
                                </h2>
                                <div id="collapseThree" className="accordion-collapse collapse" aria-labelledby="headingThree" data-bs-parent="#sectionsAccordion">
                                  <div className="accordion-body">
                                    <p>This section details the procedures for implementation and compliance.</p>
                                    <ul className="list-group list-group-flush">
                                      <li className="list-group-item">3.1 Implementation Procedures</li>
                                      <li className="list-group-item">3.2 Compliance Monitoring</li>
                                      <li className="list-group-item">3.3 Reporting Procedures</li>
                                      <li className="list-group-item">3.4 Audit Procedures</li>
                                    </ul>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {activeTab === 'visualization' && (
                          <div className="visualization-tab">
                            <div style={{ height: '500px', border: '1px solid #333', borderRadius: '4px' }}>
                              <RegulatoryOctopus 
                                framework={selectedFramework}
                                relatedFrameworks={frameworks.filter(f => f.id !== selectedFramework.id)} 
                              />
                            </div>
                            <div className="d-flex justify-content-center mt-3">
                              <Button size="sm" className="me-2">
                                <i className="bi bi-zoom-in me-1"></i> Zoom In
                              </Button>
                              <Button size="sm" className="me-2">
                                <i className="bi bi-zoom-out me-1"></i> Zoom Out
                              </Button>
                              <Button size="sm">
                                <i className="bi bi-arrow-counterclockwise me-1"></i> Reset
                              </Button>
                            </div>
                          </div>
                        )}
                        
                        {activeTab === 'crosswalk' && (
                          <div className="crosswalk-tab">
                            <p className="mb-3">
                              This section shows how this regulatory framework maps to other standards, frameworks, and axes in the Universal Knowledge Graph.
                            </p>
                            
                            <div className="table-responsive mb-4">
                              <table className="table table-bordered">
                                <thead>
                                  <tr>
                                    <th>Section</th>
                                    <th>Pillar (Axis 1)</th>
                                    <th>Method (Axis 9)</th>
                                    <th>Compliance (Axis 8)</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>Part 1.1</td>
                                    <td>P1.1.2 Acquisition Fundamentals</td>
                                    <td>M3.2 Regulatory Analysis</td>
                                    <td>C2.1 Documentation</td>
                                  </tr>
                                  <tr>
                                    <td>Part 1.3</td>
                                    <td>P1.2.1 Terminology</td>
                                    <td>M1.1 Definition Mapping</td>
                                    <td>C1.3 Term Alignment</td>
                                  </tr>
                                  <tr>
                                    <td>Part 2.2</td>
                                    <td>P2.3.1 Technical Standards</td>
                                    <td>M5.4 Technical Validation</td>
                                    <td>C3.5 Technical Verification</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                            
                            <Card>
                              <Card.Header>
                                <Card.Title>Create New Crosswalk Mapping</Card.Title>
                              </Card.Header>
                              <Card.Body>
                                <div className="row g-3">
                                  <div className="col-md-6">
                                    <label className="form-label">Section</label>
                                    <Input placeholder="Enter section number..." />
                                  </div>
                                  <div className="col-md-6">
                                    <label className="form-label">Destination Axis</label>
                                    <select className="form-select">
                                      <option>Pillar (Axis 1)</option>
                                      <option>Sector (Axis 2)</option>
                                      <option>Honeycomb (Axis 3)</option>
                                      <option>Compliance (Axis 8)</option>
                                      <option>Method (Axis 9)</option>
                                    </select>
                                  </div>
                                  <div className="col-12">
                                    <label className="form-label">Destination Element</label>
                                    <Input placeholder="Enter or search for element..." />
                                  </div>
                                  <div className="col-12">
                                    <label className="form-label">Mapping Notes</label>
                                    <Textarea rows="3" placeholder="Enter additional notes about this mapping..."></Textarea>
                                  </div>
                                  <div className="col-12">
                                    <Button>Create Mapping</Button>
                                  </div>
                                </div>
                              </Card.Body>
                            </Card>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="d-flex flex-column align-items-center justify-content-center" style={{ height: '500px' }}>
                        <i className="bi bi-book fs-1 text-secondary mb-3"></i>
                        <h5>Select a Regulatory Framework</h5>
                        <p className="text-muted">Choose a framework from the list to view detailed information and visualizations</p>
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
