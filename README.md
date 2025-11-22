# DataLogicEngine - Universal Knowledge Graph System

A sophisticated AI/ML knowledge management platform featuring a 13-axis knowledge representation system, multi-layer simulation engine, and comprehensive enterprise integrations.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Overview

The **Universal Knowledge Graph (UKG) System** is an enterprise-grade knowledge management platform that combines:

- **13-Axis Knowledge Representation** - Multi-dimensional knowledge organization
- **10-Layer Simulation Engine** - Sophisticated query processing and refinement
- **48 Knowledge Algorithms** - Specialized processing for various knowledge operations
- **Quad Persona System** - Multi-perspective analysis framework
- **Enterprise Integrations** - Azure AD, OpenAI, Microsoft Graph API support

## Features

### Core Capabilities

- ✅ **Knowledge Graph Management** - Create, query, and visualize complex knowledge structures
- ✅ **Multi-Layer Simulation** - Progressive query refinement through 10 specialized layers
- ✅ **User Authentication** - Secure login/logout with session management
- ✅ **Rich UI Components** - 20+ React pages with Chakra UI and D3.js visualizations
- ✅ **RESTful API** - 50+ endpoints for comprehensive system access
- ✅ **Database Support** - PostgreSQL for production, SQLite for development

### 13-Axis System

1. **Axis 1: Pillar Level** - Knowledge hierarchy (PL1-PL100)
2. **Axis 2: Industry Sector** - Domain categorization
3. **Axis 3: Domain Expertise** - Specialized knowledge areas
4. **Axis 4: Methods & Branches** - Methodological frameworks
5. **Axis 5: Honeycomb & Temporal** - Time-based knowledge organization
6. **Axis 6: Regulatory Framework** - Compliance and regulations
7. **Axis 7: Compliance Tracking** - Compliance monitoring (spider-web pattern)
8. **Axis 8-10:** Advanced knowledge dimensions
9. **Axis 11: Contextual** - Context-aware processing
10. **Axis 12: Location** - Geographic knowledge organization
11. **Axis 13: Temporal & Causal** - Time and causality modeling

### Technology Stack

**Backend:**
- Flask 3.1+ (Python web framework)
- SQLAlchemy 2.0+ (ORM)
- PostgreSQL 16 / SQLite (database)
- NetworkX 3.4+ (graph algorithms)
- OpenAI API integration
- Azure enterprise services

**Frontend:**
- React 18.2 (UI framework)
- Chakra UI 2.8 (component library)
- D3.js 7.8 (data visualization)
- React Router 6.14 (navigation)
- Axios (HTTP client)

**DevOps:**
- Gunicorn (WSGI server)
- Flask-Migrate (database migrations)
- Python-dotenv (environment configuration)

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
- **Default Login:** Username: `admin`, Password: `admin123`

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
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
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

# UKG System
UKG_MAX_SIMULATION_LAYERS=7
UKG_DEFAULT_CONFIDENCE_THRESHOLD=0.85
UKG_DEFAULT_REFINEMENT_STEPS=12

# Frontend
REACT_APP_API_URL=http://localhost:5000/api
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### Azure Integration (Enterprise)

For Azure AD, OpenAI, and Graph API integration, update `.env`:

```bash
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret

AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## Running the Application

### Development Mode

**Method 1: Separate Terminals**
```bash
# Terminal 1 - Backend
python main.py
# Backend runs on http://localhost:5000

# Terminal 2 - Frontend
cd frontend && npm start
# Frontend runs on http://localhost:3000
```

**Method 2: Production Mode**
```bash
# Build frontend
cd frontend && npm run build && cd ..

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
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
├── models.py                   # Database models
├── routes.py                   # Route definitions
│
├── backend/                    # Backend modules
│   ├── api.py                  # Main API blueprint
│   ├── ukg_api.py              # UKG-specific endpoints
│   ├── ukg_db.py               # Database operations
│   ├── auth.py                 # Authentication
│   ├── chat_api.py             # Chat endpoints
│   ├── compliance_api.py       # Compliance endpoints
│   └── [20+ API modules]
│
├── core/                       # Core UKG system
│   ├── simulation_engine.py   # Multi-layer simulation
│   ├── app_orchestrator.py    # Component coordination
│   ├── graph_manager.py       # Graph operations
│   ├── axes/                  # 13-axis implementations
│   ├── simulation/            # Layer implementations
│   ├── memory/                # Memory management
│   └── persona/               # Quad persona engine
│
├── knowledge_algorithms/       # 48 Knowledge Algorithms
│   ├── ka_master_controller.py
│   ├── ka_01_*.py through ka_57_*.py
│   └── [Specialized KA modules]
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/             # 20+ page components
│   │   ├── components/        # Reusable components
│   │   ├── contexts/          # React contexts
│   │   └── styles/            # CSS and styling
│   └── package.json
│
├── templates/                  # Flask templates
├── static/                     # Static assets
└── docs/                       # Documentation

Total: 200+ files, ~4MB of code
```

## API Documentation

### Authentication Endpoints

```
POST   /login                   # User login
POST   /register                # User registration
POST   /logout                  # User logout
GET    /api/user                # Get current user
```

### UKG Endpoints

```
GET    /api/ukg/pillars         # Get all pillar levels
POST   /api/ukg/pillars         # Create pillar level
GET    /api/ukg/sectors         # Get all sectors
POST   /api/ukg/sectors         # Create sector
GET    /api/ukg/domains         # Get all domains
POST   /api/ukg/domains         # Create domain
POST   /api/ukg/simulate        # Run simulation
GET    /api/ukg/graph           # Get knowledge graph
```

### Simulation Endpoints

```
GET    /api/simulations         # List user simulations
POST   /api/simulations         # Create simulation
GET    /api/simulations/:id     # Get simulation details
POST   /api/simulations/:id/start  # Start simulation
POST   /api/simulations/:id/pause  # Pause simulation
DELETE /api/simulations/:id     # Delete simulation
```

Full API documentation available at `/docs/api.md` (coming soon)

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

### Running Tests

```bash
# Backend tests (when implemented)
pytest

# Frontend tests
cd frontend && npm test
```

### Code Style

- **Python:** PEP 8, use `black` for formatting
- **JavaScript:** ESLint with React configuration
- **Commits:** Conventional commits format

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

### Docker Deployment (Future)

```bash
# Coming soon
docker-compose up -d
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

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions:
- GitHub Issues: https://github.com/kherrera6219/DataLogicEngine/issues
- Documentation: See `OPERATIONAL_RECOMMENDATIONS.md` for detailed analysis

## Acknowledgments

Built with modern web technologies and best practices for enterprise knowledge management.

---

**Status:** ✅ Development Ready | 🟡 Production In Progress

Last Updated: November 2025
