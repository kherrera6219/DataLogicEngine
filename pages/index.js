import Head from 'next/head';
import Link from 'next/link';
import Layout from '../components/Layout';

const features = [
  {
    title: '13-Axis Knowledge Framework',
    description: 'Spatially aware reasoning across pillar, sector, regulatory, context, and time dimensions.',
    icon: 'grid-3x3-gap',
    badge: 'Multi-dimensional'
  },
  {
    title: 'AI-First Workbench',
    description: 'Conversational entry point with command palette, multimodal input, and live previews.',
    icon: 'magic',
    badge: 'Voice + Text'
  },
  {
    title: 'Compliance-Grade',
    description: 'SOC 2 aligned controls, audit trails, exportable reports, and risk posture telemetry.',
    icon: 'shield-check',
    badge: 'Enterprise'
  },
  {
    title: 'Interactive Graph',
    description: 'WebGL knowledge explorer with node spotlight, axis filters, and honeycomb layouts.',
    icon: 'diagram-3',
    badge: 'Immersive'
  },
  {
    title: 'Team Collaboration',
    description: 'Shared chats, curated prompts, and annotation trails for procurement and research teams.',
    icon: 'people',
    badge: 'Real-time'
  },
  {
    title: 'Performance Ready',
    description: 'Optimistic UI, skeleton loaders, and background prefetching tuned for 60fps interactions.',
    icon: 'speedometer2',
    badge: '60fps'
  }
];

const axisTabs = [
  'Pillar',
  'Sector',
  'Honeycomb',
  'Branch',
  'Node',
  'Regulatory',
  'Compliance',
  'Context',
  'Location',
  'Time'
];

const pricing = [
  {
    name: 'Starter',
    price: '$99',
    detail: 'per seat / month',
    features: ['Single workspace', 'Chat + Graph explorer', 'Standard support']
  },
  {
    name: 'Professional',
    price: '$499',
    detail: 'per workspace / month',
    features: ['Unlimited seats', 'Compliance dashboards', 'Priority SLAs', 'API access'],
    popular: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    detail: 'annual agreements',
    features: ['SSO/SAML + SCIM', 'Dedicated tenant', 'On-prem or FedRAMP pathways']
  }
];

const journeys = [
  {
    title: 'Start in chat',
    href: '/chat',
    description: 'Converse with the copilot, load a procurement packet, and bookmark prompts for your team.',
    icon: 'chat-left-dots'
  },
  {
    title: 'Map the graph',
    href: '/knowledge-graph',
    description: 'Jump directly into the 13-axis graph explorer with spotlight, filters, and layouts.',
    icon: 'diagram-3'
  },
  {
    title: 'Check compliance',
    href: '/compliance-dashboard',
    description: 'Open the live dashboards, export reports, and monitor SOC 2 and NIST controls.',
    icon: 'shield-lock'
  }
];

const launchSteps = [
  'Connect your data sources or drop a policy packet',
  'Pick an axis (Regulatory, Context, Honeycomb, or Time) to shape the view',
  'Ask a question, then pivot into dashboards or exports without losing the trail'
];

export default function Home() {
  return (
    <Layout>
      <Head>
        <title>Universal Knowledge Graph System</title>
      </Head>

      <section className="mesh-hero text-white p-4 p-md-5 rounded-4 mb-5">
        <div className="row align-items-center g-4">
          <div className="col-lg-7">
            <div className="d-flex align-items-center gap-2 mb-3">
              <span className="pill"><i className="bi bi-stars"></i> 2025 Design System</span>
              <span className="pill"><i className="bi bi-cpu"></i> AI-first</span>
            </div>
            <h1 className="display-5 fw-bold mb-3">Universal Knowledge Graph for AI decisioning</h1>
            <p className="lead text-white-50 mb-4">
              An immersive, glassmorphic surface that blends conversational AI, interactive graph navigation, and compliance-grade governance for teams that live in audits and procurement reviews.
            </p>

            <div className="glass-panel p-3 mb-3">
              <div className="d-flex align-items-center gap-2 flex-wrap">
                <i className="bi bi-mic text-info"></i>
                <input
                  className="form-control form-control-lg bg-transparent text-white border-0"
                  placeholder="Ask me anything about procurement, policy, or your data..."
                  aria-label="AI prompt input"
                />
                <button className="btn btn-outline-light rounded-pill"><i className="bi bi-mic-fill me-2"></i>Voice</button>
                <button className="btn btn-primary rounded-pill"><i className="bi bi-arrow-return-right me-2"></i>Start with AI</button>
              </div>
            </div>

            <div className="d-flex flex-wrap gap-3 align-items-center mb-4">
              <Link href="/chat" className="btn btn-primary btn-lg rounded-pill px-4 d-flex align-items-center gap-2">
                <i className="bi bi-chat-text"></i> Open AI Workbench
              </Link>
              <Link href="/knowledge-graph" className="btn btn-outline-light btn-lg rounded-pill px-4 d-flex align-items-center gap-2">
                <i className="bi bi-diagram-3"></i> Explore Graph
              </Link>
              <span className="text-white-50 small">Trusted by federal, state, and enterprise teams.</span>
            </div>

            <div className="d-flex flex-wrap gap-3 text-white-50">
              <div className="metric-chip"><span className="status-dot bg-success"></span> 13-axis navigation</div>
              <div className="metric-chip"><span className="status-dot bg-info"></span> Real-time compliance</div>
              <div className="metric-chip"><span className="status-dot bg-primary"></span> AI copilots</div>
            </div>
          </div>

          <div className="col-lg-5">
            <div className="glass-panel p-4 h-100">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span className="section-title">Live Preview</span>
                <span className="badge bg-primary bg-opacity-25 text-primary">Interactive</span>
              </div>
              <div className="gradient-border p-3 mb-3">
                <div className="glass-border p-3 text-white-50 small">
                  <div className="d-flex justify-content-between mb-2">
                    <span>AI Response Stream</span>
                    <span className="badge bg-success bg-opacity-25 text-success">Streaming</span>
                  </div>
                  <div className="sparkle-divider"></div>
                  <p className="mb-0">“I’ve mapped the Federal Acquisition Regulation clauses to your supplier profile. Axis 6 (Regulatory) shows three open risks and two mitigations. Would you like me to generate the SOC 2 delta report?”</p>
                </div>
              </div>
              <div className="d-grid gap-2">
                <div className="action-chip"><i className="bi bi-activity me-2"></i> Live compliance telemetry</div>
                <div className="action-chip"><i className="bi bi-braces me-2"></i> YAML-ready interface specs</div>
                <div className="action-chip"><i className="bi bi-hexagon me-2"></i> Honeycomb + timeline layouts</div>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-4">
          <div className="scroll-indicator mx-auto"></div>
        </div>
      </section>

      <section className="mb-5">
        <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
          <span className="section-title">Capabilities</span>
          <div className="pill"><i className="bi bi-lightning-charge"></i> WCAG 2.2 AAA Ready</div>
        </div>
        <div className="feature-grid">
          {features.map((item) => (
            <div key={item.title} className="feature-card h-100">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <div className="d-flex align-items-center gap-2">
                  <i className={`bi bi-${item.icon} fs-4 text-primary`}></i>
                  <strong>{item.title}</strong>
                </div>
                <span className="badge bg-secondary text-uppercase">{item.badge}</span>
              </div>
              <p className="text-white-50 mb-0">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-5">
        <div className="glass-panel p-4">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-3">
            <div>
              <span className="section-title">Interactive Demo</span>
              <h3 className="mb-0 text-white">Knowledge Graph + Compliance dashboard</h3>
              <small className="text-white-50">Hover nodes to explore relationships, switch axes to change layouts.</small>
            </div>
            <div className="d-flex gap-2">
              <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-arrows-fullscreen me-1"></i> Fullscreen</button>
              <button className="btn btn-primary btn-sm rounded-pill"><i className="bi bi-play-circle me-1"></i> Start demo</button>
            </div>
          </div>

          <div className="row g-3 align-items-start">
            <div className="col-lg-8">
              <div className="gradient-border p-3 h-100">
                <div className="glass-border p-3 h-100">
                  <div className="d-flex gap-2 flex-wrap mb-3">
                    {axisTabs.map((axis) => (
                      <button key={axis} className="btn btn-sm btn-outline-light rounded-pill">{axis}</button>
                    ))}
                  </div>
                  <div className="bg-dark bg-opacity-25 rounded-3 p-4 text-center text-white-50" style={{ minHeight: '260px' }}>
                    <i className="bi bi-diagram-3 display-6 d-block mb-2 text-primary"></i>
                    <p className="mb-0">WebGL graph placeholder — renders force-directed, honeycomb, or timeline views per axis.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-lg-4">
              <div className="d-grid gap-3">
                <div className="glass-border p-3">
                  <div className="d-flex justify-content-between mb-2">
                    <span className="text-white-50">Compliance posture</span>
                    <span className="badge bg-success">92%</span>
                  </div>
                  <div className="sparkle-divider"></div>
                  <p className="mb-1">6 open issues · 2 critical mitigations · SOC 2 Type II ready</p>
                </div>
                <div className="glass-border p-3">
                  <div className="d-flex justify-content-between mb-2">
                    <span className="text-white-50">Real-time signals</span>
                    <span className="badge bg-info">Streaming</span>
                  </div>
                  <p className="mb-0">Live telemetry from regulatory spiderweb, honeycomb, and timeline axes.</p>
                </div>
                <div className="glass-border p-3">
                  <div className="d-flex justify-content-between mb-2">
                    <span className="text-white-50">Action</span>
                    <span className="badge bg-primary">Next</span>
                  </div>
                  <p className="mb-2">Generate SOC 2 export or launch chat with compliance copilots.</p>
                  <Link href="/compliance-dashboard" className="btn btn-outline-light btn-sm rounded-pill">Open dashboard</Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mb-5">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
          <div>
            <span className="section-title">Launch pathways</span>
            <h3 className="text-white mb-0">Pick a starting point and stay in flow</h3>
          </div>
          <span className="pill"><i className="bi bi-compass"></i> 90-second setup</span>
        </div>

        <div className="row g-3 mb-4">
          {journeys.map((journey) => (
            <div key={journey.title} className="col-md-4">
              <div className="glass-panel p-3 h-100">
                <div className="d-flex align-items-center gap-2 mb-2">
                  <i className={`bi bi-${journey.icon} text-primary fs-4`}></i>
                  <strong>{journey.title}</strong>
                </div>
                <p className="text-white-50 mb-3">{journey.description}</p>
                <Link href={journey.href} className="btn btn-outline-light btn-sm rounded-pill">Open</Link>
              </div>
            </div>
          ))}
        </div>

        <div className="glass-panel p-4">
          <div className="d-flex align-items-center gap-2 mb-3">
            <span className="badge bg-primary bg-opacity-25 text-primary">Workflow</span>
            <span className="section-title mb-0">Rapid launch guide</span>
          </div>
          <div className="row g-3 align-items-center">
            <div className="col-lg-7">
              <ol className="text-white-50 lead ps-3 mb-0">
                {launchSteps.map((step) => (
                  <li key={step} className="mb-2">{step}</li>
                ))}
              </ol>
            </div>
            <div className="col-lg-5">
              <div className="gradient-border p-3 h-100">
                <div className="glass-border p-3 h-100 d-flex flex-column justify-content-between">
                  <div>
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <span className="text-white-50">Live checklist</span>
                      <span className="badge bg-success">4/5 ready</span>
                    </div>
                    <p className="text-white-50 mb-3">Graph explorer, chat workbench, and compliance dashboards are all preloaded with demo data.</p>
                  </div>
                  <div className="d-flex gap-2 flex-wrap">
                    <span className="pill"><i className="bi bi-cpu"></i> AI copilots</span>
                    <span className="pill"><i className="bi bi-hexagon"></i> Honeycomb layouts</span>
                    <span className="pill"><i className="bi bi-collection"></i> Exportable reports</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mb-5">
        <div className="row g-4 align-items-center">
          <div className="col-lg-6">
            <div className="glass-panel p-4 h-100">
              <span className="section-title">Customer story</span>
              <h3 className="text-white">“Compliance review time dropped by 80%”</h3>
              <p className="text-white-50">DataLogicEngine orchestrated regulatory copilots, interactive graphs, and procurement timelines to accelerate approvals across 13 axes of context.</p>
              <div className="d-flex align-items-center gap-3">
                <div className="avatar bg-primary bg-opacity-25 rounded-circle d-flex align-items-center justify-content-center" style={{ width: '48px', height: '48px' }}>
                  <i className="bi bi-person-fill text-primary"></i>
                </div>
                <div>
                  <strong>Sarah Johnson</strong>
                  <p className="mb-0 text-white-50">Procurement Director · Department of Defense</p>
                </div>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="row g-3">
              {pricing.map((plan) => (
                <div key={plan.name} className="col-md-4 col-lg-4">
                  <div className={`glass-panel p-3 h-100 ${plan.popular ? 'border border-primary' : ''}`}>
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <strong>{plan.name}</strong>
                      {plan.popular && <span className="badge bg-primary">Popular</span>}
                    </div>
                    <h4 className="mb-0">{plan.price}</h4>
                    <small className="text-white-50">{plan.detail}</small>
                    <ul className="mt-3 text-white-50 small mb-3">
                      {plan.features.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                    <button className="btn btn-outline-light w-100 btn-sm rounded-pill">Choose plan</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="glass-panel p-4 p-md-5 text-center mb-5">
        <div className="d-flex justify-content-center gap-3 flex-wrap mb-3">
          <span className="pill"><i className="bi bi-shield-lock"></i> SOC 2 controls</span>
          <span className="pill"><i className="bi bi-people"></i> Collaboration ready</span>
          <span className="pill"><i className="bi bi-columns"></i> Responsive layouts</span>
        </div>
        <h2 className="mb-3">Ready to launch the UKG experience?</h2>
        <p className="text-white-50 mb-4">Open the AI workbench, invite teammates, and explore the knowledge graph and compliance dashboards in minutes.</p>
        <div className="d-flex justify-content-center gap-3 flex-wrap">
          <Link href="/login" className="btn btn-primary btn-lg rounded-pill px-4">Login / SSO</Link>
          <Link href="/chat" className="btn btn-outline-light btn-lg rounded-pill px-4">Start in chat</Link>
        </div>
      </section>
    </Layout>
  );
}