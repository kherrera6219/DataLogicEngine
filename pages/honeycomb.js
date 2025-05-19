import React, { useEffect, useRef, useState } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Card, Button } from '../components/ui';
// Import force-graph dynamically to avoid SSR issues
import dynamic from 'next/dynamic';

const ForceGraph = dynamic(() => import('force-graph'), {
  ssr: false
});

export default function HoneycombPage() {
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch graph data
    fetch('/api/graph_stats')
      .then(response => response.json())
      .then(data => {
        setGraphData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching graph data:', error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    // Initialize graph once data is loaded and component is mounted
    if (!loading && containerRef.current && typeof window !== 'undefined') {
      const Graph = ForceGraph();

      Graph(containerRef.current)
        .graphData(graphData)
        .nodeLabel('label')
        .nodeColor(node => node.color || '#1f77b4')
        .linkColor(link => link.color || '#999')
        .nodeRelSize(6)
        .linkWidth(1.5)
        .linkDirectionalArrowLength(3.5)
        .linkDirectionalArrowRelPos(1)
        .onNodeClick(node => {
          // Handle node click
          console.log('Clicked node:', node);
        });
    }
  }, [graphData, loading]);

  return (
    <Layout>
      <Head>
        <title>UKG - Honeycomb Graph</title>
      </Head>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Knowledge Honeycomb</h1>

        <Card className="mb-6 p-4">
          <h2 className="text-xl font-semibold mb-3">Honeycomb Graph Visualization</h2>
          <p className="mb-4">Explore the interconnected knowledge nodes in the Universal Knowledge Graph.</p>

          {loading ? (
            <div className="flex justify-center items-center h-96">
              <p>Loading graph data...</p>
            </div>
          ) : (
            <div 
              ref={containerRef} 
              className="w-full h-96 border rounded-lg"
              style={{ background: '#f8f9fa' }}
            />
          )}
        </Card>

        <Card className="p-4">
          <h2 className="text-xl font-semibold mb-3">Graph Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-lg font-medium mb-2">Nodes</h3>
              <p className="text-2xl font-bold">{graphData.nodes ? graphData.nodes.length : 0}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-medium mb-2">Connections</h3>
              <p className="text-2xl font-bold">{graphData.links ? graphData.links.length : 0}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="text-lg font-medium mb-2">Density</h3>
              <p className="text-2xl font-bold">
                {graphData.nodes && graphData.nodes.length > 0 
                  ? ((graphData.links ? graphData.links.length : 0) / graphData.nodes.length).toFixed(2) 
                  : '0'}
              </p>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
}