
"""
UKG Model Context Protocol Server

This server manages model context for AI interactions, handles 
context window optimization, and provides a unified interface for
model inference across the UKG system.
"""

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import sys
import logging
import time
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from enterprise_architecture import get_enterprise_architecture

# Initialize FastAPI app
app = FastAPI(
    title="UKG Model Context Protocol Server",
    description="Model Context Protocol Server for the Universal Knowledge Graph Enterprise Architecture",
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
logger = logging.getLogger("Model-Context-Server")

# Get enterprise architecture
enterprise_arch = get_enterprise_architecture()

# Security
security = HTTPBearer()

# Pydantic models for API requests/responses
class ContextCreateRequest(BaseModel):
    """Request to create a new context"""
    name: str
    description: Optional[str] = None
    context_type: str = Field(..., description="Type of context (e.g., 'conversation', 'document', 'simulation')")
    initial_data: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 4096
    metadata: Optional[Dict[str, Any]] = None

class ContextUpdateRequest(BaseModel):
    """Request to update an existing context"""
    context_id: str
    data: Dict[str, Any]
    append: bool = True

class ContextData(BaseModel):
    """Context data model"""
    context_id: str
    name: str
    description: Optional[str] = None
    context_type: str
    created_at: datetime
    updated_at: datetime
    token_count: int
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ModelInferenceRequest(BaseModel):
    """Request for model inference"""
    context_id: str
    model_name: str
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    parameters: Optional[Dict[str, Any]] = None

class ModelInferenceResponse(BaseModel):
    """Response from model inference"""
    context_id: str
    model_name: str
    generated_text: str
    tokens_used: int
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None

# In-memory context storage
# In a production system, this would use a database
contexts = {}

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests through the model context server"""
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

# Authentication middleware
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token"""
    # In a real implementation, validate the token
    # For demonstration, we'll accept any token
    return {"token": credentials.credentials}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the Model Context Protocol Server"""
    return {
        "status": "healthy",
        "service": "UKG Model Context Protocol Server",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Context management endpoints
@app.post("/context", response_model=ContextData)
async def create_context(
    request: ContextCreateRequest,
    auth = Depends(verify_token)
):
    """Create a new model context"""
    context_id = f"ctx_{int(time.time())}_{os.urandom(4).hex()}"
    
    # Calculate token count (simplified)
    token_count = 0
    if request.initial_data:
        # Simplified token counting - in reality use a tokenizer
        token_count = len(json.dumps(request.initial_data)) // 4
    
    # Create context
    context = {
        "context_id": context_id,
        "name": request.name,
        "description": request.description,
        "context_type": request.context_type,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "token_count": token_count,
        "data": request.initial_data or {},
        "metadata": request.metadata or {}
    }
    
    # Store context
    contexts[context_id] = context
    
    logger.info(f"Created context: {context_id}")
    return context

@app.get("/context/{context_id}", response_model=ContextData)
async def get_context(
    context_id: str,
    auth = Depends(verify_token)
):
    """Get an existing context"""
    if context_id not in contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    
    return contexts[context_id]

@app.put("/context/{context_id}", response_model=ContextData)
async def update_context(
    context_id: str,
    request: ContextUpdateRequest,
    auth = Depends(verify_token)
):
    """Update an existing context"""
    if context_id not in contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    
    context = contexts[context_id]
    
    # Update context data
    if request.append:
        # Append to existing data
        for key, value in request.data.items():
            if key in context["data"] and isinstance(context["data"][key], list) and isinstance(value, list):
                context["data"][key].extend(value)
            elif key in context["data"] and isinstance(context["data"][key], dict) and isinstance(value, dict):
                context["data"][key].update(value)
            else:
                context["data"][key] = value
    else:
        # Replace existing data
        context["data"] = request.data
    
    # Update metadata
    context["updated_at"] = datetime.now()
    
    # Recalculate token count (simplified)
    context["token_count"] = len(json.dumps(context["data"])) // 4
    
    logger.info(f"Updated context: {context_id}")
    return context

@app.delete("/context/{context_id}")
async def delete_context(
    context_id: str,
    auth = Depends(verify_token)
):
    """Delete an existing context"""
    if context_id not in contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    
    # Delete context
    del contexts[context_id]
    
    logger.info(f"Deleted context: {context_id}")
    return {"success": True, "message": f"Context {context_id} deleted"}

# Model inference endpoints
@app.post("/inference", response_model=ModelInferenceResponse)
async def run_model_inference(
    request: ModelInferenceRequest,
    auth = Depends(verify_token)
):
    """Run model inference using the provided context"""
    if request.context_id not in contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {request.context_id}")
    
    context = contexts[request.context_id]
    
    # Start timing
    start_time = time.time()
    
    # For demonstration, we'll generate a simple response
    # In a real implementation, this would call an actual LLM API
    generated_text = f"This is a simulated response for context {request.context_id} using model {request.model_name}.\n"
    generated_text += f"The context type is '{context['context_type']}' and contains {context['token_count']} tokens.\n"
    generated_text += f"Based on the prompt: '{request.prompt}'"
    
    # Calculate tokens (simplified)
    tokens_used = len(generated_text) // 4
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    logger.info(f"Ran inference for context {request.context_id} using model {request.model_name}")
    
    return {
        "context_id": request.context_id,
        "model_name": request.model_name,
        "generated_text": generated_text,
        "tokens_used": tokens_used,
        "processing_time": processing_time,
        "metadata": {
            "input_tokens": len(request.prompt) // 4,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/models")
async def list_available_models(
    auth = Depends(verify_token)
):
    """List available models for inference"""
    # In a real implementation, this would query available models
    # from the model provider or local deployment
    models = [
        {
            "name": "ukg-gpt-4",
            "description": "UKG GPT-4 model for general-purpose inference",
            "context_window": 8192,
            "input_format": "text",
            "metadata": {"provider": "internal"}
        },
        {
            "name": "ukg-expert-model",
            "description": "Specialized UKG model for expert domains",
            "context_window": 4096,
            "input_format": "text",
            "metadata": {"provider": "internal"}
        },
        {
            "name": "openai-gpt-4",
            "description": "OpenAI GPT-4 integration",
            "context_window": 8192,
            "input_format": "text",
            "metadata": {"provider": "openai"}
        }
    ]
    
    return {
        "models": models,
        "count": len(models),
        "timestamp": datetime.now().isoformat()
    }

# Context window optimization endpoint
@app.post("/context/{context_id}/optimize")
async def optimize_context_window(
    context_id: str,
    auth = Depends(verify_token)
):
    """Optimize the context window for a given context"""
    if context_id not in contexts:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    
    context = contexts[context_id]
    
    # In a real implementation, this would apply various optimization techniques:
    # - Summarize historical parts of the context
    # - Remove redundant information
    # - Apply compression algorithms
    # - Prioritize recent or important information
    
    # For demonstration, we'll return a simplified response
    original_token_count = context["token_count"]
    
    # Simulate optimization
    context["metadata"]["optimized"] = True
    context["metadata"]["last_optimized"] = datetime.now().isoformat()
    
    # Simulate token reduction
    new_token_count = max(original_token_count // 2, 100)
    context["token_count"] = new_token_count
    
    logger.info(f"Optimized context {context_id}: {original_token_count} → {new_token_count} tokens")
    
    return {
        "context_id": context_id,
        "original_token_count": original_token_count,
        "new_token_count": new_token_count,
        "reduction_percentage": round((1 - (new_token_count / original_token_count)) * 100, 2),
        "timestamp": datetime.now().isoformat()
    }

# Run the model context protocol server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("MODEL_CONTEXT_PORT", 5002))
    logger.info(f"Starting Model Context Protocol Server on port {port}")
    uvicorn.run("model_context_server:app", host="0.0.0.0", port=port, reload=True)
