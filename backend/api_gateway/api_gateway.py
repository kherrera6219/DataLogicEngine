
"""
UKG API Gateway

This gateway serves as the entry point for all API requests to the UKG system,
handling routing, authentication, and request/response transformations.
"""

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import sys
import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enterprise_architecture import get_enterprise_architecture

# Initialize FastAPI app
app = FastAPI(
    title="UKG Enterprise API Gateway",
    description="API Gateway for the Universal Knowledge Graph Enterprise Architecture",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("API-Gateway")

# Get enterprise architecture
enterprise_arch = get_enterprise_architecture()

# Authentication middleware
async def verify_token(request: Request):
    """Verify JWT token for protected routes"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token
    token = auth_header.split(" ")[1]
    
    # In a real implementation, validate the JWT token
    # For now, we'll accept any token for demonstration
    
    # Return user info extracted from token
    return {"user_id": "demo_user", "roles": ["user"]}

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests through the gateway"""
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
    """Health check endpoint for the API Gateway"""
    return {
        "status": "healthy",
        "service": "UKG API Gateway",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

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
    async with httpx.AsyncClient() as client:
        # Forward request to the Core UKG API
        response = await client.get(f"{enterprise_arch.get_service('api_gateway').endpoint}/api/v1/graph/stats")
        return response.json()

@app.post("/api/v1/query")
async def process_query(request: Request, user = Depends(verify_token)):
    """Process a query through the UKG system"""
    # Get request body
    body = await request.json()
    
    # Forward to appropriate UKG service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{enterprise_arch.get_service('api_gateway').endpoint}/api/v1/query",
            json=body
        )
        return response.json()

# Model context API routes
@app.post("/api/model/context")
async def create_model_context(request: Request, user = Depends(verify_token)):
    """Create a new model context"""
    body = await request.json()
    
    # Forward to Model Context Protocol Server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{enterprise_arch.get_service('model_context_server').endpoint}/context",
            json=body
        )
        return response.json()

# Webhook API routes
@app.post("/api/webhooks/{integration_name}")
async def process_webhook(integration_name: str, request: Request):
    """Process incoming webhooks"""
    body = await request.json()
    
    # Forward to Webhook Server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{enterprise_arch.get_service('webhook_server').endpoint}/webhooks/{integration_name}",
            json=body
        )
        return response.json()

# .NET service integration example
@app.get("/api/dotnet/resources")
async def get_dotnet_resources(user = Depends(verify_token)):
    """Get resources from the .NET service"""
    # Forward to .NET Core Service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{enterprise_arch.get_service('dotnet_core_service').endpoint}/api/resources"
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error communicating with .NET service: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False, 
                    "message": "Service unavailable",
                    "error": str(e)
                }
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
    logger.info(f"Starting API Gateway on port {port}")
    uvicorn.run("api_gateway:app", host="0.0.0.0", port=port, reload=True)
