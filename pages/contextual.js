import React from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { makeStyles } from '@fluentui/react-components';
import ContextualExpertWeb from '../components/ui/ContextualExpertWeb';
import Text from '../components/ui/Text';

const useStyles = makeStyles({
  page: {
    display: 'grid',
    gap: '24px',
  },
});

export default function ContextualExpertsPage() {
  const styles = useStyles();

  return (
    <Layout>
      <Head>
        <title>Context Experts (Axis 11) - Universal Knowledge Graph</title>
        <meta name="description" content="Explore the contextual experts in the Universal Knowledge Graph system" />
      </Head>

      <div className={styles.page}>
        <div>
          <Text fontSize="3xl" fontWeight="bold">
            Contextual experts (Axis 11)
          </Text>
          <Text color="muted">
            Personas representing situational awareness, education, certifications, and role-based decision making across the UKG.
          </Text>
        </div>

        <ContextualExpertWeb />
      </div>
    </Layout>
  );
}
