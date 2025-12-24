# Universal Knowledge Graph (UKG) System

## Overview
This project develops a Universal Knowledge Graph (UKG) and Universal Simulated Knowledge Database (USKD) system. Its purpose is to provide multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis. The system is built around a 17-Axis knowledge framework and orchestrated by the Truth Engine v7.3. The business vision is to offer a comprehensive, AI-driven platform for advanced knowledge management and simulated intelligence, with significant market potential in data analysis, strategic planning, and AI-assisted decision-making across various industries.

## User Preferences
- Clean, production-ready design
- Bootstrap-based UI with dark theme option
- Material icons for visual elements
- Comprehensive error handling
- Truth Engine enhancement over replacement philosophy

## System Architecture

### UI/UX Decisions
The front-end uses HTML/CSS/JavaScript with Bootstrap 5, favoring a clean, production-ready design with a dark theme option and Material icons for visual elements. Interactive D3.js-based visualizations are used for knowledge graphs, supporting zoom, pan, drag, filtering, and real-time updates.

### Technical Implementations
The system is built on Flask (Python 3.11) with SQLAlchemy ORM and PostgreSQL. It integrates OpenAI via Replit AI Integrations for AI capabilities.
Key features include:
- **17-Axis Knowledge Framework**: A comprehensive framework for organizing and synthesizing knowledge across 17 dimensions, including core knowledge (e.g., Pillar Levels, Sectors, Topics, Methods, Tools) and extended enterprise dimensions (Risk & Confidence, Federated Intelligence, Arrows of Time, Observability & Analytics).
- **Unified Coordinate System**: A 17-dimensional coordinate system (K ≡ x1..x17) using Nuremberg-style hierarchical numbering for indexing all knowledge elements. Features include:
  - Axes 1-5: Hierarchical core (Pillars → Sectors → Honeycomb → Branches → Nodes)
  - Axes 6-7: Crosswalk systems (Octopus one-to-many, Spiderweb many-to-many)
  - Axes 8-11: Expert roles (Knowledge, Qualifications, Regulatory, Compliance)
  - Axes 12-13: Context (Location, Temporal)
  - Axes 14-17: Extended enterprise (Risk & Confidence, Federated Intelligence, Arrows of Time, Observability & Analytics)
  - Meta-tag overlays for preserving original naming (FAR, DFARS, NAICS, ISO, NIST, etc.)
  - Dynamic traversal via Honeycomb, Octopus, and Spiderweb node systems
- **10-Layer Simulation Stack**: A sophisticated simulation engine that supports knowledge base retrieval, multi-persona expert simulation (Analyst, Expert, Critic, Synthesizer), reasoning, integration, pattern recognition, and advanced AI capabilities including AGI, Quantum Computing, Recursive Core, and Self-Awareness.
- **AI Chat**: Context-aware conversations with history tracking, multi-perspective analysis using the quad persona approach, and real-time streaming responses, enhanced by TruthCore's tier-based processing.
- **Simulations**: Creation and management of various simulation types with pagination and export functionalities.
- **Quad Persona Mathematical Framework**: Enhanced persona processing implementing:
  - Knowledge Space Mapping M(q,c,t) for similarity-based query routing to 17-axis coordinates
  - Dynamic Weight Functions (α_i(t), β_j(c), γ_k(c,t), δ_l(c,t)) replacing static persona weights
  - Structured Memory Graph G_M with temporal/relevance recall algorithms
  - Deep Recursive Learning with convergence function CF(x_t, x_{t-1}, ε=0.001)
  - 12-Step Refinement Workflow targeting 0.995 confidence threshold
  - Integration Function Ψ for dynamic persona weight synthesis
- **Database Reference Data**: 82 pillars (PL-1-107) with Nuremberg coordinates and 72 AXIS-2 worldwide sector codes with NAICS mappings

### System Design Choices
The core orchestration layer is the **Truth Engine v7.3**, comprising:
- **TruthCore**: An adaptive reasoning engine with 5-tier workflows (Trivial to Autonomous) and an LLM Router for task-based model selection. It includes a 12-step refinement process for deep synthesis and bias/safety scans.
- **TruthGate**: A security gateway enforcing zero-trust principles, budget controls, priority queues, and EU AI Act compliance (Article 53 for decision logging, Article 13 for explainability).
- **TruthMemory**: An audit and persistence layer featuring a SHA-256 hash chain for immutable audit trails, 7-year retention for artifacts (EU AI Act compliant), LRU caching, and MLflow-style metrics.
- **TruthLink**: An event bus facilitating inter-module messaging with publish/subscribe patterns, priority routing, SSE transport for real-time events, and a dead letter queue.

Security features include:
- **Session-based authentication** with Flask-Login
- **CSRF protection** with Flask-WTF tokens on all forms
- **Security headers** middleware (CSP, X-Frame-Options, etc.)
- **Rate limiting** with Flask-Limiter
- **Request size limits** with configurable max content length
- **Correlation ID tracking** for request tracing
- **Production credential validation** (blocks default credentials)
- **MCP authorization** (admin-only for server management)
- **Input validation** and adversarial input detection

Compliance features adhere to the EU AI Act, including detailed decision logging, explainability endpoints, 7-year audit trail retention, and PII detection.

## Recent Changes (December 2025)
- **v1.1.1 Codebase Cleanup**: Removed duplicate files and consolidated structure
- v1.1.1: Removed backup/standalone app files (routes_backup.py, run_simulation.py, simple_app.py)
- v1.1.1: Removed duplicate core modules at root level (kept nested versions in core/*/subfolders)
- v1.1.1: Removed duplicate data files (kept data/ukg/ versions)
- v1.1.1: Removed duplicate persona_api.py from core/ (kept backend/persona_api.py)
- v1.1.1: Consolidated redundant documentation files
- **v1.1.0 Security Hardening**: Production readiness improvements
- v1.1.0: Added CSRF protection with Flask-WTF across all forms and endpoints
- v1.1.0: Added production credential validation (blocks insecure defaults in production)
- v1.1.0: Added MCP endpoint authorization (admin-only for create/delete operations)
- v1.1.0: Added correlation ID middleware for request tracing (X-Correlation-ID header)
- v1.1.0: Fixed blocking asyncio.run() calls with shared event loop helper
- v1.1.0: Updated ARCHITECTURE.md to reflect actual monolithic Flask architecture
- v1.1.0: Updated API.md to document session-based authentication
- v1.1.0: Removed dead Next.js code (pages/ directory) and unused node_modules_old/
- v1.1.0: Standardized project naming to "Universal Knowledge Graph (UKG) System"

## Changes (December 2024)
- **v1.0.1 Patch**: Debugging sweep with fixes for SQLAlchemy warnings and missing dependencies
- v1.0.1: Fixed SQLAlchemy relationship warnings with proper back_populates in db_models.py
- v1.0.1: Installed missing pyotp and qrcode packages for MFA module
- v1.0.1: Created data/personas_db.json to eliminate startup warnings
- v1.0.1: Integration tests improved to 32 passing, total 140+ tests passing
- **v1.0.0 Release**: Production-ready application with all core features operational
- v1.0.0: Split routes.py (736 lines) into 4 modular blueprint files (auth, page, api, admin)
- v1.0.0: Created @admin_required decorator for centralized access control
- v1.0.0: Fixed test assertion field name mismatches - 93% test pass rate (150/161)
- v1.0.0: Configured production deployment settings

## Available Pages
- `/` - Home page (landing)
- `/dashboard` - User dashboard (authenticated)
- `/knowledge` - Knowledge base browser
- `/graph` - Interactive D3.js knowledge graph visualization
- `/chatbot` - AI-powered chat with Quad Persona Engine (markdown + streaming)
- `/simulations` - Simulation management
- `/analytics` - System analytics and metrics
- `/settings` - User settings
- `/profile` - User profile and API key management
- `/llm-providers` - LLM provider configuration status
- `/truth-engine` - Truth Engine v7.3 monitoring dashboard
- `/algorithms` - Knowledge Algorithm browser (KA-001 to KA-058+)
- `/persona-trace` - Quad Persona Tracing Dashboard (Analyst/Expert/Critic/Synthesizer)
- `/axis-explorer` - 17-Axis Coordinate Explorer with D3.js visualization
- `/simulation-monitor` - 10-Layer Simulation Monitor with real-time visualization
- `/mcp-server` - MCP Server Manager for protocol configuration
- `/mcp-client` - MCP Client Console for testing endpoints
- `/api-overlay` - API Overlay Dashboard showing LLM connections
- `/admin` - Admin dashboard (admin users only)
- `/admin/users` - User Management with RBAC roles/permissions
- `/admin/audit` - Audit Log with event filtering and compliance info
- `/admin/settings` - System Settings for configuring global parameters
- `/api/docs` - Swagger UI API documentation

## External Dependencies
- **Database**: PostgreSQL (Neon-backed via Replit)
- **AI/ML Services**: OpenAI (via Replit AI Integrations)
- **Visualization Libraries**: D3.js
- **Web Framework**: Flask
- **ORM**: SQLAlchemy
- **Frontend Framework**: Bootstrap 5

## Project Structure
```
├── app.py                 # Flask application setup
├── main.py                # Application entry point
├── routes.py              # Route definitions
├── models.py              # SQLAlchemy models (User, Session)
├── db_models.py           # Knowledge graph models (17-axis)
├── extensions.py          # Flask extensions
├── seed_data.py           # Database seeding script
├── backend/
│   ├── ai_chat.py         # AI chat implementation
│   ├── ka_api.py          # Knowledge Algorithm API
│   ├── mcp/               # Model Context Protocol
│   ├── truth_engine/      # Truth Engine v7.3
│   └── security/          # Security middleware
├── templates/             # Jinja2 templates
├── static/                # Static assets and swagger.json
├── quad_persona/          # Quad Persona Engine
├── simulation/            # 10-Layer Simulation Stack
├── knowledge_algorithms/  # 58+ Knowledge Algorithms
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## Registered API Blueprints
| Blueprint | URL Prefix | Description |
|-----------|------------|-------------|
| mcp_bp | /api/mcp | Model Context Protocol server management |
| ai_chat_bp | /api/ai | AI-powered chat with streaming |
| ka_bp | /api/ka | Knowledge Algorithm API (58+ algorithms) |
| truth_api | /api/truth | Truth Engine v7.3 API |
| persona_api | /api/persona | Quad Persona Engine API |
| pillar_api | /api/pillars | Pillar Levels (Axis 1) management |
| compliance_api | /api/compliance | Compliance checking API |
| swaggerui | /api/docs | Interactive API documentation |

## Version History
| Version | Date | Phase | Description |
|---------|------|-------|-------------|
| **1.1.0** | **Dec 23, 2025** | **Security** | **Security hardening & production readiness** |
| 1.0.0 | Dec 19, 2024 | Release | Production-ready release with all core features |
| 0.6.0 | Dec 19, 2024 | Phase 7 | Code organization & blueprint registration |
| 0.5.0 | Dec 19, 2024 | Phase 5 | Frontend-database integration |
| 0.4.0 | Dec 19, 2024 | Phase 4 | Database seeding & API docs |
| 0.3.1 | Dec 18, 2024 | Phase 3B | Admin features |
| 0.3.0 | Dec 17, 2024 | Phase 3 | Testing infrastructure |
| 0.2.0 | Dec 15, 2024 | Phase 2 | Core implementation |
| 0.1.1 | Dec 10, 2024 | Phase 1 | Security hardening |

## Running the Application
```bash
# Start the server
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Seed the database (if needed)
python seed_data.py
```