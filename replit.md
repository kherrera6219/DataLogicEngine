# Universal Knowledge Graph (UKG) System

## Overview
A comprehensive Universal Knowledge Graph and Universal Simulated Knowledge Database (USKD) system that provides multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis using a 17-Axis framework.

## Architecture

### Technology Stack
- **Backend**: Flask (Python 3.11) with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **Database**: PostgreSQL (Neon-backed via Replit)
- **AI**: OpenAI via Replit AI Integrations
- **Visualization**: D3.js for knowledge graphs

### Key Components

#### 17-Axis Knowledge Framework

**Core Knowledge Dimensions (Axes 1-13):**
1. Pillar Levels Axis - Hierarchical knowledge organization (PL01-PL87)
2. Sectors Axis - Industry and sector classification
3. Topics/Branches Axis - Subject matters and specializations
4. Methods Axis - Methodologies and approaches
5. Tools Axis - Software, hardware, and instruments
6. Regulatory Frameworks Axis - Laws and regulations (Octopus Node)
7. Compliance Standards Axis - Standards and best practices (Spiderweb Node)
8. Knowledge Experts Axis - Domain expertise
9. Skill Experts Axis - Skill-based expertise
10. Role Experts Axis - Professional role expertise
11. Context Experts Axis - Situational expertise
12. Locations Axis - Geographic and spatial context
13. Time Axis - Temporal context and evolution

**Extended Enterprise Dimensions (Axes 14-17):**
14. Risk & Confidence Axis - Risk classification (Low/Medium/High/Critical), confidence scoring, validation metrics, entropy analysis
15. Federated Intelligence Axis - Cross-system synchronization, distributed knowledge stores, privacy-preserving federation, data sovereignty
16. Arrows of Time Axis - Advanced causality chains, temporal consistency checks, predictive modeling, event sequencing
17. Observability & Analytics Axis - Metrics collection, audit trails, performance monitoring, SLA management, distributed tracing

#### 10-Layer Simulation Stack
1. Knowledge Base - Initial data retrieval and preprocessing
2. Quad Persona Engine - Expert role simulation (Analyst, Expert, Critic, Synthesizer)
3. Simulation Memory - Persistent state and context management
4. Reasoning Layer - Logical inference and deduction
5. Integration Layer - Multi-source knowledge synthesis
6. Enhancement Layer - Pattern recognition and neural reflection
7. AGI System - Strategic planning and complex problem solving
8. Quantum Computing Layer - Uncertainty and entanglement simulation
9. Recursive Core - Deep recursive reasoning and emergence detection
10. Self-Awareness Engine - System coherence and containment protocols

## Project Structure

```
/
├── main.py                 # Application entry point
├── app.py                  # Flask app configuration and routes
├── models.py               # SQLAlchemy database models
├── backend/
│   ├── ai_chat.py          # AI chat API endpoints
│   ├── ka_api.py           # Knowledge Algorithm API (KA-001 to KA-114)
│   ├── ka_registry.json    # 114 algorithm definitions from Excel registry
│   ├── mcp_api.py          # MCP (Model Context Protocol) API
│   └── security/           # Security middleware
├── core/
│   ├── knowledge_graph.py  # Knowledge graph operations
│   ├── simulation_engine.py # Simulation engine
│   └── axes/               # 17-Axis System modules
│       ├── axis_system.py      # Central coordinator for 17 axes
│       ├── axis1_identity.py   # Axis 1: Pillar Levels
│       ├── axis2_sectors.py    # Axis 2: Sectors
│       ├── axis4_methods.py    # Axis 4: Methods
│       ├── axis5_honeycomb.py  # Axis 5: Tools/Honeycomb
│       ├── axis6_regulatory.py # Axis 6: Regulatory Frameworks
│       ├── axis7_compliance.py # Axis 7: Compliance Standards
│       ├── axis11_contextual.py # Axis 11: Context Experts
│       ├── axis12_location.py  # Axis 12: Locations
│       ├── axis13_time.py      # Axis 13: Time
│       ├── axis14_risk.py      # Axis 14: Risk & Confidence
│       ├── axis15_federated.py # Axis 15: Federated Intelligence
│       ├── axis16_arrows_of_time.py # Axis 16: Arrows of Time
│       └── axis17_observability.py  # Axis 17: Observability & Analytics
├── data/
│   └── ukg/
│       └── axis_definitions.yaml # 17-Axis definitions
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base template
│   ├── dashboard.html      # User dashboard
│   ├── simulations.html    # Simulations list with pagination
│   ├── chat.html           # AI chat interface
│   ├── knowledge_graph.html # Knowledge graph visualization
│   └── api_docs.html       # Swagger API documentation
└── static/
    ├── css/                # Custom styles
    ├── js/                 # JavaScript files
    └── swagger/            # OpenAPI specification
```

## API Endpoints

### AI Chat API (`/api/ai/`)
- `POST /api/ai/chat` - Send chat message to AI assistant
- `POST /api/ai/chat/stream` - Streaming chat response
- `POST /api/ai/analyze` - Analyze knowledge context
- `GET /api/ai/health` - Health check

### Knowledge Algorithm API (`/api/ka/`)
- `GET /api/ka/algorithms` - List all 114 knowledge algorithms (with pagination and filters)
- `GET /api/ka/algorithms/<id>` - Get algorithm details
- `GET /api/ka/categories` - List algorithm categories with their algorithms
- `GET /api/ka/layers` - List simulation layers and associated algorithms
- `GET /api/ka/search?q=<query>` - Search algorithms by name, purpose, or notes
- `GET /api/ka/dependencies/<id>` - Get algorithm dependency graph
- `GET /api/ka/stats` - Get KA system statistics
- `POST /api/ka/algorithms/<id>/execute` - Execute an algorithm
- `POST /api/ka/batch` - Execute multiple algorithms (max 20)

### MCP API (`/api/mcp/`)
- `GET /api/mcp/context` - Get current context
- `POST /api/mcp/context` - Update context
- Various simulation and analysis endpoints

## Features

### Simulations
- Create and manage simulation sessions
- Support for multiple simulation types
- Pagination (configurable items per page)
- Export to JSON/CSV formats
- Progress tracking

### AI Chat
- Context-aware conversations
- Conversation history tracking
- Multi-perspective analysis using quad persona approach
- Real-time streaming responses

### Knowledge Graph Visualization
- Interactive D3.js-based visualization
- Zoom, pan, and drag interactions
- Node filtering and search
- Real-time updates

### API Documentation
- Swagger/OpenAPI specification at `/api-docs`
- Interactive API explorer
- Complete endpoint documentation

## Security Features
- Session-based authentication with Flask-Login
- CSRF protection
- Security headers middleware
- Rate limiting
- Request size limits
- Input validation

## Recent Changes

### December 2024
- **Migrated from 13-Axis to 17-Axis System**
  - Added Axis 14: Risk & Confidence - Risk classification, confidence scoring, validation metrics
  - Added Axis 15: Federated Intelligence - Cross-system sync, distributed knowledge, data sovereignty
  - Added Axis 16: Arrows of Time - Causality chains, temporal consistency, predictive modeling
  - Added Axis 17: Observability & Analytics - Metrics, audit trails, performance monitoring
- Created new axis modules: axis14_risk.py, axis15_federated.py, axis16_arrows_of_time.py, axis17_observability.py
- Updated axis_system.py central coordinator for 17-axis support
- Updated axis_definitions.yaml with full 17-axis definitions
- Enhanced AI chat system prompt with 17-axis knowledge framework
- Expanded Knowledge Algorithm API to 114 algorithms from enterprise Excel registry
- Added new KA endpoints: layers, search, dependencies, stats
- Implemented AI chat with OpenAI integration via Replit AI Integrations
- Created interactive knowledge graph visualization page
- Added Swagger/OpenAPI documentation
- Enhanced simulations with pagination and export functionality
- Fixed pagination edge cases (empty results handling)
- Added rate limiting to export endpoints
- Improved null handling in simulation exports

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Flask session secret key
- `AI_INTEGRATIONS_OPENAI_API_KEY` - OpenAI API key (via Replit)
- `AI_INTEGRATIONS_OPENAI_BASE_URL` - OpenAI API base URL (via Replit)

## Running the Application
The application runs via gunicorn on port 5000:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## User Preferences
- Clean, production-ready design
- Bootstrap-based UI with dark theme option
- Material icons for visual elements
- Comprehensive error handling
