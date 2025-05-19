
import React from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import ContextualExpertWeb from '../components/ui/ContextualExpertWeb';

export default function ContextualExpertsPage() {
  return (
    <Layout>
      <Head>
        <title>Context Experts (Axis 11) - Universal Knowledge Graph</title>
        <meta name="description" content="Explore the contextual experts in the Universal Knowledge Graph system" />
      </Head>
      
      <div className="container mt-4 mb-5">
        <h1 className="mb-4">Contextual Experts (Axis 11)</h1>
        <p className="lead">
          Axis 11 represents expert personas with specialized contextual knowledge. 
          These experts embody real-world application contexts and provide specialized perspectives 
          based on their role, education, certifications, training, skills, tasks, and related roles.
        </p>
        
        <ContextualExpertWeb />
      </div>
    </Layout>
  );
}
