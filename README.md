# Universal Knowledge Graph (UKG) System

> Enterprise-grade AI-powered knowledge management platform featuring a 17-axis knowledge framework, 10-layer simulation engine, Truth Engine v7.3, and comprehensive MCP integration.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-green)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue)](https://www.postgresql.org/)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [17-Axis Knowledge Framework](#17-axis-knowledge-framework)
- [Truth Engine v7.3](#truth-engine-v73)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Overview

The Universal Knowledge Graph (UKG) is a sophisticated full-stack enterprise application that implements multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis. It combines advanced knowledge organization across 17 dimensions with a powerful simulation engine and Quad Persona system.

The system provides:

- **17-Axis Knowledge Framework** - Comprehensive multi-dimensional knowledge organization
- **10-Layer Simulation Engine** - Progressive query processing and deep synthesis
- **58+ Knowledge Algorithms** - Specialized processing for various knowledge operations
- **Quad Persona Engine** - Multi-perspective analysis (Analyst, Expert, Critic, Synthesizer)
- **Truth Engine v7.3** - Adaptive reasoning with TruthCore, TruthGate, TruthMemory, TruthLink
- **Model Context Protocol (MCP)** - LLM-agnostic middleware for AI integration

## Features

### Core Capabilities

- **Knowledge Graph Management** - Create, query, and visualize complex knowledge structures
- **Multi-Layer Simulation** - Progressive query refinement through 10 specialized layers
- **User Authentication** - Secure session-based login with RBAC (admin/analyst/user/viewer)
- **Interactive Visualizations** - D3.js-powered graph visualization with zoom, pan, and filtering
- **RESTful API** - Comprehensive endpoints with Swagger UI documentation
- **PostgreSQL Database** - Production-ready with Neon-backed cloud database
- **Expert Persona Simulation** - AI-powered knowledge synthesis with quad persona approach
- **Compliance Features** - EU AI Act compliant with decision logging and 7-year audit trails

### Available Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Landing page with system overview |
| Dashboard | `/dashboard` | User dashboard (authenticated) |
| Knowledge Browser | `/knowledge` | 17-axis framework browser with pillars, sectors, domains |
| Graph Visualization | `/graph` | Interactive D3.js knowledge graph |
| AI Chat | `/chatbot` | AI-powered chat with Quad Persona Engine |
| Simulations | `/simulations` | Simulation management |
| Analytics | `/analytics` | System analytics and metrics |
| Truth Engine | `/truth-engine` | Truth Engine v7.3 monitoring dashboard |
| Algorithms | `/algorithms` | Knowledge Algorithm browser (KA-001 to KA-058+) |
| Persona Trace | `/persona-trace` | Quad Persona tracing dashboard |
| Axis Explorer | `/axis-explorer` | 17-Axis coordinate explorer |
| MCP Server | `/mcp-server` | MCP Server Manager |
| API Docs | `/api/docs` | Swagger UI API documentation |
| Admin | `/admin` | Admin dashboard (admin users only) |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/ukg-system.git
cd ukg-system

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export SESSION_SECRET="your-secret-key"

# Seed the database
python seed_data.py

# Run the application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Architecture

### Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.x, Python 3.11 |
| Database | PostgreSQL (Neon-backed) |
| ORM | SQLAlchemy |
| Frontend | Jinja2 Templates, Bootstrap 5 |
| Visualization | D3.js |
| AI Integration | OpenAI (via Replit AI Integrations) |
| API Docs | Swagger UI (OpenAPI 3.0) |

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Truth Engine v7.3                        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  TruthCore   │  TruthGate   │ TruthMemory  │  TruthLink    │
│  (Reasoning) │  (Security)  │   (Audit)    │  (Events)     │
├──────────────┴──────────────┴──────────────┴───────────────┤
│                 10-Layer Simulation Stack                   │
├─────────────────────────────────────────────────────────────┤
│              Quad Persona Engine (Axes 8-11)               │
│        Analyst | Expert | Critic | Synthesizer             │
├─────────────────────────────────────────────────────────────┤
│              17-Axis Knowledge Framework                    │
│    Pillars | Sectors | Domains | Branches | Nodes | ...    │
├─────────────────────────────────────────────────────────────┤
│                   PostgreSQL Database                       │
└─────────────────────────────────────────────────────────────┘
```

## 17-Axis Knowledge Framework

The system organizes knowledge across 17 dimensions:

### Hierarchical Core (Axes 1-5)
| Axis | Name | Description |
|------|------|-------------|
| 1 | Pillar Levels | Hierarchical knowledge pillars (PL-1 to PL-107) |
| 2 | Sectors | Worldwide industry sectors with NAICS mappings |
| 3 | Honeycomb Domains | Hexagonal knowledge expansion |
| 4 | Branches | Hierarchical knowledge trees |
| 5 | Nodes | Atomic knowledge units |

### Crosswalk Systems (Axes 6-7)
| Axis | Name | Description |
|------|------|-------------|
| 6 | Octopus Crosswalk | One-to-many relationships |
| 7 | Spiderweb Crosswalk | Many-to-many relationships |

### Expert Personas (Axes 8-11)
| Axis | Name | Description |
|------|------|-------------|
| 8 | Knowledge Expert | Subject matter expertise |
| 9 | Qualification Expert | Certification and credentials |
| 10 | Regulatory Expert | Regulatory frameworks |
| 11 | Compliance Expert | Compliance requirements |

### Context Dimensions (Axes 12-13)
| Axis | Name | Description |
|------|------|-------------|
| 12 | Location Context | Geographic and jurisdictional |
| 13 | Temporal Context | Time-based context |

### Extended Enterprise (Axes 14-17)
| Axis | Name | Description |
|------|------|-------------|
| 14 | Risk & Confidence | Risk assessment and confidence levels |
| 15 | Federated Intelligence | Distributed knowledge sources |
| 16 | Arrows of Time | Temporal flow and causality |
| 17 | Observability & Analytics | Metrics and monitoring |

## Truth Engine v7.3

The core orchestration layer comprising four components:

### TruthCore
- Adaptive reasoning engine with 5-tier workflows (Trivial to Autonomous)
- LLM Router for task-based model selection
- 12-step refinement process for deep synthesis
- Bias and safety scans

### TruthGate
- Security gateway enforcing zero-trust principles
- Budget controls and priority queues
- EU AI Act compliance (Article 53, Article 13)

### TruthMemory
- SHA-256 hash chain for immutable audit trails
- 7-year retention for artifacts (EU AI Act compliant)
- LRU caching and MLflow-style metrics

### TruthLink
- Event bus for inter-module messaging
- Publish/subscribe patterns with priority routing
- SSE transport for real-time events

## API Documentation

Interactive API documentation is available at `/api/docs` via Swagger UI.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/graph` | GET | Get graph data (nodes, edges, pillars, sectors, domains) |
| `/api/nodes` | GET/POST | List or create nodes |
| `/api/simulations` | GET/POST | Simulation management |
| `/api/chat/message` | POST | AI chat with Quad Persona |
| `/api/mcp/capabilities` | GET | MCP capabilities |

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
├── static/                # Static assets (CSS, JS, images)
├── quad_persona/          # Quad Persona Engine
├── simulation/            # 10-Layer Simulation Stack
├── knowledge_algorithms/  # 58+ Knowledge Algorithms
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `OPENAI_API_KEY` | OpenAI API key (via Replit AI) | For AI features |
| `FLASK_ENV` | Environment (development/production) | No |

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Run tests
pytest tests/
```

## Deployment

The application is configured for deployment on Replit with:
- Gunicorn WSGI server
- PostgreSQL (Neon-backed)
- Automatic HTTPS via Replit proxy

### Production Configuration

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port main:app
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

## Security

- Session-based authentication with CSRF protection
- Security headers middleware
- Rate limiting
- Request size limits
- Input validation
- Adversarial input detection
- Role-based access control (RBAC)

See [SECURITY.md](SECURITY.md) for security policies and reporting vulnerabilities.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Recent Updates

### Phase 5 (December 2024)
- Connected frontend to real database data
- `/api/graph` returns nodes, edges, pillars, sectors, domains
- Updated Knowledge Browser with tabbed interface for 17-axis framework

### Phase 4 (December 2024)
- Seeded database with 86 records (17 pillars, 15 sectors, 13 domains, 25 nodes, 16 edges)
- Added Swagger UI API documentation at `/api/docs`

### Previous Phases
- Phase 3: Testing infrastructure and admin features
- Phase 2: Core implementation and simulation engine
- Phase 1: Security hardening
- Phase 0: Emergency security fixes

## Support

For support, please open an issue on the GitHub repository or contact the development team.

---

Built with Flask, PostgreSQL, and D3.js on Replit.
