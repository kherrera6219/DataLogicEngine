"""
Salesforce MCP Connector
-----------------------
Exposes Salesforce CRM capabilities as MCP tools.
"""

from backend.mcp_server.registry import registry

@registry.register(
    name="salesforce_crm_lookup",
    description="Look up a customer or account in Salesforce CRM by name or email.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Name or email to search for"
            }
        },
        "required": ["query"]
    }
)
def crm_lookup(query: str):
    """
    Mock implementation of Salesforce lookup.
    """
    # In a real impl, this would use simple-salesforce or requests
    return {
        "status": "found",
        "results": [
            {
                "id": "0015e000002XyzABC",
                "name": "Acme Corp",
                "industry": "Technology",
                "annual_revenue": 1000000,
                "sentiment_score": 0.85
            }
        ],
        "source": "Salesforce Production"
    }

@registry.register(
    name="salesforce_lead_create",
    description="Create a new lead in Salesforce.",
    input_schema={
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "company": {"type": "string"},
            "email": {"type": "string"}
        },
        "required": ["last_name", "company", "email"]
    }
)
def lead_create(first_name: str, last_name: str, company: str, email: str):
    """
    Mock implementation of Salesforce lead creation.
    """
    return {
        "status": "success",
        "lead_id": "00Q5e000004Abc123",
        "message": f"Lead {first_name} {last_name} created successfully for {company}."
    }
