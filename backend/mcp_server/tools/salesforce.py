"""
Salesforce MCP Connector - PRODUCTION VERSION
---------------------------------------------
Exposes Salesforce CRM capabilities as MCP tools using simple-salesforce.
"""
import os
import logging
import requests
from simple_salesforce import Salesforce
from backend.mcp_server.registry import registry
from backend.mcp_server.oauth_manager import OAuthTokenError, get_connector_oauth_token

logger = logging.getLogger(__name__)


def _salesforce_oauth_token_url(domain: str) -> str:
    configured = os.getenv("SALESFORCE_OAUTH_TOKEN_URL")
    if configured:
        return configured
    normalized = (domain or "login").strip().lower()
    host = normalized if "." in normalized else ("test.salesforce.com" if normalized == "test" else "login.salesforce.com")
    return f"https://{host}/services/oauth2/token"


def _refresh_salesforce_oauth_token(refresh_token: str, _account) -> dict:
    """Refresh Salesforce OAuth token using configured client credentials."""
    domain = os.getenv("SALESFORCE_DOMAIN", "login")
    token_url = _salesforce_oauth_token_url(domain)
    client_id = os.getenv("SALESFORCE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_OAUTH_CLIENT_SECRET")
    if not all([client_id, client_secret]):
        raise OAuthTokenError(
            "Salesforce OAuth refresh requires SALESFORCE_OAUTH_CLIENT_ID and SALESFORCE_OAUTH_CLIENT_SECRET."
        )

    response = requests.post(
        token_url,
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise OAuthTokenError(f"Salesforce OAuth refresh failed ({response.status_code}).")

    payload = response.json() if response.content else {}
    if not payload.get("access_token"):
        raise OAuthTokenError("Salesforce OAuth refresh response missing access_token.")
    return payload


def get_salesforce_client(_execution_context: dict | None = None):
    """Initialize Salesforce client via managed OAuth token or fallback username/password."""
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
    domain = os.getenv("SALESFORCE_DOMAIN", "login")  # or 'test' for sandbox

    try:
        oauth_payload = get_connector_oauth_token(
            "salesforce",
            execution_context=_execution_context,
            refresh_callback=_refresh_salesforce_oauth_token,
        )
        if oauth_payload and oauth_payload.get("access_token"):
            instance_url = (
                oauth_payload.get("instance_url")
                or os.getenv("SALESFORCE_INSTANCE_URL")
            )
            if instance_url:
                return Salesforce(
                    session_id=str(oauth_payload["access_token"]),
                    instance_url=str(instance_url),
                    domain=domain,
                )
            logger.warning("Salesforce OAuth token available but instance_url is missing; falling back to password auth.")
    except OAuthTokenError as exc:
        logger.warning("Managed Salesforce OAuth token unavailable: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Managed Salesforce OAuth client initialization failed: %s", exc)
        return None

    if not all([username, password, security_token]):
        logger.warning("Salesforce credentials missing. Tools will operate in failover mode.")
        return None

    try:
        sf = Salesforce(username=username, password=password, security_token=security_token, domain=domain)
        return sf
    except Exception as e:
        logger.error(f"Salesforce connection failed: {e}")
        return None

@registry.register(
    name="salesforce_crm_lookup",
    description="Look up a customer or account in Salesforce CRM by name or email.",
    connector="salesforce",
    required_scopes=["mcp:execute", "connector:salesforce:read"],
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Name or email to search for"
            }
        },
        "required": ["query"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success", "error", "fail"]},
            "results": {"type": "array"},
            "source": {"type": "string"},
            "error": {"type": "string"},
        },
        "required": ["status"],
    },
)
def crm_lookup(query: str, _execution_context: dict | None = None):
    """
    Search for Accounts or Contacts in Salesforce.
    """
    sf = get_salesforce_client(_execution_context)
    if not sf:
        return {"error": "Salesforce API unavailable. Check credentials.", "status": "fail"}

    try:
        # Search for accounts and contacts
        search_query = f"FIND {{{query}}} IN ALL FIELDS RETURNING Account(Id, Name, Industry, AnnualRevenue, Type), Contact(Id, Name, Email, Title)"
        results = sf.search(search_query)
        
        return {
            "status": "success",
            "results": results.get('searchRecords', []),
            "source": f"Salesforce {sf.sf_instance}"
        }
    except Exception as e:
        logger.error(f"Salesforce lookup failed: {e}")
        return {"error": str(e), "status": "error"}

@registry.register(
    name="salesforce_lead_create",
    description="Create a new lead in Salesforce.",
    connector="salesforce",
    required_scopes=["mcp:execute", "connector:salesforce:write"],
    input_schema={
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "company": {"type": "string"},
            "email": {"type": "string"}
        },
        "required": ["last_name", "company", "email"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success", "error", "fail"]},
            "lead_id": {"type": "string"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
        "required": ["status"],
    },
)
def lead_create(
    first_name: str = "",
    last_name: str = "",
    company: str = "",
    email: str = "",
    _execution_context: dict | None = None,
):
    """
    Create a Lead record in Salesforce.
    """
    sf = get_salesforce_client(_execution_context)
    if not sf:
        return {"error": "Salesforce API unavailable.", "status": "fail"}

    try:
        result = sf.Lead.create({
            'FirstName': first_name,
            'LastName': last_name,
            'Company': company,
            'Email': email,
            'LeadSource': 'UKG DataLogicEngine'
        })
        
        return {
            "status": "success",
            "lead_id": result.get('id'),
            "message": f"Lead {first_name} {last_name} created successfully."
        }
    except Exception as e:
        logger.error(f"Salesforce lead creation failed: {e}")
        return {"error": str(e), "status": "error"}
