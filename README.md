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
- [Support](#support)

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

# 6. Start the backend (Terminal 1)
python main.py

# 7. Start the frontend (Terminal 2)
cd frontend && npm start
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Documentation:** http://localhost:5000/swagger
- **Default Login:** Username: `admin`, Password: `admin123`

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
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

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
│   └── style-guide.md          # UI/UX design system
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

- **Docker:** Docker Compose configuration available
- **Replit:** Pre-configured for Replit deployment
- **AWS:** Elastic Beanstalk or ECS deployment
- **Azure:** App Service or AKS deployment
- **GCP:** Cloud Run deployment

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

## Support

For issues and questions:

- **Documentation**: See [docs/](docs/) directory
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

### Upcoming Features

- 🔄 Enhanced multi-model AI support
- 🔄 Advanced quantum simulation (Layer 8)
- 🔄 Real-time collaborative editing
- 🔄 Mobile application
- 🔄 Enhanced compliance frameworks
- 🔄 GraphQL API support

---

**Status:** ✅ Development Ready | 🟡 Production In Progress

**Built with ❤️ by the DataLogicEngine Team**

Last Updated: November 2025
