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