"""
Salesforce MCP Connector - PRODUCTION VERSION
---------------------------------------------
Exposes Salesforce CRM capabilities as MCP tools using simple-salesforce.
"""
import os
import logging
from simple_salesforce import Salesforce
from backend.mcp_server.registry import registry

logger = logging.getLogger(__name__)

def get_salesforce_client():
    """Initialize Salesforce client using environment variables."""
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
    domain = os.getenv("SALESFORCE_DOMAIN", "login") # or 'test' for sandbox
    
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
    Search for Accounts or Contacts in Salesforce.
    """
    sf = get_salesforce_client()
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
    Create a Lead record in Salesforce.
    """
    sf = get_salesforce_client()
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
