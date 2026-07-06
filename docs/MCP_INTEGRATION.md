# Model Context Protocol (MCP) Integration

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.2.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Engineering + Connector Governance |
| Review cadence | Every 30 days |

## Overview

DataLogicEngine includes a Model Context Protocol-style connector and tool layer for governed access to resources, tools, prompts, server configuration, connector metrics, and UKG/knowledge-system capabilities.

Current UI surfaces:

1. `/mcp` — MCP hub with server, client, analytics, and examples tabs.
2. `/admin/mcp` — admin console entry.
3. `/admin/mcp/servers` — server registry management.

Current API surfaces:

1. canonical API: `/api/v1/mcp/*`;
2. compatibility alias: `/api/mcp/*`, redirected/mapped to the canonical family where applicable.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. It enables:

- **Resources**: Exposing data and content (knowledge graph stats, pillars, algorithms)
- **Tools**: Providing executable functions (query execution, algorithm invocation)
- **Prompts**: Sharing reusable prompt templates (expert persona, regulatory analysis)
- **Sampling**: Allowing LLM completions (future enhancement)

## Architecture

### Core Components

1. **MCP Protocol Layer** (`core/mcp/mcp_protocol.py`)
   - Message types and structures
   - Error handling
   - Base protocol implementation

2. **MCP Server** (`core/mcp/mcp_server.py`)
   - Serves resources, tools, and prompts
   - Handles client connections
   - Manages subscriptions

3. **MCP Client** (`core/mcp/mcp_client.py`)
   - Connects to MCP servers
   - Consumes resources and tools
   - Manages server communication

4. **MCP Manager** (`core/mcp/mcp_manager.py`)
   - Central registry for servers and clients
   - Orchestrates connections
   - Integrates with AppOrchestrator

5. **Database Models** (`models.py`)
   - MCPServer: Server configurations
   - MCPResource: Resource definitions
   - MCPTool: Tool specifications
   - MCPPrompt: Prompt templates

6. **API Endpoints** (`backend/routes/mcp_routes.py`)
   - REST API for MCP management
   - Server/client CRUD operations
   - Resource/tool/prompt access

7. **Frontend Console** (`frontend/app/mcp/page.tsx`)
   - Web UI for MCP management
   - Server monitoring
   - Tool execution interface

## Features

### Default UKG MCP Server

The DataLogicEngine automatically creates a default MCP server named **"DataLogicEngine-UKG"** that exposes:

#### Resources

1. **Knowledge Graph Statistics** (`ukg://graph/stats`)
   - Current graph metrics
   - Node and edge counts
   - System health

2. **Knowledge Pillars** (`ukg://pillars`)
   - List of knowledge pillars
   - Identity, Technology, Healthcare, Finance, etc.

3. **Knowledge Algorithms** (`ukg://algorithms`)
   - Available KA implementations
   - 56+ specialized algorithms

#### Tools

1. **query_knowledge_graph**
   - Execute natural language queries against UKG
   - Returns simulation results
   - Integrates with SimulationEngine

2. **execute_knowledge_algorithm**
   - Run specific knowledge algorithms
   - Parameterized execution
   - Direct KA invocation

#### Prompts

1. **regulatory_analysis**
   - Template for regulatory compliance analysis
   - Supports GDPR, HIPAA, SOX, etc.
   - Generates structured queries

2. **expert_persona**
   - Expert domain simulation template
   - Multi-domain support
   - Integrates with Persona System

## Usage

### Accessing the MCP Console

1. Navigate to `/mcp` in the product shell.
2. Use `/admin/mcp` and `/admin/mcp/servers` for owner/admin server management.
3. The MCP surfaces provide:
   - Server management
   - Resource browsing
   - Tool execution
   - Prompt generation
   - Statistics dashboard

### Creating a New MCP Server

```python
from core.mcp import MCPManager

# Initialize manager
manager = MCPManager()

# Create server
server = manager.create_server(
    name="My-Custom-Server",
    version="1.0.0",
    description="Custom MCP server for specialized tasks"
)

# Register a resource
async def get_custom_data(params):
    return "Custom data response"

server.register_resource(
    uri="custom://data",
    name="Custom Data",
    handler=get_custom_data,
    description="Custom data resource"
)

# Register a tool
async def custom_tool(arguments):
    query = arguments.get("query")
    return f"Processed: {query}"

server.register_tool(
    name="custom_processor",
    description="Processes custom queries",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    handler=custom_tool
)
```

### Using the MCP Client

```python
from core.mcp import MCPManager, MCPClient

manager = MCPManager()

# Create client
client = manager.create_client(name="DataLogicEngine")

# Get server
server = manager.get_server_by_name("DataLogicEngine-UKG")

# Connect client to server
await manager.connect_client_to_server(client.client_id, server.server_id)

# List resources
resources = await client.list_resources(server)

# Call a tool
result = await client.call_tool(
    server,
    "query_knowledge_graph",
    {"query": "What are the healthcare regulations?"}
)
```

### REST API Examples

#### List Servers

```bash
GET /api/v1/mcp/servers
```

Response:
```json
{
  "success": true,
  "servers": [
    {
      "server_id": "uuid",
      "name": "DataLogicEngine-UKG",
      "version": "1.0.0",
      "status": "active",
      "capabilities": {
        "resources": true,
        "tools": true,
        "prompts": true
      }
    }
  ]
}
```

#### Call a Tool

```bash
POST /api/v1/mcp/servers/{server_id}/tools/{tool_id}/call
Content-Type: application/json

{
  "arguments": {
    "query": "Healthcare compliance requirements"
  }
}
```

#### Get a Prompt

```bash
POST /api/v1/mcp/servers/{server_id}/prompts/{prompt_id}/get
Content-Type: application/json

{
  "arguments": {
    "framework": "GDPR",
    "domain": "Healthcare"
  }
}
```

## Integration with DataLogicEngine Components

### AppOrchestrator Integration

The MCP Manager is automatically initialized within the AppOrchestrator:

```python
class AppOrchestrator:
    def __init__(self, config):
        # ... other initialization
        self.mcp_manager = None
        self._initialize_mcp()

    def _initialize_mcp(self):
        self.mcp_manager = MCPManager(app_orchestrator=self)
        self.mcp_manager.setup_default_servers()
```

### Knowledge Algorithm Integration

MCP tools can execute knowledge algorithms:

```python
# Tool: execute_knowledge_algorithm
async def execute_algorithm(arguments):
    algorithm_name = arguments.get("algorithm")
    params = arguments.get("params", {})

    if self.app_orchestrator and self.app_orchestrator.ka_loader:
        ka_instance = self.app_orchestrator.ka_loader.get_algorithm(algorithm_name)
        result = await ka_instance.execute(params)
        return result
```

### Simulation Engine Integration

MCP queries are processed through the simulation engine:

```python
async def query_graph(arguments):
    query = arguments.get("query")

    if self.app_orchestrator and self.app_orchestrator.simulation_engine:
        result = await self.app_orchestrator.process_request(
            user_query=query,
            simulation_params=arguments.get("context", {})
        )
        return result
```

## Database Schema

### MCPServer Table

```sql
CREATE TABLE mcp_servers (
    id INTEGER PRIMARY KEY,
    server_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    version VARCHAR(32) DEFAULT '1.0.0',
    description TEXT,
    status VARCHAR(20) DEFAULT 'inactive',
    protocol_version VARCHAR(32) DEFAULT '2024-11-05',
    supports_resources BOOLEAN DEFAULT TRUE,
    supports_tools BOOLEAN DEFAULT TRUE,
    supports_prompts BOOLEAN DEFAULT TRUE,
    supports_logging BOOLEAN DEFAULT TRUE,
    config JSON,
    metadata JSON,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_active TIMESTAMP
);
```

### MCPResource Table

```sql
CREATE TABLE mcp_resources (
    id INTEGER PRIMARY KEY,
    server_id INTEGER REFERENCES mcp_servers(id),
    uri VARCHAR(256) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    mime_type VARCHAR(64),
    metadata JSON,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### MCPTool Table

```sql
CREATE TABLE mcp_tools (
    id INTEGER PRIMARY KEY,
    server_id INTEGER REFERENCES mcp_servers(id),
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    input_schema JSON NOT NULL,
    metadata JSON,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### MCPPrompt Table

```sql
CREATE TABLE mcp_prompts (
    id INTEGER PRIMARY KEY,
    server_id INTEGER REFERENCES mcp_servers(id),
    name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    arguments JSON,
    metadata JSON,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Configuration

### Environment Variables

```bash
# MCP Configuration (optional)
MCP_ENABLED=true
MCP_DEFAULT_SERVER_NAME=DataLogicEngine-UKG
MCP_PROTOCOL_VERSION=2024-11-05
```

### Config.py Integration

```python
# MCP settings
MCP_ENABLED = os.environ.get('MCP_ENABLED', 'true').lower() == 'true'
MCP_DEFAULT_SERVER_NAME = os.environ.get('MCP_DEFAULT_SERVER_NAME', 'DataLogicEngine-UKG')
MCP_PROTOCOL_VERSION = os.environ.get('MCP_PROTOCOL_VERSION', '2024-11-05')
```

## Security Considerations

1. **Authentication**: MCP routes use the current API decorator policy (`@api_session_login_required`, `@api_login_required`, and `@api_admin_required` compatibility alias depending on endpoint behavior).
2. **Authorization and scopes**: connector execution enforces MCP/connector scopes such as `mcp:execute` and connector-specific read/write scopes.
3. **Owner operations**: setup-default, dynamic server start/stop, config writes, and delete operations are owner/admin-style actions under the current single-owner desktop model.
4. **Input Validation**: JSON schema validation is required for tool arguments.
5. **Error Handling**: error responses must avoid sensitive exception disclosure.
6. **Rate Limiting**: production web/cloud deployments should keep MCP endpoints behind the same rate/resource controls as other API routes.

## Performance

- **Async Operations**: All MCP operations use asyncio for non-blocking execution
- **Database Indexing**: Indexes on `server_id`, `uri`, `name` fields
- **Caching**: Consider implementing caching for frequently accessed resources
- **Connection Pooling**: SQLAlchemy connection pooling enabled

## Monitoring and Logging

### Statistics Endpoint

```bash
GET /api/v1/mcp/stats
```

Returns:
- Total servers
- Active servers
- Total resources, tools, prompts
- Request success/failure rates

### Logging

All MCP operations are logged:
- Server creation/deletion
- Client connections
- Tool executions
- Resource accesses
- Errors and exceptions

## Future Enhancements

MCP future items are consolidated in the root `TODO.md`. Keep implementation decisions there so completed connector credential, scope, contract, and metrics work is not restated as future work in this integration reference.

## Troubleshooting

### Server Not Appearing in Console

1. Check database connection
2. Verify server was created successfully
3. Check browser console for errors
4. Refresh the page

### Tool Execution Fails

1. Verify tool arguments match schema
2. Check server logs for errors
3. Ensure AppOrchestrator is initialized
4. Verify database connection

### Frontend Not Loading

1. Ensure the frontend is running (`npm --prefix frontend run dev`) or the packaged Electron shell is active.
2. Check axios configuration
3. Verify API endpoints are accessible
4. Check browser console for errors

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
- DataLogicEngine Architecture Documentation
- Universal Knowledge Graph Documentation

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review this documentation
3. Consult ARCHITECTURE.md for system overview
4. Follow the escalation path in `docs/OPERATIONAL_RUNBOOKS.md`

## Change notes for v1.2.0

1. Removed the remaining historical OAuth wording from future-work guidance and aligned it to credential, scope, contract, and metrics governance.
2. Replaced the generic support contact with the operational runbook escalation path.

## Change notes for v1.1.0

1. Added document metadata for active-doc governance.
2. Updated UI paths from the obsolete `/mcp-console` reference to `/mcp`, `/admin/mcp`, and `/admin/mcp/servers`.
3. Updated REST examples to the canonical `/api/v1/mcp/*` API family while noting the legacy alias.
4. Updated security guidance to match the current API decorator and connector-scope model.
