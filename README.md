# DataLogicEngine - Universal Knowledge Graph System

> Enterprise-grade AI/ML knowledge management platform featuring a 13-axis knowledge representation system, multi-layer simulation engine, and comprehensive enterprise integrations.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/node-20.x-green)](https://nodejs.org/)
[![Next.js](https://img.shields.io/badge/next.js-14.0.4-black)](https://nextjs.org/)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)
- [Supporting Documents](#supporting-documents)
- [Support](#support)

## 🔴 Production Readiness Status

**Current Status:** ⚠️ **NOT READY FOR PRODUCTION** (Excellent Progress)
**Review Date:** December 7, 2025
**Next Review:** After Phase 3 completion
**Current Phase:** Phase 3 - Testing Infrastructure (PENDING)

### Quick Assessment

| Category | Status |
|----------|--------|
| Architecture | ✅ Excellent (9/10) |
| Security Configuration | ✅ Complete (Phase 0 & 1) |
| Core Implementation | ✅ Complete (Phase 2 - 100%) |
| Testing | 🔴 Minimal Coverage (~2%) |

### Phase Progress

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: Emergency Security Fixes | ✅ Complete | 100% |
| Phase 1: Security Hardening | ✅ Complete | 100% |
| Phase 2: Core Implementation | ✅ Complete | 100% |
| Phase 3: Testing Infrastructure | ⏳ Pending | 0% |

### Critical Issues Status

1. ✅ ~~Default credentials (admin/admin123)~~ - **FIXED (Phase 0)**
2. ✅ ~~Debug mode enabled~~ - **FIXED (Phase 0)**
3. ✅ ~~Secrets in version control~~ - **FIXED (Phase 0)**
4. ✅ ~~Security hardening~~ - **COMPLETE (Phase 1)**
5. 🟢 **Simulation engine** - **100% COMPLETE (Phase 2 - All 10 layers fully implemented & integrated)**
6. 🔴 **Minimal test coverage** - **Requires 80%+ (Phase 3)**

**Phase 1 Complete!** See [PHASE_1_STATUS.md](PHASE_1_STATUS.md) for security hardening details.

**Phase 2 Complete!** See [PHASE_2_STATUS.md](PHASE_2_STATUS.md) for completion summary.

### Production Documentation

**→ [PRODUCTION REVIEW SUMMARY](PRODUCTION_REVIEW_SUMMARY.md)** - Start here!

Detailed documentation:
- **[Production Code Review](docs/PRODUCTION_CODE_REVIEW.md)** - Complete findings (26 issues)
- **[Production Readiness Guide](docs/PRODUCTION_READINESS.md)** - Deployment preparation
- **[Remediation Plan](docs/REMEDIATION_PLAN.md)** - 12-week phased fix plan

**Timeline to Production:** 12 weeks (with full team)

---

## Overview

DataLogicEngine is a sophisticated full-stack enterprise application that implements a **Universal Knowledge Graph (UKG)** system. It combines advanced knowledge organization, multi-dimensional analysis, regulatory compliance tracking, and AI-powered expert persona simulation into a unified platform.

The system provides:

- **13-Axis Knowledge Representation** - Multi-dimensional knowledge organization
- **10-Layer Simulation Engine** - Sophisticated query processing and refinement
- **56+ Knowledge Algorithms** - Specialized processing for various knowledge operations
- **Quad Persona System** - Multi-perspective analysis framework
- **Enterprise Integrations** - Azure AD, OpenAI, Microsoft Graph API support

## Features

### Core Capabilities

- ✅ **Knowledge Graph Management** - Create, query, and visualize complex knowledge structures
- ✅ **Multi-Layer Simulation** - Progressive query refinement through 10 specialized layers
- ✅ **User Authentication** - Secure login/logout with JWT and Azure AD support
- ✅ **Rich UI Components** - 20+ React pages with Chakra UI and D3.js visualizations
- ✅ **RESTful API** - 50+ endpoints for comprehensive system access
- ✅ **Database Support** - PostgreSQL for production, SQLite for development
- ✅ **Expert Persona Simulation** - AI-powered knowledge, sector, regulatory, and compliance experts
- ✅ **Regulatory Compliance** - SOC2 reporting, framework mapping, compliance dashboards
- ✅ **Enterprise Security** - Comprehensive audit logging and role-based access control

### 13-Axis Knowledge Framework

1. **Axis 1: Pillar Level** - Knowledge hierarchy (48 knowledge pillars, PL1-PL100)
2. **Axis 2: Industry Sector** - Domain categorization
3. **Axis 3: Honeycomb System** - Hexagonal knowledge expansion and exploration
4. **Axis 4: Branch System** - Hierarchical knowledge trees with multiple inheritance
5. **Axis 5: Node System** - Atomic knowledge units and relationships
6. **Axis 6: Octopus Node** - Regulatory framework mapping (multi-tentacle structure)
7. **Axis 7: Spiderweb Node** - Compliance tracking and dependencies
8. **Axis 8: Knowledge Expert Persona** - AI-powered domain expertise
9. **Axis 9: Sector Expert Persona** - Industry-specific expert simulation
10. **Axis 10: Regulatory Expert Persona** - Regulatory compliance guidance
11. **Axis 11: Compliance Expert Persona** - Compliance implementation support
12. **Axis 12: Location Context** - Geographic knowledge organization
13. **Axis 13: Temporal & Causal Logic** - Time and causality modeling

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (optional - SQLite works for development)

### Installation (5 minutes)

For a detailed readiness checklist and known gaps, see [docs/runtime_gap_analysis.md](docs/runtime_gap_analysis.md).

```bash
# 1. Clone the repository
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Configure environment (already set up for development)
# .env file is pre-configured with SQLite database

# 5. Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# 6. Run a quick environment precheck (optional but recommended)
python scripts/runtime_precheck.py

# 7. Start the backend (Terminal 1)
python main.py  # serves on http://localhost:8080 by default

# 8. Start the frontend (Terminal 2)
cd frontend && npm run dev
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8080
- **API Documentation:** http://localhost:8080/swagger
- **Admin Setup:** 🔐 **SECURITY:** Set secure admin credentials in your `.env` file
  - Generate credentials using: `python3 -c "import secrets, string; print(f'Username: admin_{secrets.token_hex(6)}'); alphabet = string.ascii_letters + string.digits + string.punctuation; print(f'Password: {repr(''.join(secrets.choice(alphabet) for _ in range(32)))}')"`
  - See [SECRETS.md](SECRETS.md) for complete secrets management guide
  - See [Production Readiness Guide](docs/PRODUCTION_READINESS.md) for deployment preparation

## Architecture

### Technology Stack

#### Frontend
- **Framework**: Next.js 14.0.4 with React 18.2.0
- **UI Libraries**: Chakra UI 2.10.8, Microsoft Fluent UI 9.64.0, React Bootstrap 2.9.1
- **Visualization**: D3.js 7.9.0, React Force Graph 2D 1.27.1
- **Animation**: Framer Motion
- **Styling**: CSS Modules, Bootstrap 5.3

#### Backend
- **Framework**: Flask 3.1.1 with Gunicorn 23.0.0
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0.41
- **Authentication**: Flask-Login 0.6.3, JWT (PyJWT 2.10.1), Azure AD (Flask-Dance 7.1.0)
- **APIs**: Flask-CORS, Flask-Swagger-UI
- **AI Integration**: OpenAI API 1.79.0, Azure OpenAI
- **Graph Processing**: NetworkX 3.4.2, NumPy 2.2.6, Pandas

#### Infrastructure
- **Server**: Gunicorn WSGI server
- **Deployment**: Replit, Docker-ready
- **Architecture**: Microservices with API Gateway pattern
- **Monitoring**: Comprehensive logging (security, audit, compliance)

### Microservices Architecture

- **API Gateway** (Port 5000) - Request routing, authentication, rate limiting
- **Core UKG Service** (Port 5003) - Knowledge graph operations
- **Webhook Server** (Port 5001) - Event-driven processing
- **Model Context Service** (Port 5002) - AI model context management

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Installation

### Detailed Setup

#### 1. Backend Setup

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; print(f'Flask {flask.__version__} installed')"
```

#### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Verify installation
npm list --depth=0
```

#### 3. Database Setup

**Option A: SQLite (Development)**
```bash
# Already configured in .env
# DATABASE_URL=sqlite:///ukg_database.db

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**Option B: PostgreSQL (Production)**
```bash
# Install PostgreSQL 16
# Create database
createdb ukg_database

# Update .env file
DATABASE_URL=postgresql://user:password@localhost:5432/ukg_database

# Initialize database
python init_db.py
```

## Configuration

### Environment Variables

All configuration is in `.env` file. Key settings:

```bash
# Application
FLASK_ENV=development          # development, testing, or production
PORT=5000                      # Backend port

# Database
DATABASE_URL=sqlite:///ukg_database.db  # SQLite for dev

# Security (auto-generated secure keys)
SECRET_KEY=<generated>
JWT_SECRET_KEY=<generated>

# API Keys
OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
ANTHROPIC_API_KEY=your-claude-key
GOOGLE_API_KEY=your-gemini-key
MODEL_PROVIDER=openai  # openai | azure | anthropic | gemini

# Azure AD (Optional)
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id

# UKG System
UKG_MAX_SIMULATION_LAYERS=7
UKG_DEFAULT_CONFIDENCE_THRESHOLD=0.85
UKG_DEFAULT_REFINEMENT_STEPS=12

# Frontend
REACT_APP_API_URL=http://localhost:5000/api
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

See `.env.template` for all available configuration options.

## Running the Application

### Development Mode

**Method 1: Separate Terminals** (Recommended)
```bash
# Terminal 1 - Backend
python main.py
# Backend runs on http://localhost:5000

# Terminal 2 - Frontend
cd frontend && npm start
# Frontend runs on http://localhost:3000
```

**Method 2: Enterprise Mode**
```bash
./start_enterprise.sh
```

**Method 3: UKG Mode**
```bash
./start_ukg.sh
```

### Production Mode

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### Using Replit Workflows

The project includes pre-configured Replit workflows:

- **UKG UI Development** - Recommended for development
- **UKG Production Deployment** - For production builds
- **Initialize Database** - One-time database setup

## Project Structure

```
DataLogicEngine/
├── app.py                      # Flask application entry point
├── main.py                     # Application runner
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── models.py                   # Database models (User, Node, Edge, etc.)
├── routes.py                   # Route definitions
│
├── backend/                    # Backend modules
│   ├── api_gateway/            # API Gateway pattern implementation
│   ├── security/               # Security, compliance, audit logging
│   ├── webhook_server/         # Webhook handling
│   ├── ukg_api.py              # UKG-specific endpoints
│   ├── auth.py                 # Authentication
│   └── [20+ API modules]
│
├── core/                       # Core UKG system
│   ├── simulation/             # 10-layer simulation engines
│   ├── knowledge_algorithm/    # Knowledge algorithm base
│   ├── system/                 # Unified mapping and system management
│   ├── memory/                 # Structured memory management
│   ├── axes/                   # 13-axis framework components
│   ├── persona/                # Expert persona simulation
│   └── self_evolving/          # Self-evolving system components
│
├── knowledge_algorithms/       # 56+ Knowledge Algorithms
│   ├── ka_master_controller.py
│   ├── ka_01_*.py through ka_56_*.py
│   └── [Specialized KA modules]
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/              # 20+ page components
│   │   │   ├── ChatbotPage.js
│   │   │   ├── LoginPage.js
│   │   │   ├── KnowledgeGraphPage.js
│   │   │   └── ...
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React contexts
│   │   ├── utils/              # Utility functions
│   │   └── styles/             # CSS and styling
│   └── package.json
│
├── data/                       # Data files and databases
│   ├── layer1_database.json
│   ├── regulatory_frameworks.yaml
│   └── locations_gazetteer.yaml
│
├── logs/                       # Application logs
│   ├── security/
│   ├── audit/
│   └── compliance/
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── API.md                  # API documentation
│   ├── DEPLOYMENT.md           # Deployment guide
│   ├── style-guide.md          # UI/UX design system
│   └── supporting-documents/   # White papers, technical reports, and reference materials (24 PDFs)
│
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD workflows
│   └── ISSUE_TEMPLATE/         # Issue templates
│
├── templates/                  # Flask templates
├── static/                     # Static assets
└── tests/                      # Test suites

Total: 200+ files, ~4MB of code
```

## API Documentation

### Authentication Endpoints

```
POST   /login                   # User login
POST   /register                # User registration
POST   /logout                  # User logout
GET    /api/user                # Get current user
GET    /api/auth/me             # Get current user details
POST   /api/auth/refresh        # Refresh JWT token
```

### Knowledge Graph Endpoints

```
GET    /api/graph               # Get graph statistics
GET    /api/graph/stats         # Detailed graph statistics
POST   /api/query               # Query the knowledge graph
GET    /api/nodes/:id           # Get specific node
POST   /api/nodes               # Create new node
PUT    /api/nodes/:id           # Update node
DELETE /api/nodes/:id           # Delete node
```

### UKG Endpoints

```
GET    /api/ukg/pillars         # Get all pillar levels
POST   /api/ukg/pillars         # Create pillar level
GET    /api/ukg/sectors         # Get all sectors
POST   /api/ukg/sectors         # Create sector
GET    /api/ukg/domains         # Get all domains
POST   /api/ukg/simulate        # Run simulation
```

### Expert Persona Endpoints

```
POST   /api/persona/query       # Query expert persona
GET    /api/persona/types       # List available personas
```

### Simulation Endpoints

```
GET    /api/simulations         # List user simulations
POST   /api/simulations         # Create simulation
GET    /api/simulations/:id     # Get simulation details
POST   /api/simulation/run      # Run simulation
```

For complete API documentation with examples, see [docs/API.md](docs/API.md)

## Development

### Adding New Features

1. **Backend Endpoint:**
```python
# In backend/api.py or create new module
@api_blueprint.route('/api/new-endpoint', methods=['GET'])
def new_endpoint():
    return jsonify({"message": "Hello from new endpoint"})
```

2. **Frontend Component:**
```jsx
// In frontend/src/pages/NewPage.js
import React from 'react';

export default function NewPage() {
    return <div>New Page Content</div>;
}
```

3. **Database Model:**
```python
# In models.py
class NewModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
```

### Code Style

- **Python:** PEP 8, use `black` for formatting, type hints recommended
- **JavaScript:** ESLint with React configuration, functional components with hooks
- **Commits:** Conventional commits format (feat:, fix:, docs:, etc.)

For detailed contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

## Deployment

### Production Checklist

- [ ] Update `.env` with production values
- [ ] Set `FLASK_ENV=production`
- [ ] Configure PostgreSQL database
- [ ] Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Enable database backups

### Deployment Options

- **GitHub Codespaces:** Launch a full Docker-backed devcontainer with forwarded ports and Compose orchestration
- **Cursor:** Run and ship from the cloud IDE using the included Docker Compose file or static exports
- **Docker:** Docker Compose configuration available for local or remote hosts
- **Kubernetes:** Apply the manifests in `k8s/` (AKS/GKE/EKS compatible) or use Helm overlays
- **Azure DevOps & Visual Studio:** Build CI/CD pipelines to AKS or App Service directly from Visual Studio publish profiles
- **Replit:** Pre-configured for Replit deployment
- **AWS:** Elastic Beanstalk or ECS deployment
- **Azure:** App Service or AKS deployment
- **GCP:** Cloud Run deployment

### Model Provider Options

- **OpenAI GPT:** Use `OPENAI_API_KEY` for direct API access
- **Azure OpenAI:** Configure `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT`
- **Anthropic Claude:** Provide `ANTHROPIC_API_KEY` for enterprise Claude endpoints
- **Google Gemini:** Provide `GOOGLE_API_KEY` for Gemini models

For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Testing

```bash
# Backend tests
pytest tests/ -v

# With coverage
pytest --cov=core --cov=backend tests/

# Frontend tests
cd frontend && npm test

# With coverage
npm test -- --coverage
```

## Troubleshooting

### Common Issues

**Issue: Port already in use**
```bash
# Change PORT in .env file
PORT=5001
```

**Issue: Database connection error**
```bash
# Verify DATABASE_URL in .env
# For SQLite, ensure file path is correct
# For PostgreSQL, check credentials and service status
sudo systemctl status postgresql
```

**Issue: Frontend can't connect to backend**
```bash
# Verify backend is running on port 5000
# Check CORS_ORIGINS in .env includes frontend URL
# Verify proxy setting in frontend/package.json
```

**Issue: Missing dependencies**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

**Issue: Module not found errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
npm install
```

**Issue: Permission denied for startup scripts**
```bash
chmod +x start_enterprise.sh
chmod +x start_ukg.sh
```

For more troubleshooting help, see [OPERATIONAL_RECOMMENDATIONS.md](OPERATIONAL_RECOMMENDATIONS.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following code style guidelines
4. Write or update tests
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Security

- **Authentication**: JWT tokens, Azure AD integration
- **Authorization**: Role-based access control (RBAC)
- **Audit Logging**: Comprehensive security and compliance logs
- **Compliance**: SOC2, GDPR, HIPAA framework support
- **Encryption**: SSL/TLS for data in transit

To report security vulnerabilities, please see [SECURITY.md](SECURITY.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Supporting Documents

Comprehensive technical documentation, white papers, and reference materials are available in the [docs/supporting-documents/](docs/supporting-documents/) directory.

**Quick Links:**
- **[Supporting Documents Index](docs/supporting-documents/README.md)** - Complete catalog of all 24 PDFs organized by category
- **Core Theory**: Universal Knowledge Graph theoretical framework and white papers
- **Technical Specs**: Mathematical formulations and technical specifications
- **Architecture**: 10-layer simulation stack and system architecture
- **Implementation**: MVP plans, development guides, and blueprints
- **Research**: AI optimization and algorithm research papers

These documents provide in-depth coverage of:
- 13-Axis Knowledge Framework
- 10-Layer Simulation Architecture
- 56+ Knowledge Algorithms
- Mathematical foundations
- Enterprise workflows
- Integration patterns

## Support

For issues and questions:

- **Documentation**: See [docs/](docs/) directory
- **Supporting Documents**: See [docs/supporting-documents/](docs/supporting-documents/)
- **Issues**: [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kherrera6219/DataLogicEngine/discussions)
- **Email**: support@datalogicengine.com
- **Operational Guide**: See [OPERATIONAL_RECOMMENDATIONS.md](OPERATIONAL_RECOMMENDATIONS.md)

## Acknowledgments

- Microsoft Fluent UI Design System
- OpenAI API
- Azure Cloud Platform
- Open source community

## Roadmap

### Current Version (v0.1.0)

- ✅ 13-axis knowledge framework
- ✅ 56+ knowledge algorithms
- ✅ Expert persona simulation
- ✅ PostgreSQL integration
- ✅ User authentication

### Phase 2 Completion (December 2025)

**Simulation Engine - 100% Complete:**
- ✅ Layer 4: Reasoning & Logic Engine
- ✅ Layer 5: Memory & Analysis Integration
- ✅ Layer 6: Knowledge Enhancement
- ✅ Layer 7: AGI Simulation Engine (Enhanced)
- ✅ Layer 8: Quantum Simulation
- ✅ Layer 9: Recursive Processing
- ✅ Layer 10: Final Synthesis

**Knowledge Algorithm Integration - 100% Complete:**
- ✅ KA Master Controller with caching, versioning, dependencies
- ✅ 40+ Knowledge Algorithms integrated
- ✅ KA Management API (full REST interface)

**13-Axis Framework - 100% Complete:**
- ✅ Axes 1-7: Knowledge structure (existing)
- ✅ Axis 8: Knowledge Expert Persona
- ✅ Axis 9: Sector Expert Persona
- ✅ Axis 10: Regulatory Expert Persona
- ✅ Axis 11: Compliance Expert Persona
- ✅ Axis 12: Location Context Engine
- ✅ Axis 13: Temporal & Causal Logic

### Upcoming Features (Phase 3+)

- ⏳ Comprehensive testing infrastructure (Phase 3 - 80%+ coverage target)
- ⏳ E2E simulation tests
- ⏳ Performance benchmarking and optimization
- ⏳ Real-time collaborative editing
- ⏳ Mobile application
- ⏳ Enhanced compliance frameworks
- ⏳ GraphQL API support

---

**Status:** ✅ Development Ready | 🟢 Production In Progress (Phase 2: 100% Complete!)

**Built with ❤️ by the DataLogicEngine Team**

Last Updated: December 7, 2025
