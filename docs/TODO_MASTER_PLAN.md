# Universal Knowledge Graph (UKG) System - Master Build Plan

> **Document Version:** 1.0  
> **Created:** December 18, 2025  
> **Status:** Planning Phase

---

## System Overview

This system serves a **dual purpose**:

1. **User-Facing Application** - Direct web interface for knowledge exploration, simulation, and AI-powered analysis
2. **AI Model Overlay/API System** - LLM-agnostic middleware that accepts input from any LLM provider and outputs to user's own applications via API

### Core Technologies
- **Backend:** Flask/Python with Gunicorn (Port 5000)
- **Frontend:** Jinja2 Templates with Bootstrap 5, D3.js
- **Database:** PostgreSQL with SQLAlchemy ORM
- **AI:** OpenAI, Azure OpenAI, Anthropic (Claude), Google (Gemini) via MODEL_PROVIDER

---

## Phase 1: Foundation & Route Cleanup
**Timeline:** 1-2 days  
**Goal:** Make existing pages work and establish stable navigation

### Phase 1A: Route Consolidation
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P1A-1 | Remove duplicate routes from `routes.py` that conflict with `app.py` (`/`, `/login`, `/register`, `/logout`, `/dashboard`, `/profile`, `/settings`) | [ ] Pending | Critical |
| P1A-2 | Fix `/simulation` route 404 error | [ ] Pending | Critical |
| P1A-3 | Connect `persona_demo.html` to proper route | [ ] Pending | High |
| P1A-4 | Fix `/knowledge` route and template | [ ] Pending | High |
| P1A-5 | Fix `/graph` route and template | [ ] Pending | High |
| P1A-6 | Fix `/chatbot` route and template | [ ] Pending | High |
| P1A-7 | Fix `/analytics` route and template | [ ] Pending | High |

### Phase 1B: Navigation & Structure
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P1B-1 | Update `base.html` navigation with all working pages | [ ] Pending | High |
| P1B-2 | Create consistent page layout structure | [ ] Pending | Medium |
| P1B-3 | Add breadcrumb navigation | [ ] Pending | Low |
| P1B-4 | Test all routes and verify no 404 errors | [ ] Pending | Critical |

---

## Phase 2: Knowledge System UI
**Timeline:** 5-7 days  
**Goal:** Expose all backend systems through user interfaces

### Phase 2A: Core Interaction (Chat & Persona)
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P2A-1 | Build enterprise Chat UI with streaming responses | [ ] Pending | Critical |
| P2A-2 | Add chat history persistence and retrieval | [ ] Pending | High |
| P2A-3 | Implement markdown rendering in chat responses | [ ] Pending | High |
| P2A-4 | Add code syntax highlighting in responses | [ ] Pending | Medium |
| P2A-5 | Create Quad Persona Tracing Dashboard | [ ] Pending | High |
| P2A-6 | Visualize Analyst/Expert/Critic/Synthesizer processing flow | [ ] Pending | High |
| P2A-7 | Show persona confidence scores and reasoning | [ ] Pending | Medium |

### Phase 2B: Knowledge Framework Visualization
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P2B-1 | Build 17-Axis Coordinate Explorer page | [ ] Pending | High |
| P2B-2 | Create interactive D3.js visualization for axes | [ ] Pending | High |
| P2B-3 | Add axis filtering and search | [ ] Pending | Medium |
| P2B-4 | Show Nuremberg-style coordinate system | [ ] Pending | Medium |
| P2B-5 | Create Knowledge Algorithm Browser page | [ ] Pending | High |
| P2B-6 | List all 58+ KAs with documentation | [ ] Pending | High |
| P2B-7 | Add KA testing/execution interface | [ ] Pending | Medium |
| P2B-8 | Build 10-Layer Simulation Monitor | [ ] Pending | High |
| P2B-9 | Show real-time layer activation status | [ ] Pending | High |
| P2B-10 | Visualize data flow through layers | [ ] Pending | Medium |

### Phase 2C: Truth Engine & MCP
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P2C-1 | Build Truth Engine Monitor dashboard | [ ] Pending | High |
| P2C-2 | Show TruthCore tier-based processing status | [ ] Pending | High |
| P2C-3 | Display TruthGate security/budget controls | [ ] Pending | Medium |
| P2C-4 | Visualize TruthMemory audit trails | [ ] Pending | Medium |
| P2C-5 | Monitor TruthLink event bus messages | [ ] Pending | Medium |
| P2C-6 | Build MCP Server Manager page | [ ] Pending | High |
| P2C-7 | Create/configure/delete MCP servers | [ ] Pending | High |
| P2C-8 | Manage MCP resources, tools, prompts | [ ] Pending | High |
| P2C-9 | Create MCP Client Console page | [ ] Pending | High |
| P2C-10 | Connect to MCP servers | [ ] Pending | High |
| P2C-11 | Browse and access resources | [ ] Pending | Medium |
| P2C-12 | Execute tools with parameters | [ ] Pending | Medium |

### Phase 2D: LLM & API Overlay System
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P2D-1 | Build LLM Provider Configuration page | [ ] Pending | Critical |
| P2D-2 | Secure credential storage for OpenAI | [ ] Pending | Critical |
| P2D-3 | Secure credential storage for Azure OpenAI | [ ] Pending | High |
| P2D-4 | Secure credential storage for Anthropic (Claude) | [ ] Pending | High |
| P2D-5 | Secure credential storage for Google (Gemini) | [ ] Pending | High |
| P2D-6 | Add provider connection testing | [ ] Pending | High |
| P2D-7 | Create API Overlay Dashboard | [ ] Pending | High |
| P2D-8 | Monitor incoming LLM connections | [ ] Pending | High |
| P2D-9 | Monitor outgoing API calls | [ ] Pending | High |
| P2D-10 | Show connection statistics and health | [ ] Pending | Medium |

---

## Phase 3: Enterprise Features
**Timeline:** 5-7 days  
**Goal:** Add enterprise management and security capabilities

### Phase 3A: User & Access Management
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P3A-1 | Build User Management page | [ ] Pending | High |
| P3A-2 | Implement RBAC roles UI (Admin, Manager, User, Viewer) | [ ] Pending | High |
| P3A-3 | Create permission matrix editor | [ ] Pending | Medium |
| P3A-4 | Add user invitation system | [ ] Pending | Medium |
| P3A-5 | Create Admin Dashboard | [ ] Pending | High |
| P3A-6 | Show system statistics and health | [ ] Pending | High |
| P3A-7 | Display user activity metrics | [ ] Pending | Medium |
| P3A-8 | Show resource usage graphs | [ ] Pending | Medium |

### Phase 3B: Security & Compliance
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P3B-1 | Build Security Dashboard | [ ] Pending | High |
| P3B-2 | Display MFA enrollment status | [ ] Pending | High |
| P3B-3 | Show active sessions management | [ ] Pending | High |
| P3B-4 | Integrate vulnerability scan results | [ ] Pending | Medium |
| P3B-5 | Add security alerts and notifications | [ ] Pending | Medium |
| P3B-6 | Create Compliance Center page | [ ] Pending | High |
| P3B-7 | Show regulatory framework status (GDPR, HIPAA, SOX, etc.) | [ ] Pending | High |
| P3B-8 | Display EU AI Act compliance (Articles 13, 53) | [ ] Pending | High |
| P3B-9 | Provide audit trail viewer with 7-year retention | [ ] Pending | Medium |
| P3B-10 | Add compliance report generation | [ ] Pending | Medium |

### Phase 3C: API & External Connections
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P3C-1 | Build UKG API Key Management page | [ ] Pending | Critical |
| P3C-2 | Create new API keys for external apps | [ ] Pending | Critical |
| P3C-3 | Revoke/rotate API keys | [ ] Pending | High |
| P3C-4 | Set key permissions and rate limits | [ ] Pending | High |
| P3C-5 | Track API key usage | [ ] Pending | Medium |
| P3C-6 | Build External Connection Manager | [ ] Pending | High |
| P3C-7 | Configure external API endpoints | [ ] Pending | High |
| P3C-8 | Manage webhook subscriptions | [ ] Pending | High |
| P3C-9 | Test external connections | [ ] Pending | Medium |
| P3C-10 | Monitor connection health | [ ] Pending | Medium |

### Phase 3D: Organization & Documentation
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P3D-1 | Build Activity/Audit Log Viewer | [ ] Pending | High |
| P3D-2 | Add searchable user actions log | [ ] Pending | High |
| P3D-3 | Show system events timeline | [ ] Pending | Medium |
| P3D-4 | Add log export functionality | [ ] Pending | Medium |
| P3D-5 | Create Projects/Workspaces page | [ ] Pending | Medium |
| P3D-6 | Organize simulations by project | [ ] Pending | Medium |
| P3D-7 | Add project sharing and collaboration | [ ] Pending | Low |
| P3D-8 | Build Help Center page | [ ] Pending | Medium |
| P3D-9 | Add interactive documentation | [ ] Pending | Medium |
| P3D-10 | Include video tutorials (placeholder) | [ ] Pending | Low |
| P3D-11 | Add FAQ section | [ ] Pending | Low |

---

## Phase 4: Advanced Observability
**Timeline:** 3-5 days  
**Goal:** Implement extended enterprise dimensions (Axes 14-17)

### Phase 4A: Monitoring & Analytics (Axis 17)
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P4A-1 | Build Observability Dashboard | [ ] Pending | High |
| P4A-2 | Add real-time performance metrics | [ ] Pending | High |
| P4A-3 | Create SLA tracking and alerts | [ ] Pending | Medium |
| P4A-4 | Add custom metric dashboards | [ ] Pending | Medium |
| P4A-5 | Implement anomaly detection visualization | [ ] Pending | Low |

### Phase 4B: Advanced Features
| Task ID | Description | Status | Priority |
|---------|-------------|--------|----------|
| P4B-1 | Create Federated Data Manager (Axis 15) | [ ] Pending | Medium |
| P4B-2 | Add cross-system data synchronization UI | [ ] Pending | Medium |
| P4B-3 | Show federated query results | [ ] Pending | Medium |
| P4B-4 | Build Time-Based Knowledge Explorer (Axis 16) | [ ] Pending | Medium |
| P4B-5 | Add temporal navigation timeline | [ ] Pending | Medium |
| P4B-6 | Show knowledge evolution over time | [ ] Pending | Low |
| P4B-7 | Create Quantum State Visualizer (Layer 8) | [ ] Pending | Low |
| P4B-8 | Visualize parallel state exploration | [ ] Pending | Low |
| P4B-9 | Add quantum trust fidelity metrics | [ ] Pending | Low |

---

## Summary Statistics

| Phase | Sub-Phase | Tasks | Priority Distribution |
|-------|-----------|-------|----------------------|
| **Phase 1** | 1A + 1B | 11 | 5 Critical, 5 High, 1 Medium |
| **Phase 2** | 2A-2D | 40 | 6 Critical, 25 High, 9 Medium |
| **Phase 3** | 3A-3D | 33 | 3 Critical, 20 High, 9 Medium, 1 Low |
| **Phase 4** | 4A-4B | 14 | 0 Critical, 4 High, 7 Medium, 3 Low |
| **TOTAL** | | **98** | **14 Critical, 54 High, 26 Medium, 4 Low** |

---

## Page Inventory

### New Pages to Create (25+)

| Page | Route | Phase | Backend Exists |
|------|-------|-------|----------------|
| Enterprise Chat | `/chat` | 2A | Yes |
| Quad Persona Dashboard | `/persona-dashboard` | 2A | Yes |
| 17-Axis Explorer | `/axes` | 2B | Yes |
| Knowledge Algorithm Browser | `/algorithms` | 2B | Yes |
| 10-Layer Simulation Monitor | `/simulation-monitor` | 2B | Yes |
| Truth Engine Monitor | `/truth-engine` | 2C | Yes |
| MCP Server Manager | `/mcp/servers` | 2C | Yes |
| MCP Client Console | `/mcp/console` | 2C | Yes |
| LLM Provider Config | `/settings/llm` | 2D | Partial |
| API Overlay Dashboard | `/api-dashboard` | 2D | Partial |
| User Management | `/admin/users` | 3A | Yes |
| Admin Dashboard | `/admin` | 3A | Partial |
| Security Dashboard | `/security` | 3B | Yes |
| Compliance Center | `/compliance` | 3B | Yes |
| API Key Management | `/settings/api-keys` | 3C | Partial |
| External Connections | `/settings/connections` | 3C | Partial |
| Audit Log Viewer | `/admin/logs` | 3D | Yes |
| Projects/Workspaces | `/projects` | 3D | No |
| Help Center | `/help` | 3D | No |
| Observability Dashboard | `/observability` | 4A | Yes |
| Federated Data Manager | `/federated` | 4B | Yes |
| Time-Based Explorer | `/timeline` | 4B | Yes |
| Quantum State Visualizer | `/quantum` | 4B | Yes |

### Existing Pages to Fix

| Page | Current Route | Issue |
|------|---------------|-------|
| Simulation | `/simulation` | 404 error |
| Knowledge | `/knowledge` | May not be connected |
| Graph | `/graph` | May not be connected |
| Chatbot | `/chatbot` | May not be connected |
| Analytics | `/analytics` | May not be connected |
| Persona Demo | `/persona-demo` | Orphaned template |

---

## Technical Notes

### Backend Systems Already Implemented

1. **17-Axis Framework** - Full implementation (Axes 1-17)
2. **10-Layer Simulation Stack** - Layers 1-10 fully implemented
3. **58+ Knowledge Algorithms** - KA-01 through KA-58
4. **MCP System** - Servers, clients, resources, tools, prompts
5. **Truth Engine** - TruthCore, TruthGate, TruthMemory, TruthLink
6. **Quad Persona Engine** - Analyst, Expert, Critic, Synthesizer
7. **Security System** - MFA, RBAC, encryption, audit logging
8. **Location Context Engine** (Axis 12)
9. **Temporal Logic Engine** (Axis 13)
10. **Risk & Confidence** (Axis 14)
11. **Federated Intelligence** (Axis 15)
12. **Arrows of Time** (Axis 16)
13. **Observability & Analytics** (Axis 17)

### LLM Provider Support

| Provider | Environment Variable | Status |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | Installed via Replit |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` | Supported |
| Anthropic | `ANTHROPIC_API_KEY` | Supported |
| Google Gemini | `GOOGLE_API_KEY` | Supported |
| Provider Selector | `MODEL_PROVIDER` | `openai \| azure \| anthropic \| gemini` |

### Security Considerations

- API keys stored using Replit Secrets (never in code)
- User-provided LLM credentials use secure server-side storage
- EU AI Act compliance built into Truth Engine
- 7-year audit trail retention for compliance

---

## Next Steps

1. **Approve this plan** and switch to Build mode
2. **Begin Phase 1A** - Route consolidation
3. **Complete Phase 1** before moving to Phase 2
4. **Review progress** after each sub-phase

---

*Document maintained by: Development Team*  
*Last updated: December 18, 2025*
