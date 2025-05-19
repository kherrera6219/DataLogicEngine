
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) Enterprise Services Runner

This script starts all the enterprise services for the UKG system.
"""

import os
import sys
import subprocess
import time
import signal
import logging
import argparse
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UKG-Enterprise")

# Process management
running_processes: List[subprocess.Popen] = []

def cleanup(signum=None, frame=None) -> None:
    """Clean up any running processes"""
    logger.info("Cleaning up processes...")
    for process in running_processes:
        if process.poll() is None:  # Process is still running
            logger.info(f"Terminating process PID: {process.pid}")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    logger.info("Cleanup complete")
    sys.exit(0)

def run_command(command: str, env: Dict[str, str] = None) -> subprocess.Popen:
    """Run a command in a subprocess"""
    logger.info(f"Running command: {command}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    process = subprocess.Popen(
        command,
        shell=True,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    running_processes.append(process)
    return process

def run_api_gateway() -> subprocess.Popen:
    """Start the API Gateway"""
    logger.info("Starting API Gateway on port 5000...")
    env = {
        "API_GATEWAY_PORT": "5000",
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/api_gateway/api_gateway.py", env)

def run_webhook_server() -> subprocess.Popen:
    """Start the Webhook Server"""
    logger.info("Starting Webhook Server on port 5001...")
    env = {
        "WEBHOOK_SERVER_PORT": "5001",
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/webhook_server/webhook_server.py", env)

def run_model_context_server() -> subprocess.Popen:
    """Start the Model Context Protocol Server"""
    logger.info("Starting Model Context Protocol Server on port 5002...")
    env = {
        "MODEL_CONTEXT_PORT": "5002",
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/model_context/model_context_server.py", env)

def run_dotnet_service() -> subprocess.Popen:
    """Start the .NET Core Service"""
    logger.info("Starting .NET Core Service on port 5005...")
    env = {
        "DOTNET_PORT": "5005",
        "ASPNETCORE_ENVIRONMENT": "Development"
    }
    
    # Check if dotnet is installed
    try:
        subprocess.run(["dotnet", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(".NET SDK not found - skipping .NET service start")
        return None
    
    return run_command("dotnet run --project backend/dotnet_service", env)

def start_all_services() -> None:
    """Start all enterprise services"""
    logger.info("Starting all UKG Enterprise services...")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Start API Gateway
    api_gateway = run_api_gateway()
    
    # Start Webhook Server
    webhook_server = run_webhook_server()
    
    # Start Model Context Protocol Server
    model_context_server = run_model_context_server()
    
    # Start .NET Core Service
    dotnet_service = run_dotnet_service()
    
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
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="UKG Enterprise Services Runner")
        parser.add_argument("--gateway-only", action="store_true", help="Start only the API Gateway")
        parser.add_argument("--webhook-only", action="store_true", help="Start only the Webhook Server")
        parser.add_argument("--model-context-only", action="store_true", help="Start only the Model Context Server")
        parser.add_argument("--dotnet-only", action="store_true", help="Start only the .NET Core Service")
        args = parser.parse_args()
        
        if args.gateway_only:
            run_api_gateway().wait()
        elif args.webhook_only:
            run_webhook_server().wait()
        elif args.model_context_only:
            run_model_context_server().wait()
        elif args.dotnet_only:
            run_dotnet_service().wait()
        else:
            start_all_services()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup()
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        cleanup()
        sys.exit(1)
