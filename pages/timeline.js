
import Head from 'next/head';
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import Timeline from '../components/ui/Timeline';
import { Tab, Tabs, Form, Button, Card } from 'react-bootstrap';

export default function TimelinePage() {
  const [activeTab, setActiveTab] = useState('historical');
  const [historicalData, setHistoricalData] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [careerData, setCareerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projectId, setProjectId] = useState('PROJ_UKG_IMPL');
  const [personaId, setPersonaId] = useState('PERSONA_KNOWLEDGE_EXPERT_PL2_SE');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch historical periods
      const historicalResponse = await fetch('/api/time/historical');
      const historicalJson = await historicalResponse.json();
      
      if (historicalJson.success) {
        setHistoricalData(historicalJson.periods || []);
      }

      // Fetch project data for default project
      const projectResponse = await fetch(`/api/time/project/${projectId}`);
      const projectJson = await projectResponse.json();
      
      if (projectJson.success) {
        setProjectData({
          project: projectJson.project,
          tasks: projectJson.tasks || [],
          milestones: projectJson.milestones || [],
          completionPercentage: projectJson.completion_percentage || 0
        });
      }

      // Fetch career data for default persona
      const careerResponse = await fetch(`/api/time/career/${personaId}`);
      const careerJson = await careerResponse.json();
      
      if (careerJson.success) {
        setCareerData(careerJson.career_stages || []);
      }
    } catch (err) {
      setError(`Error fetching timeline data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectChange = async (e) => {
    e.preventDefault();
    
    setLoading(true);
    try {
      const response = await fetch(`/api/time/project/${projectId}`);
      const data = await response.json();
      
      if (data.success) {
        setProjectData({
          project: data.project,
          tasks: data.tasks || [],
          milestones: data.milestones || [],
          completionPercentage: data.completion_percentage || 0
        });
      } else {
        setError(data.error || 'Failed to fetch project data');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePersonaChange = async (e) => {
    e.preventDefault();
    
    setLoading(true);
    try {
      const response = await fetch(`/api/time/career/${personaId}`);
      const data = await response.json();
      
      if (data.success) {
        setCareerData(data.career_stages || []);
      } else {
        setError(data.error || 'Failed to fetch career data');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Head>
        <title>UKG - Timeline (Axis 13)</title>
        <meta name="description" content="Universal Knowledge Graph Timeline Management" />
      </Head>

      <div className="container-fluid mt-4 mb-5">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h1>Time Management (Axis 13)</h1>
        </div>

        {error && (
          <div className="alert alert-danger">
            <i className="bi bi-exclamation-triangle me-2"></i>
            {error}
          </div>
        )}

        <Tabs
          activeKey={activeTab}
          onSelect={(k) => setActiveTab(k)}
          className="mb-4"
        >
          <Tab eventKey="historical" title="Historical Timeline">
            {loading && !historicalData ? (
              <div className="text-center my-5">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2">Loading historical data...</p>
              </div>
            ) : (
              <Timeline 
                initialData={historicalData} 
                timelineType="historical" 
              />
            )}
          </Tab>

          <Tab eventKey="career" title="Career Timeline">
            <div className="mb-4">
              <Card className="mb-4">
                <Card.Body>
                  <Form onSubmit={handlePersonaChange} className="d-flex">
                    <Form.Group className="me-2 flex-grow-1">
                      <Form.Control
                        type="text"
                        placeholder="Enter Persona ID"
                        value={personaId}
                        onChange={(e) => setPersonaId(e.target.value)}
                      />
                    </Form.Group>
                    <Button type="submit" variant="primary">
                      Load Career
                    </Button>
                  </Form>
                </Card.Body>
              </Card>

              {loading && !careerData ? (
                <div className="text-center my-5">
                  <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mt-2">Loading career data...</p>
                </div>
              ) : (
                <Timeline 
                  initialData={careerData} 
                  timelineType="career" 
                />
              )}
            </div>
          </Tab>

          <Tab eventKey="project" title="Project Timeline">
            <div className="mb-4">
              <Card className="mb-4">
                <Card.Body>
                  <Form onSubmit={handleProjectChange} className="d-flex">
                    <Form.Group className="me-2 flex-grow-1">
                      <Form.Control
                        type="text"
                        placeholder="Enter Project ID"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                      />
                    </Form.Group>
                    <Button type="submit" variant="primary">
                      Load Project
                    </Button>
                  </Form>
                </Card.Body>
              </Card>

              {loading && !projectData ? (
                <div className="text-center my-5">
                  <div className="spinner-border" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <p className="mt-2">Loading project data...</p>
                </div>
              ) : (
                <Timeline 
                  initialData={projectData} 
                  timelineType="project" 
                />
              )}
            </div>
          </Tab>
        </Tabs>
      </div>
    </Layout>
  );
}
