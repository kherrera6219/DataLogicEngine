# DataLogicEngine Developer Guide

**Last Updated:** 2026-01-12  
**Version:** 1.0

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd DataLogicEngine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your configuration

# Initialize database
flask db upgrade

# Run development server
python run.py
```

---

## Project Structure

```
DataLogicEngine/
├── app.py                 # Flask application factory
├── config.py              # Configuration classes
├── models.py              # SQLAlchemy models (core)
├── extensions.py          # Flask extensions init
├── backend/
│   ├── security/          # Auth, CSRF, headers
│   ├── tracing/           # Enterprise traceability
│   ├── llm_gateway/       # LLM provider abstraction
│   └── *.py               # Core services
├── core/
│   ├── engine/            # KA engine, simulation
│   ├── graph/             # Knowledge graph
│   └── algorithms/        # Processing algorithms
├── knowledge_algorithms/  # 58+ KA implementations
├── quad_persona/          # Quad persona engine
├── simulation/            # 10-layer simulation stack
├── routes/                # Flask blueprints
├── tests/                 # Test suites
└── docs/                  # Documentation
```

---

## Key Concepts

### 17-Axis Knowledge Framework

The system uses a 17-dimensional coordinate system:
- **Axes 1-7**: Knowledge organization (Pillar, Sector, Honeycomb, Branch, Node, Octopus, Spiderweb)
- **Axes 8-11**: Personas (Knowledge, Sector, Regulatory, Compliance experts)
- **Axes 12-13**: Context (Location, Time)
- **Axes 14-17**: Meta (Risk, Performance, Ethics, Learning)

### Quad Persona Engine

Four AI personas debate each query:
1. **Knowledge Expert** - Domain accuracy
2. **Sector Expert** - Industry applicability
3. **Regulatory Expert** - Compliance requirements
4. **Compliance Expert** - Internal policy alignment

### 10-Layer Simulation Stack

Queries flow through 10 processing layers with recursive refinement until confidence threshold (≥99.5%) is met.

---

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/integration/test_api_endpoints.py -v

# Load testing (requires locust)
locust -f tests/performance/locustfile.py
```

### Code Quality

```bash
# Linting
pylint backend/ core/

# Security scan
bandit -r . -ll --exclude .venv,tests

# Type checking (if using mypy)
mypy backend/
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

---

## API Development

### Adding a New Endpoint

1. Create route in `routes/` or add to existing blueprint
2. Add schema validation in `backend/schemas/`
3. Write integration test in `tests/integration/`
4. Update Postman collection in `docs/api/`

### Authentication

All API endpoints (except `/health`, `/api/v1/auth/*`) require authentication:
- Session-based for web UI
- API key for programmatic access (header: `X-API-Key`)

### Rate Limiting

Default limits configured in `.env`:
- Global: 200 requests/hour
- Auth endpoints: 5 requests/minute

---

## Environment Variables

See `.env.template` for full list. Key variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Session encryption (64-char hex) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis for caching/rate limiting |
| `AZURE_OPENAI_*` | LLM provider credentials |

---

## Troubleshooting

### Common Issues

**Database connection failed:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Redis connection failed:**
```bash
# Check Redis is running
redis-cli ping
```

**Import errors:**
```bash
# Ensure virtual environment is activated
which python  # Should show .venv path
```

---

## Resources

- [API Documentation](/api/docs) - Swagger UI
- [Production Readiness](PRODUCTION_READINESS.md)
- [Deployment Checklist](../deploy/DEPLOYMENT_CHECKLIST.md)
- [Architecture Whitepapers](whitepapers/)
