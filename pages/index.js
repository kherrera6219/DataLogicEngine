
import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { marked } from 'marked';

export default function Home() {
  const [queryText, setQueryText] = useState('');
  const [confidenceValue, setConfidenceValue] = useState(0.85);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [graphStats, setGraphStats] = useState(null);
  const [memoryStats, setMemoryStats] = useState(null);

  useEffect(() => {
    // Fetch initial stats
    fetchGraphStats();
    fetchMemoryStats();
  }, []);

  const fetchGraphStats = async () => {
    try {
      const response = await fetch('/api/graph_stats');
      const data = await response.json();
      setGraphStats(data);
    } catch (error) {
      console.error('Error fetching graph stats:', error);
    }
  };

  const fetchMemoryStats = async () => {
    try {
      const response = await fetch('/api/memory_stats');
      const data = await response.json();
      setMemoryStats(data);
    } catch (error) {
      console.error('Error fetching memory stats:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!queryText.trim()) return;
    
    setIsLoading(true);
    setResult(null);
    
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: queryText,
          target_confidence: confidenceValue
        }),
      });
      
      const data = await response.json();
      setResult(data);
      
      // Refresh stats after query
      fetchGraphStats();
      fetchMemoryStats();
    } catch (error) {
      console.error('Error submitting query:', error);
      setResult({
        error: 'An error occurred while processing your query. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph (UKG) System</title>
      </Head>

      <div className="row">
        <div className="col-md-12 text-center mb-5">
          <h1>Universal Knowledge Graph System</h1>
          <p className="lead">A comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph</p>
        </div>
      </div>

      <div className="row mb-5">
        <div className="col-lg-8">
          <div className="card shadow-sm">
            <div className="card-header">
              <h3>Ask the UKG</h3>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="query-input" className="form-label">Enter your query:</label>
                  <textarea 
                    className="form-control" 
                    id="query-input" 
                    rows="3" 
                    placeholder="What would you like to know?" 
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    required
                  ></textarea>
                </div>
                <div className="mb-3">
                  <label htmlFor="confidence-slider" className="form-label">
                    Target Confidence: <span id="confidence-value">{confidenceValue}</span>
                  </label>
                  <input 
                    type="range" 
                    className="form-range" 
                    id="confidence-slider"
                    min="0.6" 
                    max="0.95" 
                    step="0.05" 
                    value={confidenceValue}
                    onChange={(e) => setConfidenceValue(parseFloat(e.target.value))}
                  />
                </div>
                <div className="d-grid">
                  <button type="submit" className="btn btn-primary" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        <span className="ms-2">Processing...</span>
                      </>
                    ) : (
                      'Submit Query'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {isLoading && (
            <div className="text-center my-4" id="loading-indicator">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Processing your query...</p>
            </div>
          )}

          {result && (
            <div className="card shadow-sm mt-4">
              <div className="card-header">
                <h3>Result</h3>
              </div>
              <div className="card-body">
                {result.error ? (
                  <div className="alert alert-danger">{result.error}</div>
                ) : (
                  <div 
                    id="result-content" 
                    className="markdown-content"
                    dangerouslySetInnerHTML={{ __html: marked.parse(result.response || '') }}
                  ></div>
                )}
              </div>
              {!result.error && (
                <div className="card-footer">
                  <small className="text-muted">
                    Confidence: {result.confidence || 'N/A'} | 
                    Processing Time: {result.processing_time_ms ? `${result.processing_time_ms}ms` : 'N/A'}
                  </small>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="col-lg-4">
          <div className="card shadow-sm">
            <div className="card-header">
              <h3>UKG System Status</h3>
            </div>
            <div className="card-body">
              <h5>Graph Statistics</h5>
              <div id="graph-stats">
                {graphStats ? (
                  <>
                    <p>Total Nodes: {graphStats.total_nodes}</p>
                    <p>Total Edges: {graphStats.total_edges}</p>
                    <p>Node Types: {Object.keys(graphStats.node_types || {}).length}</p>
                  </>
                ) : (
                  <p>Loading graph statistics...</p>
                )}
              </div>
              <hr />
              <h5>Memory Statistics</h5>
              <div id="memory-stats">
                {memoryStats ? (
                  <>
                    <p>Memory Entries: {memoryStats.total_entries || 0}</p>
                    <p>Active Sessions: {memoryStats.active_sessions || 0}</p>
                  </>
                ) : (
                  <p>Loading memory statistics...</p>
                )}
              </div>
            </div>
          </div>

          <div className="card shadow-sm mt-4">
            <div className="card-header">
              <h3>UKG Architecture</h3>
            </div>
            <div className="card-body">
              <h5>13 Axes of the UKG</h5>
              <ol>
                <li><strong>Pillar Levels</strong>: Knowledge domains and disciplines</li>
                <li><strong>Sectors</strong>: Industry sectors and markets</li>
                <li><strong>Topics</strong>: Subject matters and interests</li>
                <li><strong>Methods</strong>: Methodologies and approaches</li>
                <li><strong>Tools</strong>: Software, hardware, and tools</li>
                <li><strong>Regulatory Frameworks</strong>: Laws and regulations</li>
                <li><strong>Compliance Standards</strong>: Standards and requirements</li>
                <li><strong>Knowledge Experts</strong>: Domain expertise</li>
                <li><strong>Skill Experts</strong>: Practical skills</li>
                <li><strong>Role Experts</strong>: Professional roles</li>
                <li><strong>Context Experts</strong>: Situational contexts</li>
                <li><strong>Locations</strong>: Geographic and jurisdictional</li>
                <li><strong>Time</strong>: Temporal dimensions</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      <div className="row mb-5" id="about">
        <div className="col-md-12">
          <div className="card shadow-sm">
            <div className="card-header">
              <h3>About the UKG System</h3>
            </div>
            <div className="card-body">
              <p>The Universal Knowledge Graph (UKG) system is a comprehensive AI knowledge framework that organizes information along 13 distinct axes, creating a multidimensional representation of knowledge and expertise.</p>
              
              <h4>Key Components</h4>
              <ul>
                <li><strong>Graph Manager</strong>: Maintains the structure and relationships in the UKG.</li>
                <li><strong>Structured Memory Manager</strong>: Stores and retrieves detailed simulation states and knowledge.</li>
                <li><strong>United System Manager</strong>: Handles unique identifiers across the system.</li>
                <li><strong>Simulation Engine</strong>: Processes queries through multiple layers of simulation.</li>
                <li><strong>Knowledge Algorithms</strong>: Specialized algorithms for specific knowledge tasks.</li>
              </ul>

              <h4>Simulation Layers</h4>
              <ol>
                <li><strong>Query Contextualization</strong>: Analyzes queries to determine context.</li>
                <li><strong>Query Persona Engine & Refinement Orchestrator</strong>: Processes queries through multiple expert personas.</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';

export default function Home() {
  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph System</title>
      </Head>

      <div className="px-4 py-5 my-5 text-center">
        <h1 className="display-5 fw-bold text-white">Universal Knowledge Graph System</h1>
        <div className="col-lg-8 mx-auto">
          <p className="lead mb-4">
            A comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph that provides contextual understanding and intelligent responses.
          </p>
          <div className="d-grid gap-2 d-sm-flex justify-content-sm-center">
            <Link href="/chat" className="btn btn-primary btn-lg px-4 gap-3">
              Try the Chat Interface
            </Link>
            <button type="button" className="btn btn-outline-light btn-lg px-4">
              Learn More
            </button>
          </div>
        </div>
      </div>

      <div className="row g-4 py-5">
        <div className="col-md-4">
          <div className="card bg-dark text-light border-secondary h-100">
            <div className="card-body">
              <h3 className="card-title">13-Axis Knowledge Framework</h3>
              <p className="card-text">
                Our system organizes knowledge across 13 distinct dimensions, creating a comprehensive understanding of information.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card bg-dark text-light border-secondary h-100">
            <div className="card-body">
              <h3 className="card-title">Contextual Understanding</h3>
              <p className="card-text">
                The system provides responses with location awareness and personalized context sensitivity.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card bg-dark text-light border-secondary h-100">
            <div className="card-body">
              <h3 className="card-title">Multi-Persona Reasoning</h3>
              <p className="card-text">
                Knowledge, skill, role, and context experts work together to provide comprehensive answers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
