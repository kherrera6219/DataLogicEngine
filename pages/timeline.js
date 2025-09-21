import Head from 'next/head';
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import Timeline from '../components/ui/Timeline';
import { makeStyles, TabList, Tab, Spinner } from '@fluentui/react-components';
import Text from '../components/ui/Text';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const useStyles = makeStyles({
  page: {
    display: 'grid',
    gap: '24px',
  },
  controlRow: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
});

export default function TimelinePage() {
  const styles = useStyles();
  const [activeTab, setActiveTab] = useState('historical');
  const [historicalData, setHistoricalData] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [careerData, setCareerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [projectId, setProjectId] = useState('PROJ_UKG_IMPL');
  const [personaId, setPersonaId] = useState('PERSONA_KNOWLEDGE_EXPERT_PL2_SE');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const historicalResponse = await fetch('/api/time/historical');
        const historicalJson = await historicalResponse.json();
        if (historicalJson.success) {
          setHistoricalData(historicalJson.periods || []);
        }

        const projectResponse = await fetch(`/api/time/project/${projectId}`);
        const projectJson = await projectResponse.json();
        if (projectJson.success) {
          setProjectData({
            project: projectJson.project,
            tasks: projectJson.tasks || [],
            milestones: projectJson.milestones || [],
            completionPercentage: projectJson.completion_percentage || 0,
          });
        }

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

    fetchData();
  }, [projectId, personaId]);

  const handleProjectSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`/api/time/project/${projectId}`);
      const data = await response.json();
      if (data.success) {
        setProjectData({
          project: data.project,
          tasks: data.tasks || [],
          milestones: data.milestones || [],
          completionPercentage: data.completion_percentage || 0,
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

  const handlePersonaSubmit = async (event) => {
    event.preventDefault();
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

      <div className={styles.page}>
        <div>
          <Text fontSize="3xl" fontWeight="bold">
            Time intelligence (Axis 13)
          </Text>
          <Text color="muted">
            Explore historical context, persona career growth, and programme delivery schedules powered by the UKG.
          </Text>
        </div>

        {error && <Text color="danger">{error}</Text>}

        <TabList selectedValue={activeTab} onTabSelect={(event, data) => setActiveTab(data.value)}>
          <Tab value="historical">Historical</Tab>
          <Tab value="career">Career</Tab>
          <Tab value="project">Projects</Tab>
        </TabList>

        {loading && <Spinner size="medium" label="Refreshing timeline data" />}

        {activeTab === 'historical' && historicalData && <Timeline initialData={historicalData} timelineType="historical" />}

        {activeTab === 'career' && (
          <Card>
            <Card.Body>
              <form onSubmit={handlePersonaSubmit} className={styles.controlRow}>
                <Input
                  placeholder="Persona ID"
                  value={personaId}
                  onChange={(event, data) => setPersonaId(data.value)}
                  style={{ minWidth: '280px' }}
                />
                <Button type="submit" variant="primary">
                  Load persona timeline
                </Button>
              </form>
              {careerData && <Timeline timelineType="career" careerData={careerData} />}
            </Card.Body>
          </Card>
        )}

        {activeTab === 'project' && (
          <Card>
            <Card.Body>
              <form onSubmit={handleProjectSubmit} className={styles.controlRow}>
                <Input
                  placeholder="Project ID"
                  value={projectId}
                  onChange={(event, data) => setProjectId(data.value)}
                  style={{ minWidth: '280px' }}
                />
                <Button type="submit" variant="primary">
                  Load project plan
                </Button>
              </form>
              {projectData && <Timeline timelineType="project" projectData={projectData} />}
            </Card.Body>
          </Card>
        )}
      </div>
    </Layout>
  );
}
