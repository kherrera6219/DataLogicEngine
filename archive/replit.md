# Universal Knowledge Graph (UKG) System

## Overview
This project develops a Universal Knowledge Graph (UKG) and Universal Simulated Knowledge Database (USKD) system. Its purpose is to provide multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis, built around a 17-Axis knowledge framework and orchestrated by the Truth Engine v7.3. The business vision is to offer a comprehensive, AI-driven platform for advanced knowledge management and simulated intelligence, with significant market potential in data analysis, strategic planning, and AI-assisted decision-making.

## User Preferences
- Clean, production-ready design
- Bootstrap-based UI with dark theme option
- Material icons for visual elements
- Comprehensive error handling
- Truth Engine enhancement over replacement philosophy

## System Architecture

### UI/UX Decisions
The front-end uses HTML/CSS/JavaScript with Bootstrap 5, favoring a clean, production-ready design with a dark theme option and Material icons. Interactive D3.js-based visualizations are used for knowledge graphs, supporting zoom, pan, drag, filtering, and real-time updates.

### Technical Implementations
The system is built on Flask (Python 3.11) with SQLAlchemy ORM and PostgreSQL. It integrates OpenAI via Replit AI Integrations for AI capabilities. Key features include:
-   **17-Axis Knowledge Framework**: Organizes and synthesizes knowledge across 17 dimensions, including core knowledge (Pillar Levels, Sectors, Topics, Methods, Tools) and extended enterprise dimensions (Risk & Confidence, Federated Intelligence, Arrows of Time, Observability & Analytics).
-   **Unified Coordinate System**: A 17-dimensional coordinate system (K ≡ x1..x17) using Nuremberg-style hierarchical numbering for indexing all knowledge elements. It includes hierarchical core axes, crosswalk systems, expert roles, context axes, and extended enterprise axes, with meta-tag overlays.
-   **10-Layer Simulation Stack**: A sophisticated simulation engine supporting knowledge base retrieval, multi-persona expert simulation (Analyst, Expert, Critic, Synthesizer), reasoning, integration, pattern recognition, and advanced AI capabilities including AGI, Quantum Computing, Recursive Core, and Self-Awareness.
-   **AI Chat**: Provides context-aware conversations with history tracking, multi-perspective analysis using the quad persona approach, and real-time streaming responses, enhanced by TruthCore's tier-based processing.
-   **Simulations**: Allows creation and management of various simulation types with pagination and export functionalities.
-   **Quad Persona Mathematical Framework**: Implements advanced persona processing including Knowledge Space Mapping, Dynamic Weight Functions, Structured Memory Graph, Deep Recursive Learning, a 12-Step Refinement Workflow, and an Integration Function for dynamic persona weight synthesis.
-   **Database Reference Data**: Includes 82 pillars and 72 AXIS-2 worldwide sector codes with NAICS mappings.

### System Design Choices
The core orchestration layer is the **Truth Engine v7.3**, comprising:
-   **TruthCore**: An adaptive reasoning engine with 5-tier workflows and an LLM Router for task-based model selection, including a 12-step refinement process and bias/safety scans.
-   **TruthGate**: A security gateway enforcing zero-trust principles, budget controls, priority queues, and EU AI Act compliance (Article 53 for decision logging, Article 13 for explainability).
-   **TruthMemory**: An audit and persistence layer featuring a SHA-256 hash chain for immutable audit trails, 7-year retention for artifacts (EU AI Act compliant), LRU caching, and MLflow-style metrics.
-   **TruthLink**: An event bus facilitating inter-module messaging with publish/subscribe patterns, priority routing, SSE transport for real-time events, and a dead letter queue.

Security features include session-based authentication, CSRF protection, security headers middleware, rate limiting, request size limits, correlation ID tracking, production credential validation, and MCP authorization. Compliance features adhere to the EU AI Act, including detailed decision logging, explainability endpoints, 7-year audit trail retention, and PII detection.

## External Dependencies
-   **Database**: PostgreSQL (Neon-backed via Replit)
-   **AI/ML Services**: OpenAI (via Replit AI Integrations)
-   **Visualization Libraries**: D3.js
-   **Web Framework**: Flask
-   **ORM**: SQLAlchemy
-   **Frontend Framework**: Bootstrap 5