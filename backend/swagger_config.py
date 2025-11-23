"""
OpenAPI/Swagger configuration for UKG System API documentation
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

# Create APISpec instance
spec = APISpec(
    title="Universal Knowledge Graph (UKG) System API",
    version="1.0.0",
    openapi_version="3.0.3",
    info=dict(
        description="API documentation for the Universal Knowledge Graph System. "
                   "A comprehensive AI knowledge management system with a 13-axis knowledge graph.",
        contact=dict(
            name="UKG Team",
            email="support@example.com"
        ),
        license=dict(
            name="MIT",
            url="https://opensource.org/licenses/MIT"
        )
    ),
    servers=[
        dict(
            url="http://localhost:5000",
            description="Development server"
        ),
        dict(
            url="https://api.ukg-system.com",
            description="Production server"
        )
    ],
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

# Security schemes
spec.components.security_scheme(
    "bearerAuth",
    {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
)

spec.components.security_scheme(
    "cookieAuth",
    {
        "type": "apiKey",
        "in": "cookie",
        "name": "session"
    }
)

# Common response schemas
spec.components.schema(
    "ErrorResponse",
    {
        "type": "object",
        "properties": {
            "error": {"type": "string", "description": "Error message"},
            "code": {"type": "string", "description": "Error code"},
            "details": {"type": "object", "description": "Additional error details"}
        },
        "required": ["error"]
    }
)

spec.components.schema(
    "SuccessResponse",
    {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "Operation success status"},
            "message": {"type": "string", "description": "Success message"},
            "data": {"type": "object", "description": "Response data"}
        },
        "required": ["success"]
    }
)

# Authentication schemas
spec.components.schema(
    "LoginRequest",
    {
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Username"},
            "password": {"type": "string", "format": "password", "description": "Password"}
        },
        "required": ["username", "password"]
    }
)

spec.components.schema(
    "LoginResponse",
    {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "token": {"type": "string", "description": "JWT authentication token"},
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                }
            }
        },
        "required": ["success", "token", "user"]
    }
)

# Query schemas
spec.components.schema(
    "QueryRequest",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language query"},
            "target_confidence": {
                "type": "number",
                "format": "float",
                "minimum": 0.6,
                "maximum": 0.95,
                "description": "Target confidence threshold"
            },
            "chat_id": {"type": "string", "format": "uuid", "nullable": True},
            "use_location_context": {"type": "boolean", "default": True},
            "use_research_agents": {"type": "boolean", "default": True},
            "active_personas": {
                "type": "array",
                "items": {"type": "string", "enum": ["KE", "SE", "RE", "CE"]}
            }
        },
        "required": ["query"]
    }
)

spec.components.schema(
    "QueryResponse",
    {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "response": {"type": "string", "description": "Natural language response"},
            "confidence": {
                "type": "number",
                "format": "float",
                "description": "Confidence score"
            },
            "chat_id": {"type": "string", "format": "uuid"},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string", "format": "uri"},
                        "relevance": {"type": "number", "format": "float"}
                    }
                }
            }
        },
        "required": ["success", "response"]
    }
)


def get_apispec():
    """
    Get the APISpec instance

    Returns:
        APISpec: Configured APISpec instance
    """
    return spec


def get_swagger_json():
    """
    Get Swagger JSON specification

    Returns:
        dict: Swagger/OpenAPI specification as dictionary
    """
    return spec.to_dict()
