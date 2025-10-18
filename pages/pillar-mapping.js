import React from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import PillarMapping from '../components/ui/PillarMapping';
import { Card, Text } from '../components/ui';
import { makeStyles, shorthands } from '@fluentui/react-components';

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
});

export default function PillarMappingPage() {
  const styles = useStyles();

  return (
    <Layout>
      <Head>
        <title>Pillar Level Mapping - UKG</title>
        <meta
          name="description"
          content="Dynamic mapping of knowledge pillars in the Universal Knowledge Graph"
        />
      </Head>

      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.badge}>Axis 1 &bull; Mapping studio</span>
          <Text as="h1" fontSize="3xl" fontWeight="semibold">
            Dynamic pillar mapping workspace
          </Text>
          <Text color="muted">
            Connect pillar levels with sector, method, compliance, and contextual dimensions to orchestrate
            intelligent crosswalks and impact analysis.
          </Text>
        </header>

        <Card appearance="subtle">
          <Card.Header
            header={<Text fontWeight="semibold">Knowledge pillar dynamic mapping</Text>}
            description="Select a pillar, enrich context, and generate AI-assisted mappings across the knowledge graph."
          />
          <Card.Body>
            <PillarMapping />
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}
