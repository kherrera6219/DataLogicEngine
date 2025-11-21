# API Documentation

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Knowledge Graph](#knowledge-graph-endpoints)
  - [Nodes](#node-endpoints)
  - [Edges](#edge-endpoints)
  - [Personas](#persona-endpoints)
  - [Simulation](#simulation-endpoints)
  - [Compliance](#compliance-endpoints)
  - [Search](#search-endpoints)
- [WebSocket API](#websocket-api)
- [Examples](#examples)

## Overview

DataLogicEngine provides a comprehensive RESTful API for interacting with the Universal Knowledge Graph system. The API supports operations across all 13 axes, knowledge algorithms, expert personas, and simulation engines.

### API Version

Current Version: `v1`

All API endpoints are versioned and follow semantic versioning principles.

## Authentication

### Authentication Methods

The API supports multiple authentication methods:

1. **JWT Bearer Tokens** (Recommended)
2. **API Keys**
3. **Azure AD OAuth 2.0**

### JWT Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "user@example.com",
      "role": "user"
    }
  }
}
```

**Using the Token:**
```http
GET /api/graph
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication

```http
GET /api/graph
X-API-Key: your_api_key_here
```

### Azure AD OAuth

```http
GET /api/auth/azure/login
```

Redirects to Azure AD login page. After successful authentication, redirects back with token.

## Base URLs

### Development
```
Frontend: http://localhost:3000
API Gateway: http://localhost:5000
```

### Production
```
Frontend: https://app.datalogicengine.com
API: https://api.datalogicengine.com
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2025-11-21T12:00:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context
    }
  },
  "timestamp": "2025-11-21T12:00:00Z"
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Codes

```
AUTH_001: Invalid credentials
AUTH_002: Token expired
AUTH_003: Insufficient permissions

GRAPH_001: Invalid node ID
GRAPH_002: Node not found
GRAPH_003: Circular dependency detected

VALIDATION_001: Missing required field
VALIDATION_002: Invalid data type
VALIDATION_003: Value out of range

SYSTEM_001: Database connection error
SYSTEM_002: External service unavailable
```

## Rate Limiting

Rate limits are applied per user or per API key:

- **Authenticated Users**: 1000 requests/hour
- **API Keys**: 5000 requests/hour
- **Unauthenticated**: 100 requests/hour

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1700000000
```

## Endpoints

### Authentication Endpoints

#### POST /api/auth/login
Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600
  }
}
```

#### POST /api/auth/refresh
Refresh an expired JWT token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

#### POST /api/auth/logout
Invalidate current session.

#### GET /api/auth/me
Get current user information.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

---

### Knowledge Graph Endpoints

#### GET /api/graph
Get graph statistics and overview.

**Response:**
```json
{
  "success": true,
  "data": {
    "node_count": 1524,
    "edge_count": 3847,
    "axes": {
      "axis_1": 48,
      "axis_2": 15,
      "axis_3": 256
    },
    "last_updated": "2025-11-21T12:00:00Z"
  }
}
```

#### GET /api/graph/stats
Get detailed graph statistics.

**Query Parameters:**
- `axis` (optional): Filter by specific axis (1-13)
- `node_type` (optional): Filter by node type

**Response:**
```json
{
  "success": true,
  "data": {
    "total_nodes": 1524,
    "total_edges": 3847,
    "average_degree": 2.52,
    "density": 0.0034,
    "connected_components": 5,
    "diameter": 12,
    "clustering_coefficient": 0.234
  }
}
```

#### POST /api/query
Query the knowledge graph.

**Request:**
```json
{
  "query": "Find all regulatory nodes related to healthcare",
  "filters": {
    "axis": 6,
    "sector": "healthcare"
  },
  "limit": 50,
  "include_edges": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "AX06-REG-001",
        "type": "regulatory",
        "label": "HIPAA Compliance",
        "axis": 6,
        "data": { ... }
      }
    ],
    "edges": [ ... ],
    "total": 42
  }
}
```

---

### Node Endpoints

#### POST /api/nodes
Create a new node.

**Request:**
```json
{
  "node_type": "knowledge",
  "axis": 1,
  "label": "Machine Learning",
  "data": {
    "description": "Branch of AI",
    "pillar": "Technology",
    "tags": ["AI", "ML", "Data Science"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "AX01-KNW-1234",
    "node_type": "knowledge",
    "axis": 1,
    "label": "Machine Learning",
    "created_at": "2025-11-21T12:00:00Z"
  }
}
```

#### GET /api/nodes/:id
Get a specific node by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "AX01-KNW-1234",
    "node_type": "knowledge",
    "axis": 1,
    "label": "Machine Learning",
    "data": { ... },
    "edges": {
      "incoming": 5,
      "outgoing": 12
    },
    "created_at": "2025-11-21T12:00:00Z"
  }
}
```

#### PUT /api/nodes/:id
Update a node.

**Request:**
```json
{
  "label": "Deep Learning",
  "data": {
    "description": "Subset of Machine Learning"
  }
}
```

#### DELETE /api/nodes/:id
Delete a node.

**Query Parameters:**
- `cascade` (boolean): Delete connected edges (default: false)

#### GET /api/nodes/:id/neighbors
Get neighboring nodes.

**Query Parameters:**
- `direction`: "incoming", "outgoing", or "both" (default: "both")
- `depth`: Traversal depth (default: 1, max: 5)
- `limit`: Maximum results (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "neighbors": [
      {
        "id": "AX01-KNW-1235",
        "label": "Neural Networks",
        "distance": 1,
        "relationship": "related_to"
      }
    ],
    "total": 12
  }
}
```

#### GET /api/nodes/:id/path/:target_id
Find shortest path between two nodes.

**Response:**
```json
{
  "success": true,
  "data": {
    "path": [
      "AX01-KNW-1234",
      "AX01-KNW-1235",
      "AX01-KNW-1236"
    ],
    "length": 2,
    "relationships": [
      "related_to",
      "depends_on"
    ]
  }
}
```

---

### Edge Endpoints

#### POST /api/edges
Create a new edge.

**Request:**
```json
{
  "source_id": "AX01-KNW-1234",
  "target_id": "AX01-KNW-1235",
  "relationship_type": "related_to",
  "weight": 0.85,
  "data": {
    "confidence": "high",
    "created_by": "user"
  }
}
```

#### GET /api/edges/:id
Get edge details.

#### PUT /api/edges/:id
Update edge properties.

#### DELETE /api/edges/:id
Delete an edge.

---

### Persona Endpoints

#### POST /api/persona/query
Query an expert persona.

**Request:**
```json
{
  "persona_type": "knowledge_expert",
  "query": "What are the latest trends in AI?",
  "context": {
    "sector": "technology",
    "axis": 1
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "Based on current knowledge...",
    "persona": "knowledge_expert",
    "confidence": 0.92,
    "sources": [
      "AX01-KNW-1234",
      "AX01-KNW-1235"
    ],
    "timestamp": "2025-11-21T12:00:00Z"
  }
}
```

#### GET /api/persona/types
List available persona types.

**Response:**
```json
{
  "success": true,
  "data": {
    "personas": [
      {
        "type": "knowledge_expert",
        "axis": 8,
        "description": "Expert in knowledge domains"
      },
      {
        "type": "sector_expert",
        "axis": 9,
        "description": "Industry sector specialist"
      },
      {
        "type": "regulatory_expert",
        "axis": 10,
        "description": "Regulatory compliance expert"
      },
      {
        "type": "compliance_expert",
        "axis": 11,
        "description": "Compliance implementation expert"
      }
    ]
  }
}
```

---

### Simulation Endpoints

#### POST /api/simulation/run
Run a simulation.

**Request:**
```json
{
  "simulation_type": "layer7_agi",
  "parameters": {
    "iterations": 100,
    "learning_rate": 0.01,
    "nodes": ["AX01-KNW-1234"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "SIM-20251121-001",
    "status": "running",
    "estimated_completion": "2025-11-21T12:05:00Z"
  }
}
```

#### GET /api/simulation/:session_id
Get simulation status and results.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "SIM-20251121-001",
    "status": "completed",
    "results": {
      "iterations_completed": 100,
      "convergence": 0.0001,
      "insights": [ ... ]
    },
    "created_at": "2025-11-21T12:00:00Z",
    "completed_at": "2025-11-21T12:04:32Z"
  }
}
```

#### GET /api/simulation/layers
List available simulation layers.

---

### Compliance Endpoints

#### GET /api/compliance/check
Check compliance status.

**Query Parameters:**
- `framework`: Compliance framework (SOC2, GDPR, HIPAA)
- `node_id` (optional): Check specific node

**Response:**
```json
{
  "success": true,
  "data": {
    "framework": "SOC2",
    "status": "compliant",
    "score": 0.94,
    "issues": [
      {
        "severity": "low",
        "description": "Missing audit log for action X",
        "recommendation": "Enable comprehensive logging"
      }
    ],
    "last_audit": "2025-11-01T00:00:00Z"
  }
}
```

#### POST /api/compliance/report
Generate compliance report.

**Request:**
```json
{
  "framework": "SOC2",
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-11-21"
  },
  "format": "pdf"
}
```

---

### Search Endpoints

#### GET /api/search
Search across the knowledge graph.

**Query Parameters:**
- `q`: Search query (required)
- `type`: Node type filter
- `axis`: Axis filter (1-13)
- `limit`: Results limit (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "AX01-KNW-1234",
        "label": "Machine Learning",
        "type": "knowledge",
        "relevance": 0.95,
        "snippet": "...branch of AI focused on..."
      }
    ],
    "total": 125,
    "page": 1,
    "per_page": 50
  }
}
```

#### GET /api/search/suggest
Get search suggestions (autocomplete).

**Query Parameters:**
- `q`: Partial query
- `limit`: Max suggestions (default: 10)

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      "Machine Learning",
      "Machine Learning Algorithms",
      "Machine Learning Models"
    ]
  }
}
```

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token'
  }));
};
```

### Events

#### Subscribe to Node Updates
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'nodes',
  filter: { axis: 1 }
}));
```

#### Receive Updates
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

---

## Examples

### Python Example

```python
import requests

# Authentication
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'user@example.com',
    'password': 'password123'
})
token = response.json()['data']['access_token']

# Create a node
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:5000/api/nodes',
    headers=headers,
    json={
        'node_type': 'knowledge',
        'axis': 1,
        'label': 'Deep Learning',
        'data': {'tags': ['AI', 'ML']}
    }
)
node = response.json()['data']
print(f"Created node: {node['id']}")

# Query the graph
response = requests.post('http://localhost:5000/api/query',
    headers=headers,
    json={
        'query': 'AI-related knowledge',
        'filters': {'axis': 1},
        'limit': 10
    }
)
results = response.json()['data']
print(f"Found {len(results['nodes'])} nodes")
```

### JavaScript Example

```javascript
// Authentication
const login = async () => {
  const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'user@example.com',
      password: 'password123'
    })
  });
  const data = await response.json();
  return data.data.access_token;
};

// Query persona
const queryPersona = async (token) => {
  const response = await fetch('http://localhost:5000/api/persona/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      persona_type: 'knowledge_expert',
      query: 'Explain quantum computing',
      context: { axis: 1 }
    })
  });
  const data = await response.json();
  console.log('Expert response:', data.data.response);
};

// Usage
const token = await login();
await queryPersona(token);
```

### cURL Examples

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password123"}'

# Create Node
curl -X POST http://localhost:5000/api/nodes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "node_type": "knowledge",
    "axis": 1,
    "label": "Blockchain",
    "data": {"tags": ["crypto", "distributed"]}
  }'

# Search
curl -X GET "http://localhost:5000/api/search?q=AI&axis=1&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API Changelog

### v1.0.0 (2025-11-21)
- Initial API release
- All 13-axis endpoints
- Expert persona integration
- Simulation API
- Compliance checking

---

For additional support, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
