
"""
UKG API Gateway

This gateway serves as the entry point for all API requests to the UKG system,
handling routing, authentication, and request/response transformations.
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
import jwt
import os
import sys
import time
from typing import Dict, Any, Optional
from datetime import datetime
from threading import Lock
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enterprise_architecture import get_enterprise_architecture
from middleware.asgi_security import apply_standard_fastapi_middleware
from backend.logging_config import configure_service_logging
from backend.security.ssrf import SSRFProtectionError, assert_safe_outbound_url, normalize_host_tokens
from backend.utils.cors_policy import resolve_service_cors_policy

# Initialize FastAPI app
app = FastAPI(
    title="UKG Enterprise API Gateway",
    description="API Gateway for the Universal Knowledge Graph Enterprise Architecture",
    version="1.0.0"
)
apply_standard_fastapi_middleware(app, service_name="api_gateway")

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
logger = configure_service_logging("api_gateway")

# Get enterprise architecture
enterprise_arch = get_enterprise_architecture()

SERVICE_START_TIME = time.time()
REQUEST_METRICS = {"total": 0, "inflight": 0}
REQUEST_METRICS_LOCK = Lock()
UPSTREAM_REQUEST_TIMEOUT = httpx.Timeout(20.0, connect=5.0)


def _gateway_jwt_secret() -> str:
    """Return the configured gateway JWT secret or fail closed."""
    secret = (
        os.environ.get("API_GATEWAY_JWT_SECRET")
        or os.environ.get("JWT_SECRET_KEY")
        or ""
    ).strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API gateway authentication is not configured",
        )
    return secret


def _gateway_jwt_algorithms() -> list[str]:
    raw_algorithms = os.environ.get("API_GATEWAY_JWT_ALGORITHMS", "HS256")
    algorithms = [item.strip() for item in raw_algorithms.split(",") if item.strip()]
    return algorithms or ["HS256"]


def _required_gateway_roles() -> set[str]:
    raw_roles = os.environ.get("API_GATEWAY_REQUIRED_ROLES", "")
    return {role.strip() for role in raw_roles.split(",") if role.strip()}


def _token_roles(payload: Dict[str, Any]) -> set[str]:
    roles = payload.get("roles", [])
    if isinstance(roles, str):
        return {role.strip() for role in roles.split(",") if role.strip()}
    if isinstance(roles, (list, tuple, set)):
        return {str(role).strip() for role in roles if str(role).strip()}
    return set()


# Authentication dependency
async def verify_token(request: Request):
    """Verify a signed JWT bearer token for protected routes."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_parts = auth_header.split(None, 1)
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer" or not auth_parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    audience = os.environ.get("API_GATEWAY_JWT_AUDIENCE") or None
    issuer = os.environ.get("API_GATEWAY_JWT_ISSUER") or None
    decode_kwargs: dict[str, Any] = {
        "algorithms": _gateway_jwt_algorithms(),
        "options": {"require": ["exp"], "verify_aud": bool(audience)},
    }
    if audience:
        decode_kwargs["audience"] = audience
    if issuer:
        decode_kwargs["issuer"] = issuer

    try:
        payload = jwt.decode(auth_parts[1].strip(), _gateway_jwt_secret(), **decode_kwargs)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub") or payload.get("user_id") or payload.get("identity")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing a subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    required_roles = _required_gateway_roles()
    roles = _token_roles(payload)
    if required_roles and roles.isdisjoint(required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient token role",
        )

    return {"user_id": str(user_id), "roles": sorted(roles), "claims": payload}

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests through the gateway"""
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
    services_registered = len(getattr(enterprise_arch, "services", {}))
    ready = enterprise_arch is not None and services_registered > 0
    status_code = 200 if ready else 503
    return (
        {
            "status": "ready" if ready else "not_ready",
            "checks": {
                "enterprise_architecture": "ok" if enterprise_arch is not None else "error",
                "service_registry": "ok" if services_registered > 0 else "empty",
            },
            "registered_services": services_registered,
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
        "# HELP ukg_api_gateway_uptime_seconds Process uptime in seconds.",
        "# TYPE ukg_api_gateway_uptime_seconds gauge",
        f"ukg_api_gateway_uptime_seconds {uptime_seconds:.3f}",
        "# HELP ukg_api_gateway_http_requests_total Total HTTP requests handled.",
        "# TYPE ukg_api_gateway_http_requests_total counter",
        f"ukg_api_gateway_http_requests_total {total_requests}",
        "# HELP ukg_api_gateway_http_requests_inflight Current in-flight requests.",
        "# TYPE ukg_api_gateway_http_requests_inflight gauge",
        f"ukg_api_gateway_http_requests_inflight {inflight_requests}",
        "# HELP ukg_api_gateway_ready Ready status (1=ready, 0=not ready).",
        "# TYPE ukg_api_gateway_ready gauge",
        f"ukg_api_gateway_ready {ready}",
        "# HELP ukg_api_gateway_registered_services Number of registered services.",
        "# TYPE ukg_api_gateway_registered_services gauge",
        f"ukg_api_gateway_registered_services {readiness['registered_services']}",
    ]
    return "\n".join(lines) + "\n"


def _upstream_allowlist_hosts() -> set[str]:
    hosts = set()
    for service in getattr(enterprise_arch, "services", {}).values():
        parsed = urlparse(service.endpoint)
        if parsed.hostname:
            hosts.add(parsed.hostname.lower().rstrip("."))
    hosts.update(normalize_host_tokens(os.environ.get("API_GATEWAY_UPSTREAM_ALLOWLIST")))
    return hosts


def _resolve_upstream_url(service_name: str, path: str) -> str:
    service = enterprise_arch.get_service(service_name)
    if not service:
        raise HTTPException(status_code=503, detail=f"{service_name} service not available")

    target_url = f"{service.endpoint.rstrip('/')}/{path.lstrip('/')}"
    try:
        assert_safe_outbound_url(
            target_url,
            allowed_hosts=_upstream_allowlist_hosts(),
            allow_private_hosts=True,
        )
    except SSRFProtectionError as exc:
        logger.error("Blocked upstream request for %s (%s): %s", service_name, target_url, exc)
        raise HTTPException(status_code=502, detail="Blocked upstream endpoint by SSRF policy") from exc
    return target_url


async def _forward_json_request(
    *,
    method: str,
    service_name: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:
    url = _resolve_upstream_url(service_name, path)
    async with httpx.AsyncClient(timeout=UPSTREAM_REQUEST_TIMEOUT, follow_redirects=False) as client:
        try:
            response = await client.request(method.upper(), url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Upstream HTTP error from %s: status=%s path=%s",
                service_name,
                exc.response.status_code,
                path,
            )
            raise HTTPException(status_code=exc.response.status_code, detail="Upstream service error") from exc
        except httpx.HTTPError as exc:
            logger.error("Upstream request failure for %s (%s): %s", service_name, path, exc)
            raise HTTPException(status_code=503, detail="Upstream service unavailable") from exc


@app.get("/live")
async def live_check():
    """Liveness probe endpoint."""
    return {
        "status": "live",
        "service": "UKG API Gateway",
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
    """Health check endpoint for the API Gateway"""
    readiness, readiness_code = _readiness_status()
    return {
        "status": "healthy" if readiness_code == 200 else "degraded",
        "service": "UKG API Gateway",
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

# Enterprise architecture status
@app.get("/architecture/status")
async def architecture_status():
    """Get the status of the entire enterprise architecture"""
    return enterprise_arch.get_architecture_status()

# Service health checks
@app.get("/architecture/health")
async def architecture_health():
    """Run health checks on all services"""
    health_results = await enterprise_arch.health_check_all()
    return {
        "status": "completed",
        "results": health_results,
        "timestamp": datetime.now().isoformat()
    }

# UKG API routes
@app.get("/api/v1/graph/stats")
async def get_graph_stats(user = Depends(verify_token)):
    """Get statistics about the knowledge graph"""
    return await _forward_json_request(
        method="GET",
        service_name="core_ukg",
        path="/api/v1/graph/stats",
    )

@app.post("/api/v1/query")
async def process_query(request: Request, user = Depends(verify_token)):
    """Process a query through the UKG system"""
    body = await request.json()
    return await _forward_json_request(
        method="POST",
        service_name="core_ukg",
        path="/api/v1/query",
        payload=body,
    )

# Model context API routes
@app.post("/api/model/context")
async def create_model_context(request: Request, user = Depends(verify_token)):
    """Create a new model context"""
    body = await request.json()
    return await _forward_json_request(
        method="POST",
        service_name="model_context_server",
        path="/context",
        payload=body,
    )

# Webhook API routes
@app.post("/api/webhooks/{integration_name}")
async def process_webhook(integration_name: str, request: Request):
    """Process incoming webhooks"""
    body = await request.json()
    return await _forward_json_request(
        method="POST",
        service_name="webhook_server",
        path=f"/webhooks/{integration_name}",
        payload=body,
    )

# .NET service integration example
@app.get("/api/dotnet/resources")
async def get_dotnet_resources(user = Depends(verify_token)):
    """Get resources from the .NET service"""
    return await _forward_json_request(
        method="GET",
        service_name="dotnet_service",
        path="/api/resources",
    )

# Default 404 handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": f"API endpoint not found: {request.url.path}",
            "timestamp": datetime.now().isoformat()
        }
    )

# Run the API gateway
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("API_GATEWAY_PORT", 5000))
    host = os.environ.get("API_GATEWAY_HOST", os.environ.get("SERVICE_BIND_HOST", "127.0.0.1"))
    logger.info(f"Starting API Gateway on port {port}")
    uvicorn.run("api_gateway:app", host=host, port=port, reload=True)
