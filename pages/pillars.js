import { useEffect, useMemo, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';
import PillarMapping from '../components/ui/PillarMapping';
import { Card, Button, Text } from '../components/ui';
import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Spinner,
  makeStyles,
  shorthands,
} from '@fluentui/react-components';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    ...shorthands.padding('32px', '24px', '56px'),
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(117, 172, 242, 0.16)',
    color: '#9cc2f7',
    fontWeight: 600,
    ...shorthands.padding('4px', '12px'),
    borderRadius: '999px',
    letterSpacing: '0.04em',
  },
  grid: {
    display: 'grid',
    gap: '16px',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
  },
  loadingPanel: {
    minHeight: '220px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    flexDirection: 'column',
  },
});

export default function PillarsPage() {
  const styles = useStyles();
  const [pillars, setPillars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPillars = async () => {
      try {
        const response = await fetch('/api/pillars/');
        if (response.ok) {
          const data = await response.json();
          setPillars(data);
        } else {
          setError('Failed to fetch pillars');
        }
      } catch (err) {
        setError(`Error fetching pillars: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchPillars();
  }, []);

  const formattedPillars = useMemo(() => pillars ?? [], [pillars]);

  return (
    <Layout>
      <Head>
        <title>UKG - Knowledge Pillar System</title>
        <meta name="description" content="Universal Knowledge Graph Pillar Level Management" />
      </Head>

      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.badge}>Axis 1 &bull; Pillar levels</span>
          <Text as="h1" fontSize="3xl" fontWeight="semibold">
            Knowledge pillar intelligence
          </Text>
          <Text color="muted">
            Inspect foundational domain structures, understand sublevel coverage, and trigger dynamic mappings
            into adjacent Universal Knowledge Graph axes.
          </Text>
        </header>

        {error && (
          <MessageBar intent="error">
            <MessageBarBody>
              <MessageBarTitle>Pillar catalogue unavailable</MessageBarTitle>
              {error}
            </MessageBarBody>
          </MessageBar>
        )}

        {loading ? (
          <Card appearance="subtle">
            <div className={styles.loadingPanel}>
              <Spinner appearance="primary" size="large" />
              <Text color="muted">Loading Microsoft-aligned pillar definitions…</Text>
            </div>
          </Card>
        ) : (
          <Card appearance="subtle">
            <Card.Header
              header={<Text fontWeight="semibold">Pillar overview</Text>}
              description="Explore available pillar levels and open detailed mappings."
            />
            <Card.Body>
              <div className={styles.grid}>
                {formattedPillars.map((pillar) => (
                  <Card key={pillar.id} appearance="subtle">
                    <Card.Body>
                      <Text fontWeight="semibold">{pillar.id}</Text>
                      <Text>{pillar.label || pillar.name}</Text>
                      <Text fontSize="sm" color="muted" style={{ marginTop: '8px' }}>
                        {pillar.description}
                      </Text>
                      <Text fontSize="sm" color="muted" style={{ marginTop: '8px' }}>
                        Sublevels:{' '}
                        {pillar.sublevels && Array.isArray(pillar.sublevels)
                          ? pillar.sublevels.length
                          : Object.keys(pillar.sublevels || {}).length || 0}
                      </Text>
                      <Button
                        variant="outline"
                        style={{ marginTop: '12px' }}
                        as={Link}
                        href={`/pillars?id=${pillar.id}`}
                      >
                        Open mapping view
                      </Button>
                    </Card.Body>
                  </Card>
                ))}
              </div>
            </Card.Body>
          </Card>
        )}

        <Card appearance="subtle">
          <Card.Header
            header={<Text fontWeight="semibold">Dynamic pillar mapping engine</Text>}
            description="Orchestrate intelligent crosswalks between pillar levels and adjacent axes."
          />
          <Card.Body>
            <PillarMapping initialPillarId={undefined} />
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}
