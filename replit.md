# Universal Knowledge Graph (UKG) System

## Overview
A comprehensive Universal Knowledge Graph and Universal Simulated Knowledge Database (USKD) system that provides multi-perspective knowledge synthesis, expert simulation, and AI-powered analysis.

## Architecture

### Technology Stack
- **Backend**: Flask (Python 3.11) with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **Database**: PostgreSQL (Neon-backed via Replit)
- **AI**: OpenAI via Replit AI Integrations
- **Visualization**: D3.js for knowledge graphs

### Key Components

#### 13-Axis Knowledge Framework
1. Identity Axis - User and entity identification
2. Sector Axis - Industry and sector classification
3. Domain Axis - Knowledge domain categorization
4. Knowledge Axis - Core knowledge areas
5. Methods Axis - Methodologies and approaches
6. Honeycomb Axis - Interconnected knowledge cells
7. Regulatory Axis - Legal and regulatory frameworks
8. Compliance Axis - Standards and compliance requirements
9. Knowledge Expert Axis - Subject matter expertise
10. Sector Expert Axis - Industry expertise
11. Contextual Expert Axis - Context-aware expertise
12. Location Axis - Geographic and spatial context
13. Time Axis - Temporal context and evolution

#### 10-Layer Simulation Stack
1. Knowledge Base
2. Quad Persona Engine
3. Simulation Memory
4. Reasoning Layer
5. Integration Layer
6. Enhancement Layer
7. AGI System
8. Quantum Computing Layer
9. Recursive Core
10. Self-Awareness Engine

## Project Structure

```
/
├── main.py                 # Application entry point
├── app.py                  # Flask app configuration and routes
├── models.py               # SQLAlchemy database models
├── backend/
│   ├── ai_chat.py          # AI chat API endpoints
│   ├── ka_api.py           # Knowledge Algorithm API (KA-01 to KA-50)
│   ├── mcp_api.py          # MCP (Model Context Protocol) API
│   └── security/           # Security middleware
├── core/
│   ├── knowledge_graph.py  # Knowledge graph operations
│   └── simulation_engine.py # Simulation engine
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
- `GET /api/ka/algorithms` - List all 50 knowledge algorithms
- `GET /api/ka/algorithms/<id>` - Get algorithm details
- `GET /api/ka/categories` - List algorithm categories
- `POST /api/ka/execute/<id>` - Execute an algorithm
- `POST /api/ka/batch` - Execute multiple algorithms

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
- Added Knowledge Algorithm API with 50 algorithms across 14 categories
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
