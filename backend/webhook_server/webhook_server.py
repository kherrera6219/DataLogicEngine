
"""
UKG Webhook Server

This server handles incoming webhooks from external services and integrations,
processing events and triggering appropriate actions in the UKG system.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import os
import sys
import time
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime
from threading import Lock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enterprise_architecture import get_enterprise_architecture
from middleware.asgi_security import apply_standard_fastapi_middleware
from backend.logging_config import configure_service_logging
from backend.utils.cors_policy import resolve_service_cors_policy

# Initialize FastAPI app
app = FastAPI(
    title="UKG Webhook Server",
    description="Webhook Server for the Universal Knowledge Graph Enterprise Architecture",
    version="1.0.0"
)
apply_standard_fastapi_middleware(app, service_name="webhook_server")

cors_origins, cors_allow_credentials = resolve_service_cors_policy()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logger = configure_service_logging("webhook_server")

# Get enterprise architecture
enterprise_arch = get_enterprise_architecture()

SERVICE_START_TIME = time.time()
REQUEST_METRICS = {"total": 0, "inflight": 0}
REQUEST_METRICS_LOCK = Lock()

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
    with REQUEST_METRICS_LOCK:
        REQUEST_METRICS["total"] += 1
        REQUEST_METRICS["inflight"] += 1

    response = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        process_time = time.time() - start_time
        with REQUEST_METRICS_LOCK:
            REQUEST_METRICS["inflight"] = max(0, REQUEST_METRICS["inflight"] - 1)
        logger.info(
            "Method: %s Path: %s Status: %s Time: %.4fs",
            request.method,
            request.url.path,
            status_code,
            process_time,
        )


def _readiness_status() -> tuple[dict, int]:
    """Compute webhook server readiness state."""
    ready = bool(webhook_processors)
    status_code = 200 if ready else 503
    return (
        {
            "status": "ready" if ready else "not_ready",
            "checks": {
                "processor_registry": "ok" if ready else "empty",
            },
            "registered_processors": len(webhook_processors),
            "timestamp": datetime.now().isoformat(),
        },
        status_code,
    )


def _metrics_payload() -> str:
    uptime_seconds = max(0.0, time.time() - SERVICE_START_TIME)
    with REQUEST_METRICS_LOCK:
        total_requests = REQUEST_METRICS["total"]
        inflight_requests = REQUEST_METRICS["inflight"]
    readiness, readiness_code = _readiness_status()
    ready = 1 if readiness_code == 200 else 0

    lines = [
        "# HELP ukg_webhook_server_uptime_seconds Process uptime in seconds.",
        "# TYPE ukg_webhook_server_uptime_seconds gauge",
        f"ukg_webhook_server_uptime_seconds {uptime_seconds:.3f}",
        "# HELP ukg_webhook_server_http_requests_total Total HTTP requests handled.",
        "# TYPE ukg_webhook_server_http_requests_total counter",
        f"ukg_webhook_server_http_requests_total {total_requests}",
        "# HELP ukg_webhook_server_http_requests_inflight Current in-flight requests.",
        "# TYPE ukg_webhook_server_http_requests_inflight gauge",
        f"ukg_webhook_server_http_requests_inflight {inflight_requests}",
        "# HELP ukg_webhook_server_ready Ready status (1=ready, 0=not ready).",
        "# TYPE ukg_webhook_server_ready gauge",
        f"ukg_webhook_server_ready {ready}",
        "# HELP ukg_webhook_processors_registered Number of registered processors.",
        "# TYPE ukg_webhook_processors_registered gauge",
        f"ukg_webhook_processors_registered {readiness['registered_processors']}",
    ]
    return "\n".join(lines) + "\n"


@app.get("/live")
async def live_check():
    """Liveness probe endpoint."""
    return {
        "status": "live",
        "service": "UKG Webhook Server",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/ready")
async def ready_check():
    """Readiness probe endpoint."""
    payload, status_code = _readiness_status()
    return JSONResponse(status_code=status_code, content=payload)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the Webhook Server"""
    readiness, readiness_code = _readiness_status()
    return {
        "status": "healthy" if readiness_code == 200 else "degraded",
        "service": "UKG Webhook Server",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "ready": readiness["status"],
    }


@app.get("/metrics")
async def metrics():
    """Canonical metrics endpoint for scraping."""
    return PlainTextResponse(
        _metrics_payload(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

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
                "error": "Request body is not valid JSON",
                "code": "WEBHOOK_INVALID_JSON",
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
                "error": "Webhook processor failed",
                "code": "WEBHOOK_PROCESSING_ERROR",
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
    host = os.environ.get("WEBHOOK_SERVER_HOST", os.environ.get("SERVICE_BIND_HOST", "127.0.0.1"))
    logger.info(f"Starting Webhook Server on port {port}")
    uvicorn.run("webhook_server:app", host=host, port=port, reload=True)
