# MCP (Model Context Protocol) Module

This module implements the Model Context Protocol for DataLogicEngine, enabling standardized communication between LLM applications and the Universal Knowledge Graph system.

## Module Structure

```
core/mcp/
├── __init__.py              # Module exports
├── mcp_protocol.py          # Core protocol implementation
├── mcp_server.py            # MCP server implementation
├── mcp_client.py            # MCP client implementation
├── mcp_manager.py           # Server/client manager and registry
└── README.md                # This file
```

## Components

### mcp_protocol.py

Core protocol definitions:
- `MCPMessage`: JSON-RPC 2.0 message format
- `MCPResource`: Resource definitions
- `MCPTool`: Tool specifications
- `MCPPrompt`: Prompt templates
- `MCPServerInfo`, `MCPClientInfo`: Server/client metadata
- `MCPError`, `MCPErrorCode`: Error handling
- `MCPRequestHandler`: Base request handler class

### mcp_server.py

MCP Server implementation:
- Serves resources, tools, and prompts via MCP protocol
- Handles initialization, resource listing, tool calls, etc.
- Supports resource subscriptions
- Tracks usage statistics

Key methods:
- `register_resource()`: Add a new resource
- `register_tool()`: Add a new tool
- `register_prompt()`: Add a new prompt template
- `handle_request()`: Process incoming MCP requests

### mcp_client.py

MCP Client implementation:
- Connects to MCP servers
- Lists and accesses resources
- Calls tools
- Retrieves prompts
- Manages subscriptions

Key methods:
- `initialize()`: Connect to a server
- `list_resources()`: Get available resources
- `read_resource()`: Read a specific resource
- `call_tool()`: Execute a tool
- `get_prompt()`: Retrieve a prompt template

### mcp_manager.py

Central management and orchestration:
- Server registry
- Client registry
- Connection management
- Default server setup
- Integration with AppOrchestrator

Key methods:
- `create_server()`: Create a new MCP server
- `create_client()`: Create a new MCP client
- `connect_client_to_server()`: Establish connection
- `setup_default_servers()`: Initialize default UKG server

## Usage Examples

### Creating a Server

```python
from core.mcp import MCPServer

# Create server
server = MCPServer(
    name="My-Server",
    version="1.0.0",
    description="Custom MCP server"
)

# Register a resource
async def get_data(params):
    return {"data": "example"}

server.register_resource(
    uri="custom://data",
    name="Custom Data",
    handler=get_data,
    description="Example resource",
    mime_type="application/json"
)

# Register a tool
async def process_query(arguments):
    query = arguments.get("query")
    return f"Processed: {query}"

server.register_tool(
    name="process",
    description="Process a query",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    handler=process_query
)
```

### Using the Manager

```python
from core.mcp import MCPManager

# Initialize manager
manager = MCPManager()

# Create and setup default servers
ukg_server = manager.setup_default_servers()

# Create a client
client = manager.create_client(name="MyClient")

# Connect client to server
await manager.connect_client_to_server(
    client.client_id,
    ukg_server.server_id
)

# Use the client
resources = await client.list_resources(ukg_server)
result = await client.call_tool(
    ukg_server,
    "query_knowledge_graph",
    {"query": "What is AI?"}
)
```

## Integration with DataLogicEngine

The MCP module is integrated with DataLogicEngine through the AppOrchestrator:

```python
# In AppOrchestrator.__init__()
from core.mcp import MCPManager

self.mcp_manager = MCPManager(app_orchestrator=self)
self.mcp_manager.setup_default_servers()
```

This enables:
- Automatic MCP server initialization
- Integration with SimulationEngine for query processing
- Access to KnowledgeAlgorithms through tools
- Persona system integration for prompts

## Protocol Compliance

This implementation follows the Model Context Protocol specification (version 2024-11-05):

- ✅ JSON-RPC 2.0 message format
- ✅ Server initialization handshake
- ✅ Resources (list, read, subscribe, unsubscribe)
- ✅ Tools (list, call)
- ✅ Prompts (list, get)
- ✅ Error handling
- ✅ Capabilities negotiation
- ⏳ Logging (partial implementation)
- ⏳ Sampling (future enhancement)

## Testing

```python
import asyncio
from core.mcp import MCPServer, MCPClient, MCPMessage, MCPMethod

# Test server/client interaction
async def test_mcp():
    # Create server
    server = MCPServer(name="TestServer")

    # Register test resource
    async def test_resource(params):
        return "Test data"

    server.register_resource(
        uri="test://resource",
        name="Test Resource",
        handler=test_resource
    )

    # Create client
    client = MCPClient(name="TestClient")

    # Initialize connection
    await client.initialize(server)

    # List resources
    resources = await client.list_resources(server)
    print(f"Resources: {resources}")

    # Read resource
    data = await client.read_resource(server, "test://resource")
    print(f"Data: {data}")

# Run test
asyncio.run(test_mcp())
```

## Error Handling

The module uses standardized error codes:

- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32001`: Resource not found
- `-32002`: Tool not found
- `-32003`: Prompt not found
- `-32004`: Tool execution error

Example:
```python
from core.mcp import MCPError, MCPErrorCode

try:
    result = await client.call_tool(server, "nonexistent", {})
except MCPError as e:
    print(f"Error {e.code}: {e.message}")
```

## Performance Considerations

- All handlers are async for non-blocking execution
- Minimal overhead in message routing
- Efficient JSON serialization
- Resource subscriptions use lightweight tracking
- Statistics tracked in-memory with optional persistence

## Security

- Input validation on all parameters
- Error messages sanitized (no sensitive data)
- Resource URIs validated
- Tool arguments validated against schema
- Admin operations require authentication (when integrated with Flask)

## Dependencies

- Python 3.7+
- asyncio (built-in)
- dataclasses (built-in)
- typing (built-in)
- logging (built-in)

No external dependencies required!

## License

Part of the DataLogicEngine project.
