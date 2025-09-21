import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { makeStyles, shorthands, Spinner } from '@fluentui/react-components';
import Card from '../components/ui/Card';
import Dropdown from '../components/ui/Dropdown';
import Text from '../components/ui/Text';

const useStyles = makeStyles({
  page: {
    display: 'grid',
    gap: '24px',
  },
  content: {
    display: 'grid',
    gridTemplateColumns: '320px 1fr',
    gap: '24px',
    '@media(max-width: 992px)': {
      gridTemplateColumns: '1fr',
    },
  },
  infoCard: {
    display: 'grid',
    gap: '12px',
  },
  list: {
    margin: 0,
    paddingLeft: '18px',
    lineHeight: 1.6,
  },
  message: {
    borderRadius: '16px',
    backgroundColor: 'rgba(117,172,242,0.12)',
    border: '1px solid rgba(117,172,242,0.25)',
    ...shorthands.padding('16px'),
  },
});

export default function CompliancePage() {
  const styles = useStyles();
  const [standardTypes, setStandardTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [standards, setStandards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStandard, setSelectedStandard] = useState(null);

  useEffect(() => {
    fetchStandardTypes();
  }, []);

  useEffect(() => {
    if (!selectedType) return;

    const fetchStandards = async (type) => {
      try {
        setLoading(true);
        const response = await fetch(`/api/compliance/standards?type=${type}`);
        const data = await response.json();

        if (data.status === 'success') {
          const standardsList = [];
          if (data.hierarchy) {
            Object.values(data.hierarchy).forEach((mega) => {
              standardsList.push(mega.standard);
              if (mega.large_standards) {
                Object.values(mega.large_standards).forEach((large) => {
                  standardsList.push(large.standard);
                });
              }
            });
          }

          setStandards(standardsList);
          if (standardsList.length > 0) {
            setSelectedStandard(standardsList[0].id);
          }
        } else {
          setError(data.message || 'Failed to load standards');
        }
      } catch (err) {
        setError(`Error fetching standards: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStandards(selectedType);
  }, [selectedType]);

  const fetchStandardTypes = async () => {
    try {
      setLoading(true);
      const types = [
        { id: 'iso', name: 'ISO Standards' },
        { id: 'nist', name: 'NIST Standards' },
        { id: 'pci', name: 'PCI Standards' },
        { id: 'hipaa', name: 'HIPAA Standards' },
        { id: 'gdpr', name: 'GDPR Standards' },
      ];
      setStandardTypes(types);
      setSelectedType(types[0].id);
    } catch (err) {
      setError(`Error fetching standard types: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Head>
        <title>Compliance Standards | UKG System</title>
      </Head>

      <div className={styles.page}>
        <div>
          <Text fontSize="3xl" fontWeight="bold">
            Compliance standards atlas
          </Text>
          <Text color="muted">
            Explore the spiderweb hierarchy aligning Microsoft enterprise controls with regulatory frameworks.
          </Text>
        </div>

        <div className={styles.content}>
          <Card>
            <Card.Body className={styles.infoCard}>
              <Text fontWeight="semibold">Filters</Text>
              <Dropdown
                placeholder="Select a standard type"
                options={standardTypes.map((type) => ({ value: type.id, label: type.name }))}
                value={selectedType}
                onChange={(value) => {
                  setSelectedType(value);
                  setSelectedStandard(null);
                }}
              />
              <Dropdown
                placeholder="Select a standard"
                options={standards.map((std) => ({ value: std.id, label: std.label }))}
                value={selectedStandard}
                onChange={(value) => setSelectedStandard(value)}
                disabled={loading || standards.length === 0}
              />

              <div className={styles.message}>
                <Text fontSize="sm" color="muted">
                  The spiderweb model organizes standards by Mega, Large, Medium, Small, and Granular nodes to map coverage across controls.
                </Text>
              </div>
            </Card.Body>
          </Card>

          <Card>
            <Card.Body>
              {loading ? (
                <Spinner size="large" label="Loading compliance data" />
              ) : error ? (
                <div className={styles.message}>
                  <Text color="danger">{error}</Text>
                </div>
              ) : selectedStandard ? (
                <div>
                  <Text fontWeight="semibold" fontSize="lg">
                    Spiderweb structure
                  </Text>
                  <Text fontSize="sm" color="muted">
                    Mega → Large → Medium → Small → Granular
                  </Text>
                  <div style={{ marginTop: '16px' }}>
                    <iframe
                      title="Compliance spiderweb"
                      src={`/api/compliance/spiderweb/${selectedStandard}`}
                      style={{ width: '100%', minHeight: '420px', border: 'none', borderRadius: '16px' }}
                    />
                  </div>
                </div>
              ) : (
                <div className={styles.message}>
                  <Text>Select a standard to view its spiderweb structure.</Text>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
