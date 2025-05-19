
import React from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import UnifiedMapping from '../components/ui/UnifiedMapping';

export default function UnifiedMappingPage() {
  return (
    <Layout>
      <Head>
        <title>Unified Mapping System - UKG</title>
        <meta name="description" content="13D coordinate system with Nuremberg numbering and SAM.gov naming conventions" />
      </Head>
      <UnifiedMapping />
    </Layout>
  );
}
