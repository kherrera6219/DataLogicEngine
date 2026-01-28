"""
Jira MCP Connector
-----------------
Exposes Jira Project Management capabilities as MCP tools.
"""

from backend.mcp_server.registry import registry

@registry.register(
    name="jira_ticket_create",
    description="Create a new ticket/issue in Jira.",
    input_schema={
        "type": "object",
        "properties": {
            "project_key": {"type": "string", "description": "e.g., UKG, PROJ"},
            "summary": {"type": "string"},
            "description": {"type": "string"},
            "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story"], "default": "Task"}
        },
        "required": ["project_key", "summary"]
    }
)
def ticket_create(project_key: str, summary: str, description: str = "", issue_type: str = "Task"):
    """
    Mock implementation of Jira ticket creation.
    """
    ticket_id = f"{project_key}-{(summary.__hash__() % 1000) + 1000}"
    return {
        "status": "created",
        "key": ticket_id,
        "link": f"https://jira.enterprise.com/browse/{ticket_id}",
        "summary": summary
    }

@registry.register(
    name="jira_status_check",
    description="Get the status of a specific Jira ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_key": {"type": "string", "description": "The Ticket ID (e.g., UKG-123)"}
        },
        "required": ["ticket_key"]
    }
)
def status_check(ticket_key: str):
    """
    Mock implementation of Jira status check.
    """
    return {
        "key": ticket_key,
        "status": "In Progress",
        "assignee": "Jane Doe",
        "updated": "2024-03-15T10:30:00Z"
    }
