import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';

export default function Home() {
  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph System</title>
      </Head>

      <section className="landing-hero position-relative overflow-hidden">
        <div className="gradient-overlay"></div>
        <div className="floating-orb orb-one"></div>
        <div className="floating-orb orb-two"></div>
        <div className="floating-orb orb-three"></div>
        <div className="container position-relative py-5">
          <div className="row align-items-center g-5">
            <div className="col-lg-7 text-start">
              <span className="badge rounded-pill bg-opacity-10 bg-primary text-primary-emphasis mb-3">Next-Generation Intelligence</span>
              <h1 className="display-4 fw-bold text-white mb-4 pe-lg-5">
                Build trustable intelligence with the Universal Knowledge Graph System
              </h1>
              <p className="lead text-white-50 mb-4">
                Orchestrate 13 knowledge dimensions, contextual signals, and persona-driven reasoning to unlock transparent and auditable AI decisions across your enterprise.
              </p>
              <div className="d-flex flex-column flex-md-row gap-3">
                <Link href="/chat" className="btn btn-hero-primary btn-lg px-4 d-flex align-items-center justify-content-center">
                  <i className="bi bi-chat-text me-2"></i>
                  Launch the AI Copilot
                </Link>
                <Link href="/unified-mapping" className="btn btn-hero-outline btn-lg px-4 d-flex align-items-center justify-content-center">
                  <i className="bi bi-rocket-takeoff me-2"></i>
                  Explore the Graph
                </Link>
              </div>
              <div className="d-flex flex-wrap gap-4 mt-5">
                <div className="stat-card">
                  <span className="stat-value">13</span>
                  <span className="stat-label">Knowledge Axes</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">24/7</span>
                  <span className="stat-label">Context-Aware Insights</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">360°</span>
                  <span className="stat-label">Governance & Trust</span>
                </div>
              </div>
            </div>
            <div className="col-lg-5">
              <div className="hero-visual glass-card">
                <div className="glow-border"></div>
                <div className="d-flex justify-content-between align-items-start mb-4">
                  <div>
                    <p className="text-uppercase text-white-50 mb-1 small">Live Knowledge Signal</p>
                    <h2 className="fs-4 text-white mb-0">Persona Collaboration Heatmap</h2>
                  </div>
                  <span className="badge bg-success bg-opacity-25 text-success">Stable</span>
                </div>
                <div className="persona-grid">
                  {[
                    { icon: 'bi-compass', label: 'Context' },
                    { icon: 'bi-person-bounding-box', label: 'Persona' },
                    { icon: 'bi-lightbulb', label: 'Strategy' },
                    { icon: 'bi-shield-check', label: 'Compliance' },
                    { icon: 'bi-geo-alt', label: 'Location' },
                    { icon: 'bi-graph-up', label: 'Impact' },
                  ].map((persona) => (
                    <div key={persona.label} className="persona-tile">
                      <i className={`bi ${persona.icon}`}></i>
                      <span>{persona.label}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <p className="text-white-50 small mb-2">Confidence Distribution</p>
                  <div className="confidence-bar">
                    <span style={{ width: '78%' }}></span>
                  </div>
                  <div className="d-flex justify-content-between text-white-50 small mt-2">
                    <span>Transparent</span>
                    <span>Auditable</span>
                    <span>Explainable</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-5">
        <div className="text-center mb-5">
          <span className="badge rounded-pill bg-primary-subtle text-primary-emphasis mb-3">Why UKG?</span>
          <h2 className="fw-semibold text-white mb-3">A platform engineered for clarity and control</h2>
          <p className="text-white-50 mb-0">
            Harmonize siloed data, map multi-layer relationships, and activate responsible AI outcomes with confidence.
          </p>
        </div>

        <div className="row g-4">
          {[
            {
              icon: 'bi-grid-3x3-gap-fill',
              title: '13-Axis Intelligence Fabric',
              description:
                'Model reality across missions, capabilities, compliance, and timelines to keep your teams aligned and informed.',
            },
            {
              icon: 'bi-bezier',
              title: 'Contextual Signal Fusion',
              description:
                'Blend personas, location awareness, and regulatory triggers to produce answers that adapt to every scenario.',
            },
            {
              icon: 'bi-people-fill',
              title: 'Persona-Driven Reasoning',
              description:
                'Coordinate knowledge, skill, role, and context experts to reason transparently and surface traceable insights.',
            },
            {
              icon: 'bi-shield-lock',
              title: 'Governance & Explainability',
              description:
                'Built-in lineage, audit trails, and safeguards ensure decisions meet mission-critical compliance requirements.',
            },
            {
              icon: 'bi-lightning-charge',
              title: 'Real-Time Orchestration',
              description:
                'Activate simulations and remediation workflows instantly with our event-driven orchestration engine.',
            },
            {
              icon: 'bi-diagram-3',
              title: 'Unified Knowledge Graph',
              description:
                'Connect enterprise systems, policies, and on-the-ground insights into a single navigable knowledge landscape.',
            },
          ].map((feature) => (
            <div className="col-12 col-md-6 col-xl-4" key={feature.title}>
              <div className="feature-card h-100 p-4">
                <div className="feature-icon mb-3">
                  <i className={`bi ${feature.icon}`}></i>
                </div>
                <h3 className="h5 text-white mb-3">{feature.title}</h3>
                <p className="text-white-50 mb-0">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="py-5 position-relative">
        <div className="radial-highlight"></div>
        <div className="row g-4 align-items-center">
          <div className="col-lg-6">
            <div className="glass-card p-4 p-lg-5 h-100">
              <h2 className="h3 text-white mb-4">Operational clarity at every layer</h2>
              <div className="d-flex flex-wrap gap-3">
                {[
                  'Mission & Goals',
                  'Capabilities & Pillars',
                  'Signals & Events',
                  'Controls & Policies',
                  'Risk & Compliance',
                  'Response Playbooks',
                ].map((item) => (
                  <span key={item} className="capability-pill">
                    <i className="bi bi-check2-circle me-2"></i>
                    {item}
                  </span>
                ))}
              </div>
              <p className="text-white-50 mt-4 mb-0">
                The Universal Knowledge Graph connects strategy to execution with real-time visibility into dependencies, impacts, and responsible owners.
              </p>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="innovation-grid">
              {[
                { title: 'Adaptive Reasoning', text: 'Dynamic persona collaboration unlocks richer conversations and contextual awareness.' },
                { title: 'Simulation Ready', text: 'Run layered simulations and orchestration workflows to test strategies before deployment.' },
                { title: 'Trusted Data Layer', text: 'Source-of-truth integrations, lineage tracking, and AI safety guardrails baked in.' },
              ].map((item) => (
                <div key={item.title} className="innovation-tile">
                  <h3 className="h5 text-white mb-2">{item.title}</h3>
                  <p className="text-white-50 mb-0">{item.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="py-5">
        <div className="row g-4">
          <div className="col-lg-7">
            <div className="glass-card h-100 p-4 p-lg-5">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span className="badge rounded-pill bg-info-subtle text-info-emphasis">Live Metrics</span>
                <i className="bi bi-activity text-info"></i>
              </div>
              <h2 className="h4 text-white mb-4">Intelligence operations at a glance</h2>
              <div className="row g-4">
                {[
                  { label: 'Knowledge Refresh Cycle', value: '12 mins', trend: '+18%' },
                  { label: 'Persona Coverage', value: '92%', trend: '+6%' },
                  { label: 'Compliance Guardrails', value: '148', trend: 'Real-time' },
                ].map((metric) => (
                  <div className="col-md-4" key={metric.label}>
                    <div className="metric-card">
                      <p className="text-white-50 small mb-1">{metric.label}</p>
                      <h3 className="h4 text-white mb-0">{metric.value}</h3>
                      <span className="metric-trend">{metric.trend}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <p className="text-white-50 small mb-2">Operational Confidence</p>
                <div className="confidence-bar confidence-bar-secondary">
                  <span style={{ width: '86%' }}></span>
                </div>
              </div>
            </div>
          </div>
          <div className="col-lg-5">
            <div className="testimonial-card h-100 p-4 p-lg-5">
              <i className="bi bi-quote text-primary display-5"></i>
              <p className="lead text-white mt-3">
                “The Universal Knowledge Graph gives our teams a live operational picture—tying mission priorities, compliance mandates, and on-the-ground insights together with unprecedented clarity.”
              </p>
              <div className="mt-4">
                <p className="text-white fw-semibold mb-1">Chief Intelligence Officer</p>
                <p className="text-white-50 mb-0">Global Resilience Organization</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-banner my-5 py-5 text-center">
        <div className="container">
          <h2 className="display-6 fw-semibold text-white mb-3">Ready to activate a living knowledge graph?</h2>
          <p className="text-white-50 mb-4">
            Deploy UKG as the connective tissue between strategy, compliance, and execution with transparency built in from day one.
          </p>
          <div className="d-flex flex-column flex-sm-row justify-content-center gap-3">
            <Link href="/chat" className="btn btn-hero-primary btn-lg px-4">
              <i className="bi bi-play-circle me-2"></i>
              Start a Guided Session
            </Link>
            <Link href="/compliance-dashboard" className="btn btn-hero-outline btn-lg px-4">
              <i className="bi bi-bar-chart-line me-2"></i>
              View Governance Console
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}