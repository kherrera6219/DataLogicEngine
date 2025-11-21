# DataLogicEngine Architecture

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [13-Axis Knowledge Framework](#13-axis-knowledge-framework)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Architecture](#api-architecture)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)

## Overview

DataLogicEngine is a sophisticated enterprise knowledge graph system built on a microservices architecture. It combines a Next.js frontend with a Flask backend, implementing a unique 13-axis knowledge framework for multi-dimensional knowledge organization and retrieval.

### Architectural Goals

1. **Scalability**: Support growing knowledge graphs and increasing user loads
2. **Modularity**: Independent services that can be deployed and scaled separately
3. **Security**: Enterprise-grade authentication, authorization, and audit logging
4. **Performance**: Fast query response times through optimized graph algorithms
5. **Extensibility**: Easy addition of new knowledge algorithms and axes

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Browser  │  │  Mobile  │  │ Desktop  │  │   API    │   │
│  │   App    │  │   App    │  │   App    │  │ Clients  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                    Next.js (Port 3000)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pages  │  Components  │  Hooks  │  Context  │ Utils │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                        │
│                  Flask API Gateway (Port 5000)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication  │  Routing  │  Rate Limiting  │ CORS │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Core UKG        │ │  Webhook     │ │  Model Context   │
│  Service         │ │  Server      │ │  Service         │
│  (Port 5003)     │ │  (Port 5001) │ │  (Port 5002)     │
└──────────────────┘ └──────────────┘ └──────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Knowledge Graph  │  Simulation  │  Expert Personas  │  │
│  │  56+ Algorithms   │  Engines     │  13-Axis System   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Access Layer                      │
│              SQLAlchemy ORM + Repository Pattern             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ PostgreSQL   │  │ JSON Files   │  │  YAML Configs    │ │
│  │ (Primary DB) │  │  (Fallback)  │  │  (Reference)     │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Microservices Architecture

#### 1. API Gateway (Port 5000)
- **Purpose**: Single entry point for all API requests
- **Responsibilities**:
  - Request routing
  - Authentication/Authorization
  - Rate limiting
  - CORS handling
  - Request/response logging

#### 2. Core UKG Service (Port 5003)
- **Purpose**: Core knowledge graph operations
- **Responsibilities**:
  - Graph CRUD operations
  - Knowledge algorithm execution
  - 13-axis framework management
  - Query processing

#### 3. Webhook Server (Port 5001)
- **Purpose**: Event-driven processing
- **Responsibilities**:
  - External event handling
  - Asynchronous processing
  - Integration with external systems

#### 4. Model Context Service (Port 5002)
- **Purpose**: AI model context management
- **Responsibilities**:
  - Context preparation for AI models
  - Prompt engineering
  - Response processing

## Technology Stack

### Frontend Stack

```yaml
Framework: Next.js 14.0.4
  - React: 18.2.0
  - TypeScript: Optional
  - CSS Modules: Built-in

UI Libraries:
  - Chakra UI: 2.10.8 (Component library)
  - Microsoft Fluent UI: 9.64.0 (Design system)
  - React Bootstrap: 2.9.1
  - Bootstrap Icons: 1.11.3

Visualization:
  - D3.js: 7.9.0 (Data visualization)
  - React Force Graph 2D: 1.27.1 (Network graphs)
  - Framer Motion: Animation library

Utilities:
  - Marked: Markdown parsing
  - dotenv: Environment management
```

### Backend Stack

```yaml
Framework: Flask 3.1.1
  - Python: 3.11+
  - Gunicorn: 23.0.0 (WSGI server)

Database:
  - PostgreSQL: 16
  - SQLAlchemy: 2.0.41 (ORM)
  - psycopg2: PostgreSQL driver

Authentication:
  - Flask-Login: 0.6.3
  - PyJWT: 2.10.1 (JWT tokens)
  - Flask-Dance: 7.1.0 (OAuth)

APIs:
  - Flask-CORS: Cross-origin support
  - Flask-Swagger-UI: API documentation
  - Marshmallow: Serialization/validation

AI Integration:
  - OpenAI: 1.79.0
  - Azure OpenAI: Azure SDK

Data Processing:
  - NetworkX: 3.4.2 (Graph algorithms)
  - NumPy: 2.2.6
  - Pandas: Data manipulation
```

## 13-Axis Knowledge Framework

The core innovation of DataLogicEngine is its 13-dimensional knowledge organization system.

### Axis 1: Pillar Levels
**Purpose**: Foundational knowledge organization

- 48 knowledge pillars representing core domains
- Hierarchical structure from abstract to concrete
- Each pillar has subtopics and related concepts

**Implementation**: `core/axes/axis01_pillar.py`

### Axis 2: Industry Sectors
**Purpose**: Domain-specific knowledge

- Industry classification (Technology, Healthcare, Finance, etc.)
- Sector-specific terminology and concepts
- Cross-sector relationships

**Implementation**: `core/axes/axis02_sector.py`

### Axis 3: Honeycomb System
**Purpose**: Knowledge expansion and exploration

- Hexagonal knowledge cells
- 6-way connectivity for related concepts
- Expansion algorithm (KA-04)
- Visual representation in 3D

**Implementation**: `core/axes/axis03_honeycomb.py`

### Axis 4: Branch System
**Purpose**: Hierarchical knowledge trees

- Parent-child relationships
- Multiple inheritance support
- Branch traversal algorithms

**Implementation**: `core/axes/axis04_branch.py`

### Axis 5: Node System
**Purpose**: Atomic knowledge units

- Individual knowledge nodes
- Node types and properties
- Inter-node relationships

**Implementation**: `core/axes/axis05_node.py`

### Axis 6: Octopus Node (Regulatory)
**Purpose**: Regulatory framework mapping

- Central regulatory concept with multiple tentacles
- Each tentacle represents a regulatory domain
- Compliance requirement tracking

**Implementation**: `core/axes/axis06_octopus.py`

### Axis 7: Spiderweb Node (Compliance)
**Purpose**: Compliance network

- Web-like compliance relationships
- Impact analysis
- Compliance dependencies

**Implementation**: `core/axes/axis07_spiderweb.py`

### Axis 8: Knowledge Expert Persona
**Purpose**: Expert simulation for knowledge domain

- AI-powered expert persona
- Knowledge domain expertise
- Query answering capability

**Implementation**: `core/persona/knowledge_expert.py`

### Axis 9: Sector Expert Persona
**Purpose**: Industry sector expertise

- Sector-specific expert simulation
- Industry best practices
- Trend analysis

**Implementation**: `core/persona/sector_expert.py`

### Axis 10: Regulatory Expert Persona
**Purpose**: Regulatory compliance expertise

- Regulatory framework knowledge
- Compliance guidance
- Risk assessment

**Implementation**: `core/persona/regulatory_expert.py`

### Axis 11: Compliance Expert Persona
**Purpose**: Compliance implementation expertise

- Implementation guidance
- Audit preparation
- Documentation support

**Implementation**: `core/persona/compliance_expert.py`

### Axis 12: Location Context
**Purpose**: Geospatial knowledge context

- Geographic location data
- Location-specific regulations
- Regional variations

**Implementation**: `core/axes/axis12_location.py`

### Axis 13: Temporal/Causal Logic
**Purpose**: Time-based and causal relationships

- Temporal ordering
- Cause-effect relationships
- Historical evolution

**Implementation**: `core/axes/axis13_temporal.py`

## Core Components

### 1. Knowledge Graph Engine

```python
# core/knowledge_graph.py
class KnowledgeGraph:
    """
    Main knowledge graph implementation using NetworkX
    """
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.united_system = UnitedSystemManager()

    def add_node(self, node_type, data):
        """Add a node to the graph"""

    def add_edge(self, source, target, relationship):
        """Add an edge between nodes"""

    def query(self, query_params):
        """Query the knowledge graph"""
```

### 2. Knowledge Algorithms (56+)

Located in `knowledge_algorithms/`, these algorithms power various graph operations:

- **KA-01**: Semantic Mapping - Maps concepts to semantic space
- **KA-04**: Honeycomb Expansion - Expands knowledge in hexagonal patterns
- **KA-06**: Coordinate Projection - Maps multi-dimensional knowledge to coordinates
- **KA-07/08**: Expert Simulation - Simulates regulatory and compliance experts
- **KA-10-56**: Advanced algorithms for validation, tree-of-thought, neural reconstruction

### 3. Simulation Engines

Multi-layer simulation system located in `core/simulation/`:

```
Layer 1-3: Memory Simulation
  └─ Propagates knowledge through memory structures

Layer 5: Integration Engine
  └─ Integrates multiple knowledge sources

Layer 7: AGI Simulation
  └─ Advanced general intelligence simulation

Layer 8: Quantum Simulation
  └─ Quantum-inspired knowledge processing

Layer 9-10: Recursive Processing
  └─ Deep recursive knowledge analysis
```

### 4. United System Manager

```python
# core/system/united_system_manager.py
class UnitedSystemManager:
    """
    Manages unique IDs across all 13 axes
    """
    def generate_id(self, axis, node_type):
        """Generate unique identifier"""

    def validate_id(self, node_id):
        """Validate identifier format"""

    def get_axis_from_id(self, node_id):
        """Extract axis from identifier"""
```

## Data Flow

### Query Processing Flow

```
1. User Request
   └─> Next.js Frontend (pages/api/query.js)
       └─> API Gateway (backend/api_gateway/routes.py)
           └─> Core UKG Service (backend/ukg_api.py)
               ├─> Knowledge Graph Engine
               │   ├─> Algorithm Selection
               │   ├─> Query Execution
               │   └─> Result Processing
               └─> Database Query (SQLAlchemy)
                   └─> PostgreSQL
       <─ Response with Results
   <─ JSON Response to Frontend
```

### Knowledge Addition Flow

```
1. Add Knowledge Request
   └─> Frontend Form Submission
       └─> API Gateway
           └─> Core UKG Service
               ├─> Validate Data (Marshmallow)
               ├─> Generate ID (United System)
               ├─> Add to Graph (Knowledge Graph Engine)
               ├─> Execute Algorithms (e.g., Honeycomb Expansion)
               └─> Persist to Database
       <─ Success Response
```

### Expert Persona Query Flow

```
1. Persona Query Request
   └─> Frontend Chat Interface
       └─> API Gateway
           └─> Core UKG Service
               ├─> Select Persona (Knowledge/Sector/Regulatory/Compliance)
               ├─> Context Preparation (Model Context Service)
               ├─> AI API Call (OpenAI/Azure)
               ├─> Response Processing
               └─> Knowledge Graph Update
       <─ Expert Response
```

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    role VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nodes table
CREATE TABLE nodes (
    id VARCHAR(100) PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    axis INTEGER NOT NULL,
    label VARCHAR(200),
    data JSONB,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Edges table
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) REFERENCES nodes(id),
    target_id VARCHAR(100) REFERENCES nodes(id),
    relationship_type VARCHAR(100),
    weight FLOAT DEFAULT 1.0,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Graphs table
CREATE TABLE knowledge_graphs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulation Sessions table
CREATE TABLE simulation_sessions (
    id SERIAL PRIMARY KEY,
    session_type VARCHAR(50),
    layer INTEGER,
    parameters JSONB,
    results JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(256) UNIQUE NOT NULL,
    name VARCHAR(100),
    permissions JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_axis ON nodes(axis);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

## API Architecture

### RESTful API Design

All APIs follow REST principles with consistent response formats:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-11-21T00:00:00Z"
}
```

### Error Responses

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2025-11-21T00:00:00Z"
}
```

### Authentication

```
Authorization: Bearer <JWT_TOKEN>
X-API-Key: <API_KEY>
```

## Security Architecture

### Authentication Flow

```
1. User Login
   ├─> Username/Password OR
   └─> Azure AD OAuth
       └─> Validate Credentials
           ├─> Generate JWT Token
           │   └─> Expiration: 1 hour
           └─> Create Session
               └─> Return Token
```

### Authorization Layers

1. **Route-level**: `@login_required` decorator
2. **Resource-level**: RBAC checks
3. **Data-level**: Row-level security

### Security Features

- **JWT Tokens**: Short-lived access tokens
- **Password Hashing**: Industry-standard bcrypt
- **HTTPS**: Enforced in production
- **CORS**: Restricted origins
- **Rate Limiting**: Per-user and per-IP
- **Audit Logging**: All security events logged
- **Input Validation**: Marshmallow schemas

## Deployment Architecture

### Development Environment

```yaml
Frontend:
  - npm run dev (Port 3000)
  - Hot reload enabled

Backend:
  - Flask development server
  - Debug mode enabled
  - SQLite database (optional)
```

### Production Environment

```yaml
Frontend:
  - Next.js build (npm run build)
  - Served by Next.js server or CDN

Backend:
  - Gunicorn WSGI server
  - Multiple worker processes
  - PostgreSQL database
  - Reverse proxy (Nginx)

Infrastructure:
  - Load balancer
  - Auto-scaling groups
  - Database replication
  - Redis cache (optional)
```

### Container Architecture (Docker)

```yaml
services:
  frontend:
    image: datalogicengine-frontend
    ports: ["3000:3000"]

  api-gateway:
    image: datalogicengine-backend
    ports: ["5000:5000"]
    depends_on: [postgres]

  ukg-service:
    image: datalogicengine-ukg
    ports: ["5003:5003"]

  postgres:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
```

## Design Patterns

### Backend Patterns

1. **Microservices**: Independent, scalable services
2. **API Gateway**: Single entry point pattern
3. **Repository**: Data access abstraction
4. **Factory**: Dynamic object creation (United System)
5. **Strategy**: Algorithm selection (Knowledge Algorithms)
6. **Observer**: Event-driven webhooks

### Frontend Patterns

1. **Component Composition**: Reusable UI components
2. **Container/Presenter**: Separation of concerns
3. **Custom Hooks**: Shared logic extraction
4. **Context API**: Global state management

## Performance Considerations

### Optimization Strategies

1. **Database**: Indexed queries, connection pooling
2. **Caching**: Redis for frequent queries
3. **Lazy Loading**: On-demand component loading
4. **Graph Algorithms**: Optimized NetworkX operations
5. **Async Processing**: Background jobs for heavy operations

### Scalability

- **Horizontal Scaling**: Add more service instances
- **Database Sharding**: Partition by knowledge domain
- **CDN**: Static asset distribution
- **Microservices**: Independent scaling per service

## Future Architecture Enhancements

1. **GraphQL API**: Alternative to REST
2. **Event Sourcing**: Complete audit trail
3. **CQRS**: Separate read/write models
4. **Service Mesh**: Advanced microservice communication
5. **Kubernetes**: Container orchestration
6. **Real-time**: WebSocket support for live updates

---

For more details, see:
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Database Schema](DATABASE.md)
