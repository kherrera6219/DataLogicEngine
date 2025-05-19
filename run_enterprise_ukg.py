
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) Enterprise Architecture Runner

This script orchestrates the startup of all UKG enterprise components in the correct order,
with proper dependency management and health checks.
"""

import os
import sys
import subprocess
import logging
import argparse
import time
import signal
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/enterprise_ukg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("UKG-Enterprise-Runner")

# Process management
running_processes = []

def cleanup(signum=None, frame=None) -> None:
    """Clean up running processes on shutdown"""
    logger.info("🛑 Shutting down UKG Enterprise Architecture...")
    for process in running_processes:
        if process.poll() is None:  # Process is still running
            logger.info(f"Terminating process PID: {process.pid}")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} didn't terminate gracefully, killing it")
                process.kill()
    logger.info("Cleanup complete")
    sys.exit(0)

def run_command(command: str, env: Dict[str, str] = None, working_dir: str = None) -> subprocess.Popen:
    """Run a command in a subprocess"""
    logger.info(f"Running command: {command}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    process = subprocess.Popen(
        command,
        shell=True,
        env=merged_env,
        cwd=working_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    running_processes.append(process)
    return process

def ensure_directories():
    """Ensure required directories exist"""
    directories = ["logs", "data"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def start_api_gateway(port: int = 5000) -> subprocess.Popen:
    """Start the API Gateway service"""
    logger.info(f"Starting API Gateway on port {port}...")
    env = {
        "API_GATEWAY_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/api_gateway/api_gateway.py", env)

def start_webhook_server(port: int = 5001) -> subprocess.Popen:
    """Start the Webhook Server service"""
    logger.info(f"Starting Webhook Server on port {port}...")
    env = {
        "WEBHOOK_SERVER_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/webhook_server/webhook_server.py", env)

def start_model_context_server(port: int = 5002) -> subprocess.Popen:
    """Start the Model Context Protocol Server service"""
    logger.info(f"Starting Model Context Protocol Server on port {port}...")
    env = {
        "MODEL_CONTEXT_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/model_context/model_context_server.py", env)

def start_core_ukg_service(port: int = 5003) -> subprocess.Popen:
    """Start the Core UKG service"""
    logger.info(f"Starting Core UKG service on port {port}...")
    env = {
        "UKG_CORE_PORT": str(port),
        "FLASK_APP": "app.py",
        "FLASK_ENV": "production",
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("gunicorn --bind 0.0.0.0:5003 --workers=2 app:app", env)

def start_frontend(port: int = 3000) -> subprocess.Popen:
    """Start the Next.js frontend"""
    logger.info(f"Starting Next.js frontend on port {port}...")
    env = {
        "PORT": str(port),
        "NEXT_PUBLIC_API_URL": f"http://0.0.0.0:5000",
        "NEXT_PUBLIC_CORE_UKG_URL": f"http://0.0.0.0:5003",
        "NODE_ENV": "production"
    }
    if os.path.exists("package.json"):
        # For production
        return run_command("npm start", env)
    else:
        logger.warning("No package.json found, skipping frontend start")
        return None

def check_health(url: str, max_attempts: int = 10, delay: int = 2) -> bool:
    """Check if a service is healthy by making a request to its health endpoint"""
    import requests
    from requests.exceptions import RequestException
    
    logger.info(f"Checking health of service at {url}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Service at {url} is healthy")
                return True
            logger.warning(f"Service at {url} returned status code {response.status_code}")
        except RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{max_attempts}: Error connecting to {url}: {str(e)}")
        
        if attempt < max_attempts - 1:
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    logger.error(f"Service at {url} failed health check after {max_attempts} attempts")
    return False

def start_enterprise_architecture(dotnet: bool = False, frontend: bool = True) -> None:
    """Start the complete UKG Enterprise Architecture"""
    logger.info("Starting UKG Enterprise Architecture...")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start API Gateway (port 5000)
    api_gateway = start_api_gateway()
    time.sleep(2)  # Give the gateway time to start
    
    # Start Webhook Server (port 5001)
    webhook_server = start_webhook_server()
    time.sleep(1)
    
    # Start Model Context Protocol Server (port 5002)
    model_context_server = start_model_context_server()
    time.sleep(1)
    
    # Start Core UKG Service (port 5003)
    core_ukg = start_core_ukg_service()
    time.sleep(1)
    
    # Start Next.js Frontend (port 3000)
    if frontend:
        frontend_process = start_frontend()
    
    # Start .NET Service (port 5005) if requested
    if dotnet:
        try:
            dotnet_check = subprocess.run(["dotnet", "--version"], capture_output=True, check=False)
            if dotnet_check.returncode == 0:
                logger.info("Starting .NET Core Service on port 5005...")
                env = {
                    "DOTNET_PORT": "5005",
                    "ASPNETCORE_ENVIRONMENT": "Development"
                }
                dotnet_service = run_command("dotnet run --project backend/dotnet_service", env)
            else:
                logger.warning(".NET SDK not found - skipping .NET service start")
        except Exception as e:
            logger.warning(f"Error starting .NET service: {str(e)}")
    
    # Check health of services
    health_checks = [
        ("API Gateway", "http://0.0.0.0:5000/health"),
        ("Webhook Server", "http://0.0.0.0:5001/health"),
        ("Model Context Server", "http://0.0.0.0:5002/health"),
        ("Core UKG Service", "http://0.0.0.0:5003/health")
    ]
    
    for service_name, url in health_checks:
        check_health(url)
    
    print("\n" + "=" * 80)
    print("🚀 UKG Enterprise Architecture is now running!")
    print("=" * 80)
    print("API Gateway:           http://0.0.0.0:5000")
    print("Webhook Server:        http://0.0.0.0:5001")
    print("Model Context Server:  http://0.0.0.0:5002")
    print("Core UKG Service:      http://0.0.0.0:5003")
    if frontend:
        print("Frontend:             http://0.0.0.0:3000")
    if dotnet:
        print(".NET Service:         http://0.0.0.0:5005")
    print("=" * 80 + "\n")
    
    # Wait for all processes to complete
    try:
        # Monitor and log output from processes
        while True:
            for process in running_processes:
                if process.poll() is not None:
                    logger.error(f"Process exited with code {process.returncode}")
                    cleanup()
                
                # Read output
                output = process.stdout.readline()
                if output:
                    print(output.rstrip())
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UKG Enterprise Architecture Runner")
    parser.add_argument("--gateway-only", action="store_true", help="Start only the API Gateway")
    parser.add_argument("--webhook-only", action="store_true", help="Start only the Webhook Server")
    parser.add_argument("--model-context-only", action="store_true", help="Start only the Model Context Server")
    parser.add_argument("--core-only", action="store_true", help="Start only the Core UKG Service")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the Next.js frontend")
    parser.add_argument("--with-dotnet", action="store_true", help="Include .NET Core Service")
    parser.add_argument("--no-frontend", action="store_true", help="Don't start the frontend")
    args = parser.parse_args()
    
    try:
        if args.gateway_only:
            start_api_gateway().wait()
        elif args.webhook_only:
            start_webhook_server().wait()
        elif args.model_context_only:
            start_model_context_server().wait()
        elif args.core_only:
            start_core_ukg_service().wait()
        elif args.frontend_only:
            start_frontend().wait()
        else:
            start_enterprise_architecture(
                dotnet=args.with_dotnet,
                frontend=not args.no_frontend
            )
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        cleanup()
        sys.exit(1)
