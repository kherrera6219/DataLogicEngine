# Universal Knowledge Graph (UKG) System

> Enterprise-grade AI-powered knowledge management platform featuring a 17-axis knowledge framework, 10-layer simulation engine, Truth Engine v7.3, and comprehensive MCP integration.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-green)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/tests-164-brightgreen)](tests/)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Universal Knowledge Graph (UKG) is a sophisticated full-stack enterprise application that implements multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis.

### Core Capabilities

| Feature                      | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| **17-Axis Framework**        | Multi-dimensional knowledge organization                             |
| **10-Layer Simulation**      | Progressive query processing and deep synthesis                      |
| **58+ Knowledge Algorithms** | Specialized processing (KA-001 to KA-058+)                           |
| **Quad Persona Engine**      | Multi-perspective analysis (Analyst, Expert, Critic, Synthesizer)    |
| **Truth Engine v7.3**        | Adaptive reasoning with TruthCore, TruthGate, TruthMemory, TruthLink |
| **MCP Integration**          | Model Context Protocol for LLM-agnostic AI integration               |

---

## Features

### Security ✅

- MFA/TOTP authentication
- CSRF protection with Flask-WTF
- Security headers middleware
- Rate limiting (Redis-backed)
- Request timeout protection
- API key authentication
- Role-based access control (RBAC)
- Audit logging with correlation IDs

### Infrastructure ✅

- PostgreSQL with connection pooling (pool_size=20, max_overflow=40)
- Redis configuration for caching and rate limiting
- Response compression (gzip/brotli)
- Alembic database migrations
- CI/CD with GitHub Actions

### UI/UX ✅

- 32 responsive template pages
- Interactive D3.js knowledge graph visualization
- Admin dashboard
- Swagger UI API documentation

### Available Pages

| Page                | Route           | Description                 |
| ------------------- | --------------- | --------------------------- |
| Home                | `/`             | Landing page                |
| Dashboard           | `/dashboard`    | User dashboard              |
| Knowledge Browser   | `/knowledge`    | 17-axis framework browser   |
| Graph Visualization | `/graph`        | Interactive knowledge graph |
| AI Chat             | `/chatbot`      | AI chat with Quad Persona   |
| Simulations         | `/simulations`  | Simulation management       |
| Truth Engine        | `/truth-engine` | Truth Engine dashboard      |
| Algorithms          | `/algorithms`   | Knowledge Algorithm browser |
| MCP Server          | `/mcp-server`   | MCP Server Manager          |
| Admin               | `/admin`        | Admin dashboard             |
| API Docs            | `/api/docs`     | Swagger UI                  |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy template)
cp .env.template .env
# Edit .env with your settings

# Initialize database
flask db upgrade
python backend/seed_data.py

# Run the application
python main.py
# Or with gunicorn:
gunicorn --bind 0.0.0.0:5000 main:app
```

---

## Architecture

### Technology Stack

| Layer      | Technology                    |
| ---------- | ----------------------------- |
| Backend    | Flask 3.x, Python 3.11        |
| Database   | PostgreSQL 15+                |
| ORM        | SQLAlchemy 2.x                |
| Migrations | Alembic / Flask-Migrate       |
| Caching    | Redis / Flask-Caching         |
| Task Queue | Celery                        |
| Frontend   | Jinja2, Bootstrap 5, D3.js    |
| API Docs   | Swagger UI (OpenAPI 3.0)      |
| Security   | Flask-Login, Flask-WTF, pyotp |

### System Architecture

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
├─────────────────────────────────────────────────────────────┤
│              17-Axis Knowledge Framework                    │
├─────────────────────────────────────────────────────────────┤
│           PostgreSQL + Redis + Celery                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
DataLogicEngine/
├── app.py                    # Flask application
├── main.py                   # Entry point
├── config.py                 # Configuration classes
├── extensions.py             # Flask extensions
├── wsgi.py                   # WSGI entry point
│
├── backend/                  # Backend modules (35 files)
│   ├── auth.py              # Authentication logic
│   ├── security/            # Security middleware (17 files)
│   ├── middleware/          # Request middleware
│   ├── truth_engine/        # Truth Engine v7.3 (21 files)
│   └── *.py                 # API modules
│
├── routes/                   # Flask blueprints
│   ├── auth_routes.py
│   ├── page_routes.py
│   ├── api_routes.py
│   └── admin_routes.py
│
├── models/                   # SQLAlchemy models (7 files)
├── simulation/               # 10-Layer simulation (19 files)
├── core/                     # Core business logic (73 files)
├── knowledge_algorithms/     # 58+ KA modules (51 files)
├── quad_persona/            # Quad Persona Engine
│
├── templates/               # Jinja2 templates (32 files)
├── static/                  # Static assets
├── config/                  # Configuration files
├── demos/                   # Demo scripts
├── scripts/                 # Utility scripts
├── tests/                   # Test suite (164 tests)
├── docs/                    # Documentation
└── migrations/              # Alembic migrations
```

---

## Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

| Variable         | Description                     | Required        |
| ---------------- | ------------------------------- | --------------- |
| `DATABASE_URL`   | PostgreSQL connection string    | Yes             |
| `SESSION_SECRET` | Flask session secret (64 chars) | Yes             |
| `SECRET_KEY`     | Application secret key          | Yes             |
| `REDIS_URL`      | Redis connection (for caching)  | Recommended     |
| `OPENAI_API_KEY` | OpenAI API key                  | For AI features |
| `FLASK_ENV`      | `development` or `production`   | Yes             |

See [.env.template](.env.template) for full list.

---

## API Documentation

Interactive API documentation available at `/api/docs` (Swagger UI).

### Key Endpoints

| Endpoint          | Method   | Description          |
| ----------------- | -------- | -------------------- |
| `/api/health`     | GET      | Health check         |
| `/api/v1/graph`   | GET      | Knowledge graph data |
| `/api/v1/ka/*`    | GET/POST | Knowledge Algorithms |
| `/api/v1/truth/*` | GET/POST | Truth Engine         |
| `/api/v1/mcp/*`   | GET/POST | MCP Protocol         |
| `/api/v1/chat/*`  | POST     | AI Chat              |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific category
pytest tests/security/ -v
pytest tests/integration/ -v
```

**Current:** 164 tests

---

## Security

- ✅ MFA/TOTP authentication
- ✅ CSRF protection
- ✅ Security headers
- ✅ Rate limiting
- ✅ Request timeouts
- ✅ Audit logging
- ✅ Password policy (12+ chars, complexity)
- ✅ Account lockout

See [SECURITY.md](SECURITY.md) for security policies and vulnerability reporting.

---

## Roadmap

See [ENTERPRISE_ROADMAP.md](ENTERPRISE_ROADMAP.md) for the full enterprise implementation plan.

### Current Status

- **Phase 1-2:** ✅ Complete (Infrastructure, Security)
- **Phase 3:** 🔄 In Progress (Documentation)
- **Phase 4-5:** 📅 Planned (Features, Performance)

### Known Gaps

See [GAP_ANALYSIS.md](GAP_ANALYSIS.md) for identified gaps and priorities.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Documentation

| Document                                       | Description             |
| ---------------------------------------------- | ----------------------- |
| [SECURITY.md](SECURITY.md)                     | Security policies       |
| [CONTRIBUTING.md](CONTRIBUTING.md)             | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md)                   | Version history         |
| [TODO.md](TODO.md)                             | Current task list       |
| [GAP_ANALYSIS.md](GAP_ANALYSIS.md)             | Gap analysis            |
| [ENTERPRISE_ROADMAP.md](ENTERPRISE_ROADMAP.md) | Enterprise roadmap      |

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
- **Documentation:** [docs/](docs/)

---

_Built with Flask, PostgreSQL, Redis, and D3.js_
