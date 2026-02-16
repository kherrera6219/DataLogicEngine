"""
Jira MCP Connector - PRODUCTION VERSION
---------------------------------------
Exposes Jira Project Management capabilities as MCP tools using the jira library.
"""
import os
import logging
from jira import JIRA
from backend.mcp_server.registry import registry

logger = logging.getLogger(__name__)

def get_jira_client():
    """Initialize Jira client using environment variables."""
    server = os.getenv("JIRA_SERVER_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN") # Use API tokens for cloud, password for on-prem
    
    if not all([server, email, api_token]):
        logger.warning("Jira credentials missing. Tools will operate in failover mode.")
        return None
        
    try:
        # Authentication via email and API token
        options = {'server': server}
        jira = JIRA(options=options, basic_auth=(email, api_token))
        return jira
    except Exception as e:
        logger.error(f"Jira connection failed: {e}")
        return None

@registry.register(
    name="jira_ticket_create",
    description="Create a new ticket/issue in Jira.",
    connector="jira",
    required_scopes=["mcp:execute", "connector:jira:write"],
    input_schema={
        "type": "object",
        "properties": {
            "project_key": {"type": "string", "description": "e.g., UKG, PROJ"},
            "summary": {"type": "string"},
            "description": {"type": "string"},
            "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story", "Incident"], "default": "Task"}
        },
        "required": ["project_key", "summary"]
    }
)
def ticket_create(project_key: str, summary: str, description: str = "", issue_type: str = "Task"):
    """
    Create an Issue in Jira.
    """
    jira = get_jira_client()
    if not jira:
        return {"error": "Jira API unavailable. Check credentials.", "status": "fail"}

    try:
        issue_dict = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        new_issue = jira.create_issue(fields=issue_dict)
        
        return {
            "status": "created",
            "key": new_issue.key,
            "link": f"{jira.client_info()}/browse/{new_issue.key}",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Jira ticket creation failed: {e}")
        return {"error": str(e), "status": "error"}

@registry.register(
    name="jira_status_check",
    description="Get the status of a specific Jira ticket.",
    connector="jira",
    required_scopes=["mcp:execute", "connector:jira:read"],
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
    Retrieve status and metadata for a specific Jira issue.
    """
    jira = get_jira_client()
    if not jira:
        return {"error": "Jira API unavailable.", "status": "fail"}

    try:
        issue = jira.issue(ticket_key)
        return {
            "key": ticket_key,
            "status": str(issue.fields.status.name),
            "summary": issue.fields.summary,
            "assignee": str(issue.fields.assignee) if issue.fields.assignee else "Unassigned",
            "priority": str(issue.fields.priority.name) if hasattr(issue.fields, 'priority') else "None",
            "updated": issue.fields.updated
        }
    except Exception as e:
        logger.error(f"Jira status check failed: {e}")
        return {"error": str(e), "status": "error"}
