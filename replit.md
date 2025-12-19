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

Security features include session-based authentication, CSRF protection, security headers, rate limiting, request size limits, input validation, and adversarial input detection. Compliance features adhere to the EU AI Act, including detailed decision logging, explainability endpoints, 7-year audit trail retention, and PII detection.

## Recent Changes (December 2024)
- Fixed KnowledgeNode model: Renamed `metadata` column to `node_metadata` to avoid SQLAlchemy reserved attribute conflict
- Created missing templates: knowledge.html, graph.html, chatbot.html, analytics.html, settings.html, admin/dashboard.html
- Added LLM Provider configuration page at `/llm-providers` for managing AI model integrations
- Updated navigation with links to Knowledge, Graph, Simulations, and AI Chat
- Route consolidation: Fixed route imports in main.py to properly load routes.py
- Added Truth Engine Monitor page at `/truth-engine` showing TruthCore, TruthGate, TruthMemory, TruthLink status
- Added Knowledge Algorithms page at `/algorithms` for browsing and executing 58+ algorithms
- Enhanced Chat UI with markdown rendering (via marked.js) and streaming response support

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

## External Dependencies
- **Database**: PostgreSQL (Neon-backed via Replit)
- **AI/ML Services**: OpenAI (via Replit AI Integrations)
- **Visualization Libraries**: D3.js
- **Web Framework**: Flask
- **ORM**: SQLAlchemy
- **Frontend Framework**: Bootstrap 5