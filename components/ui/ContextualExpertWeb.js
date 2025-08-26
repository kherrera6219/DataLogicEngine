
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner, Alert, Nav, Tab, Accordion } from 'react-bootstrap';

const ContextualExpertWeb = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [experts, setExperts] = useState([]);
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [expertiseModel, setExpertiseModel] = useState(null);

  useEffect(() => {
    const fetchExperts = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/contextual/experts');
        const data = await response.json();

        if (data.success) {
          setExperts(data.experts);
          if (data.experts.length > 0) {
            setSelectedExpert(data.experts[0]);
            fetchExpertiseModel(data.experts[0].id);
          }
        } else {
          setError(data.error || 'Failed to fetch contextual experts');
        }
      } catch (err) {
        setError('Error fetching contextual experts: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchExperts();
  }, []);

  const fetchExpertiseModel = async (expertId) => {
    try {
      const response = await fetch(`/api/contextual/expertise-model/${expertId}`);
      const data = await response.json();
      
      if (data.success) {
        setExpertiseModel(data.expertise_model);
      } else {
        setError(data.error || 'Failed to fetch expertise model');
      }
    } catch (err) {
      setError('Error fetching expertise model: ' + err.message);
    }
  };

  const handleExpertSelect = (expert) => {
    setSelectedExpert(expert);
    fetchExpertiseModel(expert.id);
  };

  const renderExpertsMenu = () => {
    return (
      <Nav variant="pills" className="flex-column">
        {experts.map((expert) => (
          <Nav.Item key={expert.id}>
            <Nav.Link 
              active={selectedExpert && selectedExpert.id === expert.id}
              onClick={() => handleExpertSelect(expert)}
            >
              {expert.label}
            </Nav.Link>
          </Nav.Item>
        ))}
      </Nav>
    );
  };

  const renderExpertiseModel = () => {
    if (!expertiseModel) return null;

    return (
      <div className="expertise-model mt-3">
        <h4>7-Part Expertise Model</h4>
        
        <Accordion defaultActiveKey="0">
          <Accordion.Item eventKey="0">
            <Accordion.Header>Role</Accordion.Header>
            <Accordion.Body>
              <p>{expertiseModel.role}</p>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="1">
            <Accordion.Header>Formal Education</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.formal_education.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="2">
            <Accordion.Header>Industry & Corporate Certifications</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.certifications.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="3">
            <Accordion.Header>Job Training</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.job_training.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="4">
            <Accordion.Header>Skills</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.skills.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="5">
            <Accordion.Header>Related Tasks</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.related_tasks.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
          
          <Accordion.Item eventKey="6">
            <Accordion.Header>Related Roles</Accordion.Header>
            <Accordion.Body>
              <ul>
                {expertiseModel.related_roles.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Accordion.Body>
          </Accordion.Item>
        </Accordion>
      </div>
    );
  };

  const renderExpertDetails = () => {
    if (!selectedExpert) return null;

    return (
      <div className="expert-details">
        <h3>{selectedExpert.label}</h3>
        <p>{selectedExpert.description}</p>
        
        {renderExpertiseModel()}
        
        <div className="branch-structure mt-4">
          <h4>Branch Structure</h4>
          <p>The contextual expert hierarchy follows the branch pattern:</p>
          <ul>
            <li>Mega branches (4)</li>
            <li>Large branches (4 per mega)</li>
            <li>Medium branches (4 per large)</li>
            <li>Small branches (4 per medium)</li>
            <li>Granular branches (as needed)</li>
          </ul>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="text-center p-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        {error}
      </Alert>
    );
  }

  return (
    <div className="contextual-expert-web">
      <Card className="mb-4">
        <Card.Header>
          <h2>Contextual Expert Web (Axis 11)</h2>
          <p className="text-muted">
            Contextual experts provide specialized perspectives based on real-world application contexts.
            Each expert has a comprehensive 7-part expertise model.
          </p>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={4}>
              {renderExpertsMenu()}
            </Col>
            <Col md={8}>
              {renderExpertDetails()}
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
};

export default ContextualExpertWeb;
