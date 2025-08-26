
import React, { useState, useEffect } from 'react';
import { Card, Button } from './index';

const RegulatoryOctopus = ({ frameworkUid, onNodeClick }) => {
  const [octopusData, setOctopusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState({});

  useEffect(() => {
    if (!frameworkUid) return;

    const fetchOctopusData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/regulatory/octopus/${frameworkUid}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch octopus data: ${response.statusText}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          setOctopusData(data.octopus);
        } else {
          setError(data.message || 'Failed to load regulatory octopus data');
        }
      } catch (err) {
        setError(err.message || 'An error occurred while fetching the octopus data');
        console.error('Error fetching octopus data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOctopusData();
  }, [frameworkUid]);

  const toggleExpandNode = (nodeId, level) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };
  
  const handleNodeClick = (node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  if (loading) {
    return <div className="text-center p-4"><div className="spinner-border" role="status"></div></div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (!octopusData) {
    return <div className="text-center p-4">No data available. Select a regulatory framework.</div>;
  }

  const renderRequirements = (requirements, parentId) => {
    if (!requirements || Object.keys(requirements).length === 0) {
      return <div className="text-muted">No requirements defined</div>;
    }

    return (
      <ul className="list-group mt-2">
        {Object.entries(requirements).map(([reqId, reqData]) => (
          <li 
            key={reqId} 
            className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
            onClick={() => handleNodeClick(reqData.requirement)}
          >
            <div>
              <div className="fw-bold">{reqData.requirement.label}</div>
              <div className="small text-muted">{reqData.requirement.description}</div>
              {reqData.requirement.criticality && (
                <span className={`badge bg-${reqData.requirement.criticality === 'high' ? 'danger' : 
                  reqData.requirement.criticality === 'medium' ? 'warning' : 'info'} me-1`}>
                  {reqData.requirement.criticality}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    );
  };

  const renderSmallFrameworks = (smallFrameworks, parentId) => {
    if (!smallFrameworks || Object.keys(smallFrameworks).length === 0) {
      return <div className="text-muted">No small frameworks defined</div>;
    }

    return (
      <div className="ms-3 mt-2">
        {Object.entries(smallFrameworks).map(([smallId, smallData]) => {
          const isExpanded = expandedNodes[smallId] === true;
          
          return (
            <Card key={smallId} className="mb-2 border-info">
              <Card.Header className="bg-light">
                <div 
                  className="d-flex justify-content-between align-items-center"
                  onClick={() => toggleExpandNode(smallId, 'small')}
                  style={{ cursor: 'pointer' }}
                >
                  <div>
                    <span className="text-primary">
                      <i className="bi bi-file-text me-2"></i>
                      {smallData.framework.label}
                    </span>
                  </div>
                  <div>
                    <span className="badge bg-info me-1">
                      {Object.keys(smallData.granular_requirements || {}).length} Reqs
                    </span>
                    <button className="btn btn-sm btn-outline-secondary">
                      <i className={`bi bi-chevron-${isExpanded ? 'up' : 'down'}`}></i>
                    </button>
                  </div>
                </div>
              </Card.Header>
              {isExpanded && (
                <Card.Body>
                  <small className="text-muted d-block mb-2">{smallData.framework.description}</small>
                  <h6 className="mt-3">Granular Requirements</h6>
                  {renderRequirements(smallData.granular_requirements, smallId)}
                </Card.Body>
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  const renderMediumFrameworks = (mediumFrameworks, parentId) => {
    if (!mediumFrameworks || Object.keys(mediumFrameworks).length === 0) {
      return <div className="text-muted">No medium frameworks defined</div>;
    }

    return (
      <div className="ms-3 mt-2">
        {Object.entries(mediumFrameworks).map(([mediumId, mediumData]) => {
          const isExpanded = expandedNodes[mediumId] === true;
          
          return (
            <Card key={mediumId} className="mb-3 border-primary">
              <Card.Header className="bg-light">
                <div 
                  className="d-flex justify-content-between align-items-center"
                  onClick={() => toggleExpandNode(mediumId, 'medium')}
                  style={{ cursor: 'pointer' }}
                >
                  <div>
                    <span className="text-primary">
                      <i className="bi bi-journal-text me-2"></i>
                      {mediumData.framework.label}
                    </span>
                  </div>
                  <div>
                    <span className="badge bg-primary me-1">
                      {Object.keys(mediumData.small_frameworks || {}).length} Small
                    </span>
                    <button className="btn btn-sm btn-outline-secondary">
                      <i className={`bi bi-chevron-${isExpanded ? 'up' : 'down'}`}></i>
                    </button>
                  </div>
                </div>
              </Card.Header>
              {isExpanded && (
                <Card.Body>
                  <small className="text-muted d-block mb-2">{mediumData.framework.description}</small>
                  <h6 className="mt-3">Small Frameworks</h6>
                  {renderSmallFrameworks(mediumData.small_frameworks, mediumId)}
                </Card.Body>
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  const renderLargeFrameworks = (largeFrameworks) => {
    if (!largeFrameworks || Object.keys(largeFrameworks).length === 0) {
      return <div className="text-muted">No large frameworks defined</div>;
    }

    return (
      <div className="mt-3">
        {Object.entries(largeFrameworks).map(([largeId, largeData]) => {
          const isExpanded = expandedNodes[largeId] === true;
          
          return (
            <Card key={largeId} className="mb-4 border-secondary">
              <Card.Header className="bg-light">
                <div 
                  className="d-flex justify-content-between align-items-center"
                  onClick={() => toggleExpandNode(largeId, 'large')}
                  style={{ cursor: 'pointer' }}
                >
                  <div>
                    <span className="text-secondary">
                      <i className="bi bi-journal-album me-2"></i>
                      {largeData.framework.label}
                    </span>
                  </div>
                  <div>
                    <span className="badge bg-secondary me-1">
                      {Object.keys(largeData.medium_frameworks || {}).length} Medium
                    </span>
                    <button className="btn btn-sm btn-outline-secondary">
                      <i className={`bi bi-chevron-${isExpanded ? 'up' : 'down'}`}></i>
                    </button>
                  </div>
                </div>
              </Card.Header>
              {isExpanded && (
                <Card.Body>
                  <div className="d-flex justify-content-between mb-3">
                    <div>
                      <small className="text-muted d-block">{largeData.framework.description}</small>
                      {largeData.framework.issuing_authority && (
                        <span className="badge bg-light text-dark me-1">
                          {largeData.framework.issuing_authority}
                        </span>
                      )}
                      {largeData.framework.effective_date && (
                        <span className="badge bg-light text-dark">
                          Effective: {new Date(largeData.framework.effective_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <div>
                      <Button size="sm" variant="outline-primary" onClick={() => handleNodeClick(largeData.framework)}>
                        View Details
                      </Button>
                    </div>
                  </div>
                  <h6 className="mt-3">Medium Frameworks</h6>
                  {renderMediumFrameworks(largeData.medium_frameworks, largeId)}
                </Card.Body>
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <div className="regulatory-octopus">
      <div className="mb-4">
        <h3 className="mb-3">
          <i className="bi bi-diagram-3 me-2"></i>
          {octopusData.mega_framework.label}
        </h3>
        <p className="text-muted">{octopusData.mega_framework.description}</p>
        <div className="d-flex mb-3">
          {octopusData.mega_framework.framework_type && (
            <span className="badge bg-dark me-2">
              Type: {octopusData.mega_framework.framework_type}
            </span>
          )}
          {octopusData.mega_framework.issuing_authority && (
            <span className="badge bg-dark me-2">
              Authority: {octopusData.mega_framework.issuing_authority}
            </span>
          )}
          {octopusData.mega_framework.effective_date && (
            <span className="badge bg-dark">
              Effective: {new Date(octopusData.mega_framework.effective_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
      
      <h5 className="mb-3">
        <i className="bi bi-diagram-2 me-2"></i>
        Large Frameworks
      </h5>
      {renderLargeFrameworks(octopusData.large_frameworks)}
    </div>
  );
};

export default RegulatoryOctopus;
