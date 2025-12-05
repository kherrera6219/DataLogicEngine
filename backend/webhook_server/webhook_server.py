
"""
UKG Webhook Server

This server handles incoming webhooks from external services and integrations,
processing events and triggering appropriate actions in the UKG system.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
import logging
import time
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enterprise_architecture import get_enterprise_architecture

# Initialize FastAPI app
app = FastAPI(
    title="UKG Webhook Server",
    description="Webhook Server for the Universal Knowledge Graph Enterprise Architecture",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Webhook-Server")

# Get enterprise architecture
enterprise_arch = get_enterprise_architecture()

# Webhook secret keys for verification
# In production, these would be stored securely (e.g., environment variables)
WEBHOOK_SECRETS = {
    "github": os.environ.get("GITHUB_WEBHOOK_SECRET", "github_webhook_secret"),
    "slack": os.environ.get("SLACK_WEBHOOK_SECRET", "slack_webhook_secret"),
    "gitlab": os.environ.get("GITLAB_WEBHOOK_SECRET", "gitlab_webhook_secret"),
    "jira": os.environ.get("JIRA_WEBHOOK_SECRET", "jira_webhook_secret"),
}

# Webhook processors registry
webhook_processors = {}

def register_webhook_processor(integration_name):
    """Decorator to register webhook processors"""
    def decorator(func):
        webhook_processors[integration_name] = func
        logger.info(f"Registered webhook processor for: {integration_name}")
        return func
    return decorator

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests through the webhook server"""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the request
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Time: {process_time:.4f}s"
    )
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the Webhook Server"""
    return {
        "status": "healthy",
        "service": "UKG Webhook Server",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Webhook integrations information
@app.get("/webhooks")
async def get_webhook_integrations():
    """Get information about available webhook integrations"""
    return {
        "available_integrations": list(webhook_processors.keys()),
        "registered_count": len(webhook_processors),
        "timestamp": datetime.now().isoformat()
    }

# Generic webhook handler
@app.post("/webhooks/{integration_name}")
async def process_webhook(integration_name: str, request: Request):
    """
    Process incoming webhooks from various services
    
    Args:
        integration_name: The name of the integration (github, slack, etc.)
        request: The webhook request
    """
    # Check if we have a processor for this integration
    if integration_name not in webhook_processors:
        logger.warning(f"No webhook processor registered for: {integration_name}")
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"No webhook processor found for {integration_name}",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Verify webhook signature if applicable
    if integration_name in WEBHOOK_SECRETS:
        signature = request.headers.get(f"X-{integration_name.capitalize()}-Signature", "")
        if not signature:
            logger.warning(f"Missing signature for {integration_name} webhook")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Missing webhook signature",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Get request body for verification
        body = await request.body()
        
        # Verify signature (implementation varies by integration)
        # This is a simplified example
        secret = WEBHOOK_SECRETS[integration_name]
        computed_signature = hmac.new(
            secret.encode(), 
            body, 
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            logger.warning(f"Invalid signature for {integration_name} webhook")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "Invalid webhook signature",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Parse request body
    try:
        body_json = await request.json()
    except Exception as e:
        logger.error(f"Error parsing webhook request body: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid JSON in request body",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Process the webhook
    try:
        # Call the registered processor
        processor = webhook_processors[integration_name]
        result = await processor(body_json, request.headers)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Webhook processed successfully",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error processing {integration_name} webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Error processing webhook",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Register webhook processors for different integrations

@register_webhook_processor("github")
async def process_github_webhook(data: Dict[str, Any], headers: Dict[str, str]):
    """Process GitHub webhooks"""
    event_type = headers.get("X-GitHub-Event", "")
    logger.info(f"Processing GitHub webhook: {event_type}")
    
    # Process different GitHub event types
    if event_type == "push":
        # Handle code push event
        repo = data.get("repository", {}).get("full_name", "")
        branch = data.get("ref", "").replace("refs/heads/", "")
        commits = data.get("commits", [])
        
        logger.info(f"GitHub push to {repo}/{branch} with {len(commits)} commits")
        
        # In a real implementation, trigger UKG updates based on repository changes
        return {
            "event_type": event_type,
            "repository": repo,
            "branch": branch,
            "commit_count": len(commits),
            "action": "knowledge_update_scheduled"
        }
    
    # Process other GitHub events as needed
    return {"event_type": event_type, "action": "acknowledged"}

@register_webhook_processor("slack")
async def process_slack_webhook(data: Dict[str, Any], headers: Dict[str, str]):
    """Process Slack webhooks"""
    # Slack events API verification challenge
    if "challenge" in data:
        return {"challenge": data["challenge"]}
    
    # Process Slack events
    event_type = data.get("event", {}).get("type", "")
    logger.info(f"Processing Slack webhook: {event_type}")
    
    # In a real implementation, process Slack events and possibly
    # trigger knowledge updates or user notifications
    
    return {"event_type": event_type, "action": "acknowledged"}

@register_webhook_processor("jira")
async def process_jira_webhook(data: Dict[str, Any], headers: Dict[str, str]):
    """Process Jira webhooks"""
    event_type = data.get("webhookEvent", "")
    logger.info(f"Processing Jira webhook: {event_type}")
    
    # Process Jira events
    issue_key = data.get("issue", {}).get("key", "")
    
    # In a real implementation, update knowledge graph with Jira issue data
    
    return {
        "event_type": event_type,
        "issue_key": issue_key,
        "action": "acknowledged"
    }

# Run the webhook server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("WEBHOOK_SERVER_PORT", 5001))
    logger.info(f"Starting Webhook Server on port {port}")
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port, reload=True)
