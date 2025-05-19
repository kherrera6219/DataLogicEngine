import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';

export default function Home() {
  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph System</title>
      </Head>

      <div className="container-fluid px-4 py-5 my-4 text-center">
        <div className="row justify-content-center align-items-center g-4">
          <div className="col-lg-8">
            <h1 className="display-5 fw-bold text-white mb-4">Universal Knowledge Graph System</h1>
            <p className="lead mb-4">
              A comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph that provides contextual understanding and intelligent responses.
            </p>
            <div className="d-flex flex-column flex-sm-row gap-3 justify-content-center">
              <Link href="/chat" className="btn btn-primary btn-lg px-4 d-flex align-items-center justify-content-center">
                <i className="bi bi-chat-text me-2"></i> Try the Chat Interface
              </Link>
              <button type="button" className="btn btn-outline-light btn-lg px-4 d-flex align-items-center justify-content-center">
                <i className="bi bi-info-circle me-2"></i> Learn More
              </button>
            </div>
          </div>
          <div className="col-lg-4 d-none d-lg-block">
            <div className="position-relative" style={{ height: '300px' }}>
              <div className="position-absolute top-50 start-50 translate-middle">
                <i className="bi bi-diagram-3 text-primary" style={{ fontSize: '200px', opacity: '0.6' }}></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4 py-5">
        <div className="col d-flex">
          <div className="card bg-dark text-light border-secondary flex-fill">
            <div className="card-body d-flex flex-column">
              <div className="d-flex align-items-center mb-3">
                <i className="bi bi-grid-3x3-gap-fill fs-3 me-3 text-primary"></i>
                <h3 className="card-title mb-0">13-Axis Knowledge Framework</h3>
              </div>
              <p className="card-text flex-grow-1">
                Our system organizes knowledge across 13 distinct dimensions, creating a comprehensive understanding of information.
              </p>
              <button className="btn btn-outline-primary mt-3">Learn More</button>
            </div>
          </div>
        </div>
        <div className="col d-flex">
          <div className="card bg-dark text-light border-secondary flex-fill">
            <div className="card-body d-flex flex-column">
              <div className="d-flex align-items-center mb-3">
                <i className="bi bi-geo-alt-fill fs-3 me-3 text-primary"></i>
                <h3 className="card-title mb-0">Contextual Understanding</h3>
              </div>
              <p className="card-text flex-grow-1">
                The system provides responses with location awareness and personalized context sensitivity.
              </p>
              <button className="btn btn-outline-primary mt-3">Learn More</button>
            </div>
          </div>
        </div>
        <div className="col d-flex">
          <div className="card bg-dark text-light border-secondary flex-fill">
            <div className="card-body d-flex flex-column">
              <div className="d-flex align-items-center mb-3">
                <i className="bi bi-people-fill fs-3 me-3 text-primary"></i>
                <h3 className="card-title mb-0">Multi-Persona Reasoning</h3>
              </div>
              <p className="card-text flex-grow-1">
                Knowledge, skill, role, and context experts work together to provide comprehensive answers.
              </p>
              <button className="btn btn-outline-primary mt-3">Learn More</button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}