# Frontend Product Surface and Trace Review Map

> **Document metadata**
> - Document version: v1.1.0
> - Last reviewed: 2026-07-06
> - Status: Active architecture review map
> - Owner: Platform Architecture
> - Scope: Current Next.js/Electron review surfaces and traceability UI map.

## Purpose

This diagram maps how the backend architecture becomes a product surface that judges, reviewers, operators, and users can actually click through. It connects the Next.js frontend routes, provider stack, sidebar navigation, API clients, trace explorer, graph views, Truth Engine monitor, chat interface, MCP hub, admin/compliance views, privacy disclosures, and Electron desktop shell.

The goal is to show that DataLogicEngine is not only backend architecture. It has a frontend review surface for operating, inspecting, tracing, and explaining the AI system.

## Primary Code Paths

- `frontend/app/layout.tsx`
- `frontend/components/layout/AppSidebar.tsx`
- `frontend/README.md`
- `frontend/app/dashboard/`
- `frontend/app/chat/`
- `frontend/app/graph/`
- `frontend/app/knowledge/`
- `frontend/app/runs/`
- `frontend/app/truth-engine/`
- `frontend/app/mcp/`
- `frontend/app/admin/`
- `frontend/app/settings/`
- `frontend/lib/api/`
- `frontend/components/Chat/`
- `frontend/components/Graph/`
- `frontend/components/mcp/`
- `frontend/components/ui/api-error-boundary.tsx`
- `frontend/contexts/AuthContext.tsx`
- `frontend/electron/`

## Mermaid Product Surface Map

```mermaid
flowchart TD
    User[Judge / Operator / User]
    Electron[Electron Desktop Shell\noptional Windows runtime]
    Browser[Browser / Next.js Runtime]
    Root[Root Layout\nfrontend/app/layout.tsx]

    User --> Electron
    User --> Browser
    Electron --> Root
    Browser --> Root

    subgraph PROVIDERS[Root Provider Stack]
        FeatureFlags[FeatureFlagProvider]
        ClientErrors[ClientErrorBootstrap]
        Theme[ThemeProvider]
        SWR[SWRConfig\ncache + revalidation + retries]
        Auth[AuthProvider\nweb auth + desktop auto-login]
        AppInit[AppInitializer\nworkspace bootstrap]
        Toast[ToastProvider]
        ErrorBoundary[ApiErrorBoundary\nmodule-level recovery]
        Sidebar[AppSidebar]
        CloudDisclosure[CloudDisclosureBanner]
        NavBar[NavBar]
        DesktopStatus[DesktopStatus]
    end

    Root --> FeatureFlags
    FeatureFlags --> ClientErrors
    ClientErrors --> Theme
    Theme --> SWR
    SWR --> Auth
    Auth --> AppInit
    AppInit --> Toast
    Toast --> ErrorBoundary
    ErrorBoundary --> Sidebar
    ErrorBoundary --> CloudDisclosure
    ErrorBoundary --> NavBar
    ErrorBoundary --> DesktopStatus

    subgraph NAV[Primary Navigation]
        Dashboard[/dashboard\nSystem overview]
        Chat[/chat\nEnterprise AI]
        MCP[/mcp\nMCP Hub]
        Projects[/projects\nProject management]
        Admin[/admin\nAdmin + Compliance]
        Settings[/settings\nUser/runtime settings]
    end

    Sidebar --> Dashboard
    Sidebar --> Chat
    Sidebar --> MCP
    Sidebar --> Projects
    Sidebar --> Admin
    Sidebar --> Settings

    subgraph DEEP[Secondary / Review Surfaces]
        Graph[/graph\n3D Knowledge Graph]
        Knowledge[/knowledge\nNode/edge browser]
        Runs[/runs\nTrace Runs Explorer]
        RunDetail[/runs/view\nRun detail view]
        Analytics[/analytics\nSystem analytics]
        Algorithms[/algorithms\nKnowledge Algorithm browser]
        Simulations[/simulations\nSimulation management]
        TruthEngine[/truth-engine\nTruth Engine monitor]
        Privacy[/settings/privacy + /legal/privacy\nPrivacy controls and policy]
        Disclosures[/about/cloud-services + /about/ai-limitations\nCloud/AI limitations disclosures]
    end

    Dashboard --> Analytics
    Chat --> Runs
    Runs --> RunDetail
    Dashboard --> TruthEngine
    Dashboard --> Graph
    Graph --> Knowledge
    Projects --> RunDetail
    Admin --> Privacy
    Settings --> Privacy
    CloudDisclosure --> Disclosures

    subgraph API[Frontend API Client Layer]
        ApiBase[frontend/lib/api/index.ts\nbase request + CSRF handling]
        AuthApi[auth.ts\ncheck/session/desktop auto-login]
        ChatApi[chat.ts + system_chat.ts]
        TraceApi[trace.ts\nfetch/export trace runs]
        KnowledgeApi[knowledge.ts\ngraph nodes/edges]
        McpApi[mcp.ts\nconnectors + OAuth]
        SimulationApi[simulation.ts]
        ComplianceApi[compliance.ts]
        Types[types.ts\nshared TypeScript interfaces]
        Socket[lib/socket.ts\nreal-time updates]
    end

    Auth --> AuthApi
    Chat --> ChatApi
    Runs --> TraceApi
    RunDetail --> TraceApi
    Graph --> KnowledgeApi
    Knowledge --> KnowledgeApi
    MCP --> McpApi
    Simulations --> SimulationApi
    Admin --> ComplianceApi
    ApiBase --> AuthApi
    ApiBase --> ChatApi
    ApiBase --> TraceApi
    ApiBase --> KnowledgeApi
    ApiBase --> McpApi
    ApiBase --> SimulationApi
    ApiBase --> ComplianceApi
    Types --> ApiBase
    Socket --> Dashboard
    Socket --> TruthEngine

    subgraph BACKEND[Backend Services Exposed to UI]
        Flask[Flask API\n/api/v1/*]
        DMRF[DMRF Reasoning Control Plane]
        Truth[Truth Engine\nTruthGate + TruthCore + TruthMemory + TruthLink]
        Trace[Trace API / Runs / Export]
        Storage[Storage APIs\nSQL + Graph + Vector + Object]
        MCPBackend[MCP Server APIs]
        AdminBackend[Admin / Compliance / Privacy APIs]
    end

    ApiBase --> Flask
    Flask --> DMRF
    Flask --> Truth
    Flask --> Trace
    Flask --> Storage
    Flask --> MCPBackend
    Flask --> AdminBackend

    Trace --> Runs
    Truth --> TruthEngine
    DMRF --> Chat
    Storage --> Graph
    Storage --> Knowledge
    MCPBackend --> MCP
    AdminBackend --> Admin
```

## Judge Click Path

A reviewer can inspect the product in this order:

1. **Dashboard** — verify the app has a system overview and monitoring surface.
2. **Enterprise AI / Chat** — submit a query and inspect trace IDs, detailed response, evidence, controls, and message history.
3. **Runs / Trace Explorer** — inspect stage-by-stage execution, evidence, claims, persona tracking, policy decisions, and exports.
4. **Graph / Knowledge** — inspect the 3D knowledge graph, node/edge browser, search/filter behavior, and 17-axis navigation.
5. **Truth Engine Monitor** — inspect tier routing and Truth Engine execution status.
6. **MCP Hub** — inspect connector registry, OAuth/token lifecycle, analytics, and server configuration.
7. **Admin / Compliance** — inspect provider configuration, MCP management, security/compliance dashboard, and audit export (single authenticated owner).
8. **Settings / Privacy / Legal / About** — inspect local/cloud disclosures, privacy controls, AI limitations, and cloud-service transparency.
9. **Desktop Status** — verify Electron/desktop runtime state when running as a Windows app.

## Route-to-Subsystem Crosswalk

| Frontend route/surface | Backend/system area | Review value |
|---|---|---|
| `/dashboard` | health, analytics, operational APIs | Shows system-level status and monitoring. |
| `/chat` | DMRF, LLM Gateway, Truth Engine, trace generation | Main AI interaction surface. |
| `/runs` and `/runs/view` | trace API, TruthMemory, export integrity | Shows reasoning trace review and exportability. |
| `/graph` | graph store, USKD, 17-axis coordinate model | Shows knowledge graph and coordinate navigation. |
| `/knowledge` | knowledge node/edge APIs | Shows inspectable knowledge assets. |
| `/truth-engine` | Truth Engine API | Shows TruthCore/TruthGate/TruthMemory/TruthLink status. |
| `/mcp` | MCP server APIs | Shows connector and external-tool integration management. |
| `/admin` | admin, compliance, provider config | Shows governance and administrative controls (single owner). |
| `/admin/compliance` | audit/security/compliance APIs | Shows compliance review and audit surface. |
| `/settings` | user/runtime/application settings | Shows configurable runtime behavior. |
| `/settings/privacy` and `/legal/privacy` | privacy APIs and policy docs | Shows privacy controls and user-facing policy. |
| `/about/cloud-services` | cloud disclosure | Shows transparency around external dependencies. |
| `/about/ai-limitations` | AI limitation disclosure | Shows safety and limitation communication. |

## Root Layout Provider Stack

The root layout composes the app in this order:

```text
FeatureFlagProvider
  ClientErrorBootstrap
  ThemeProvider
    SWRConfig
      AuthProvider
        AppInitializer
          ToastProvider
            ApiErrorBoundary
              AppSidebar
              CloudDisclosureBanner
              NavBar
              main content
              DesktopStatus
```

This is important because the frontend product surface is wrapped with:

- feature flags;
- client-side error reporting;
- theme management;
- SWR data fetching behavior;
- authentication and desktop auto-login;
- app initialization/loading state;
- toast notifications;
- API error recovery;
- cloud-dependency disclosure;
- desktop runtime status.

## Sidebar Navigation Surface

`AppSidebar` is the single authoritative navigation surface, grouping the primary
user-facing surfaces into sections:

```text
Workspace:       Dashboard, Enterprise AI, Projects, Simulations, MCP Hub
Knowledge:       Knowledge Base, Knowledge Graph, Algorithms
Trace & Review:  Trace Explorer, Truth Engine, Analytics
System:          Admin*, Compliance*, Settings
```

`NavBar` is global chrome only — logo, cloud-status indicator, theme toggle, and the
account menu; it no longer duplicates primary page links. Admin and Compliance are
integrated into single-mode desktop operation (OS-level auth; see
`docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md`). The
sidebar collapsed state is persisted in local storage.

## Trace Review Surface

The frontend README describes the Trace Explorer as supporting:

- comprehensive trace run visualization;
- stage-by-stage execution breakdown;
- evidence and claims viewer;
- persona and policy decision tracking;
- export functionality.

This maps directly to the backend concepts from DMRF, TruthMemory, TruthLink, and export integrity.

## Chat Review Surface

The chat interface is described as supporting:

- interactive chat with UKG-enhanced LLMs;
- streaming responses;
- message history;
- trace ID linking for auditability;
- advanced model control panel;
- detailed response view with evidence.

This means the main AI interface is designed to expose reasoning/evidence context rather than only final answers.

## Graph Review Surface

The knowledge graph surface is described as supporting:

- interactive 3D graph visualization;
- node and edge browser;
- search and filter capabilities;
- 17-axis coordinate navigation.

This maps the 17-axis and USKD/graph architecture into a visual inspection surface.

## MCP and Admin Review Surfaces

The MCP hub exposes:

- connector registry;
- OAuth token management;
- analytics per connector;
- server configuration.

The Admin panel exposes:

- LLM provider configuration;
- MCP server management;
- compliance dashboard;
- audit log export (single authenticated owner).

These are important because they show the application is designed for single-owner local-first desktop operation with Windows OS-level authentication, not multi-user SaaS.

## Frontend Technology Stack

The frontend is built on:

- Next.js App Router;
- React;
- TypeScript;
- Tailwind CSS;
- Shadcn/Radix UI components;
- SWR for data fetching;
- Electron 40 for optional Windows desktop shell;
- Recharts;
- Three.js + `react-force-graph-3d`.

## Judge Review Path

A technical judge should inspect these files in order:

1. `frontend/app/layout.tsx` — confirms the root provider stack, app shell, sidebar, nav, disclosure banner, footer, and desktop status.
2. `frontend/components/layout/AppSidebar.tsx` — confirms primary product navigation and desktop local-auth gate (single owner).
3. `frontend/README.md` — confirms documented route structure, key features, API integration, design system, and desktop shell.
4. `frontend/lib/api/index.ts` — confirms base API request behavior and CSRF handling.
5. `frontend/lib/api/trace.ts` — confirms trace run fetch/export behavior.
6. `frontend/components/Chat/` and `frontend/app/chat/` — confirms Enterprise AI interaction surface.
7. `frontend/app/runs/` — confirms trace explorer and run detail surfaces.
8. `frontend/app/graph/` and `frontend/components/Graph/` — confirms graph/axis review surfaces.
9. `frontend/app/truth-engine/` — confirms Truth Engine monitoring surface.
10. `frontend/app/mcp/` and `frontend/components/mcp/` — confirms MCP connector review surface.
11. `frontend/app/admin/` — confirms admin/governance/compliance surface.
12. `frontend/electron/main.ts` and `frontend/electron/preload.ts` — confirms desktop shell and safe IPC exposure.

## Interpretation

The frontend turns DataLogicEngine's research-heavy backend into a reviewable product. It gives judges surfaces to inspect query execution, trace stages, graph context, evidence, personas, Truth Engine status, connector governance, compliance posture, runtime disclosures, and desktop/local-first behavior.

This matters because a complex AI architecture without a review surface is hard to evaluate. DataLogicEngine includes the UI layers needed to make the architecture visible.
