
import React from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import PillarMapping from '../components/ui/PillarMapping';

export default function PillarMappingPage() {
  return (
    <Layout>
      <Head>
        <title>Pillar Level Mapping - UKG</title>
        <meta name="description" content="Dynamic mapping of knowledge pillars in the Universal Knowledge Graph" />
      </Head>
      
      <div className="container-fluid py-4">
        <div className="row">
          <div className="col-12 mb-4">
            <div className="bg-dark p-4 rounded">
              <h2>Knowledge Pillar Dynamic Mapping</h2>
              <p className="lead">
                Explore and create dynamic mappings between knowledge pillars (Axis 1) 
                and other dimensions in the Universal Knowledge Graph.
              </p>
            </div>
          </div>
          
          <div className="col-12">
            <PillarMapping />
          </div>
        </div>
      </div>
    </Layout>
  );
}
