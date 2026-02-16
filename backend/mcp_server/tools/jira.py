"""
Jira MCP Connector - PRODUCTION VERSION
---------------------------------------
Exposes Jira Project Management capabilities as MCP tools using the jira library.
"""
import os
import logging
import requests
from jira import JIRA
from backend.mcp_server.registry import registry
from backend.mcp_server.oauth_manager import OAuthTokenError, get_connector_oauth_token

logger = logging.getLogger(__name__)


def _refresh_jira_oauth_token(refresh_token: str, _account) -> dict:
    """Refresh Jira OAuth token using Atlassian OAuth token endpoint."""
    token_url = os.getenv("JIRA_OAUTH_TOKEN_URL", "https://auth.atlassian.com/oauth/token")
    client_id = os.getenv("JIRA_OAUTH_CLIENT_ID")
    client_secret = os.getenv("JIRA_OAUTH_CLIENT_SECRET")
    if not all([client_id, client_secret]):
        raise OAuthTokenError("Jira OAuth refresh requires JIRA_OAUTH_CLIENT_ID and JIRA_OAUTH_CLIENT_SECRET.")

    response = requests.post(
        token_url,
        json={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise OAuthTokenError(f"Jira OAuth refresh failed ({response.status_code}).")

    payload = response.json() if response.content else {}
    if not payload.get("access_token"):
        raise OAuthTokenError("Jira OAuth refresh response missing access_token.")
    return payload


def get_jira_client(_execution_context: dict | None = None):
    """Initialize Jira client via managed OAuth token or fallback basic auth."""
    server = os.getenv("JIRA_SERVER_URL")
    email = os.getenv("JIRA_USER_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")  # Use API tokens for cloud, password for on-prem

    if not server:
        logger.warning("Jira server URL missing. Tools will operate in failover mode.")
        return None

    try:
        oauth_payload = get_connector_oauth_token(
            "jira",
            execution_context=_execution_context,
            refresh_callback=_refresh_jira_oauth_token,
        )
        if oauth_payload and oauth_payload.get("access_token"):
            options = {"server": server}
            return JIRA(options=options, token_auth=str(oauth_payload["access_token"]))
    except OAuthTokenError as exc:
        logger.warning("Managed Jira OAuth token unavailable: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Managed Jira OAuth client initialization failed: %s", exc)
        return None

    if not all([email, api_token]):
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
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["created", "error", "fail"]},
            "key": {"type": "string"},
            "link": {"type": "string"},
            "summary": {"type": "string"},
            "error": {"type": "string"},
        },
        "required": ["status"],
    },
)
def ticket_create(
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    _execution_context: dict | None = None,
):
    """
    Create an Issue in Jira.
    """
    jira = get_jira_client(_execution_context)
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
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "key": {"type": "string"},
            "summary": {"type": "string"},
            "assignee": {"type": "string"},
            "priority": {"type": "string"},
            "updated": {"type": "string"},
            "error": {"type": "string"},
        },
        "required": ["status"],
    },
)
def status_check(ticket_key: str, _execution_context: dict | None = None):
    """
    Retrieve status and metadata for a specific Jira issue.
    """
    jira = get_jira_client(_execution_context)
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
