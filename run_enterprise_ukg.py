
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) Enterprise Architecture Runner

This script orchestrates the startup of all UKG enterprise components in the correct order,
with proper dependency management and health checks.
"""

import subprocess
import os
import sys
import logging
import argparse
import time
import signal
import atexit
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/ukg_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("UKG-Enterprise")

# Import config manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from backend.config_manager import get_config
    config = get_config()
except ImportError:
    logger.error("Failed to import config_manager. Make sure it exists.")
    sys.exit(1)

# Track running processes
processes = []

def run_command(cmd, env=None, cwd=None, name=None):
    """Run a command in a subprocess and return the process"""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    logger.info(f"Running command: {cmd}")
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=cwd
        )
        processes.append((process, name or cmd))
        return process
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        return None

def cleanup():
    """Cleanup all running processes on exit"""
    logger.info("Shutting down UKG Enterprise system...")
    for p, name in processes:
        if p.poll() is None:  # If the process is still running
            logger.info(f"Terminating process: {name}")
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing process: {name}")
                p.kill()
    logger.info("All processes terminated.")

def check_health(service_name: str, max_retries: int = 10, retry_interval: int = 1) -> bool:
    """Check if a service is healthy by making a request to its health endpoint"""
    health_url = config.get_health_check_url(service_name)
    
    for i in range(max_retries):
        try:
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                logger.info(f"Service {service_name} is healthy at {health_url}")
                return True
        except requests.RequestException:
            pass
        
        if i < max_retries - 1:
            logger.info(f"Waiting for {service_name} to become healthy (attempt {i+1}/{max_retries})...")
            time.sleep(retry_interval)
    
    logger.error(f"Service {service_name} failed health check at {health_url}")
    return False

def start_api_gateway() -> subprocess.Popen:
    """Start the API Gateway service"""
    port = config.get_port("api_gateway")
    logger.info(f"Starting API Gateway on port {port}...")
    env = {
        "FLASK_APP": "app.py",
        "FLASK_ENV": config.get("system.environment"),
        "PYTHONUNBUFFERED": "1",
        "PORT": str(port)
    }
    return run_command(f"gunicorn --bind 0.0.0.0:{port} --workers=2 app:app", env, name="api_gateway")

def start_webhook_server() -> subprocess.Popen:
    """Start the Webhook Server service"""
    port = config.get_port("webhook_server")
    logger.info(f"Starting Webhook Server on port {port}...")
    env = {
        "WEBHOOK_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/webhook_server/webhook_server.py", env, name="webhook_server")

def start_model_context_server() -> subprocess.Popen:
    """Start the Model Context Protocol Server service"""
    port = config.get_port("model_context")
    logger.info(f"Starting Model Context Protocol Server on port {port}...")
    env = {
        "MODEL_CONTEXT_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/model_context/model_context_server.py", env, name="model_context_server")

def start_core_ukg_service() -> subprocess.Popen:
    """Start the Core UKG service"""
    port = config.get_port("core_ukg")
    logger.info(f"Starting Core UKG service on port {port}...")
    env = {
        "UKG_CORE_PORT": str(port),
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/enterprise_architecture.py", env, name="core_ukg_service")

def start_frontend() -> subprocess.Popen:
    """Start the Next.js frontend"""
    port = config.get_port("frontend")
    logger.info(f"Starting Next.js frontend on port {port}...")
    env = {
        "PORT": str(port),
        "NEXT_PUBLIC_API_URL": f"http://0.0.0.0:{config.get_port('api_gateway')}",
        "NEXT_PUBLIC_CORE_UKG_URL": f"http://0.0.0.0:{config.get_port('core_ukg')}",
        "NODE_ENV": "production"
    }
    # For production
    return run_command("npm start", env, name="frontend")

def monitor_processes():
    """Monitor running processes and restart if they crash"""
    while True:
        for i, (p, name) in enumerate(processes[:]):
            if p.poll() is not None:  # Process has terminated
                out, _ = p.communicate()
                if out:
                    logger.error(f"Process {name} exited with output: {out}")
                logger.warning(f"Process {name} terminated with return code {p.returncode}")
                
                # Remove from processes list
                processes.remove((p, name))
                
                # Attempt to restart the process if it wasn't terminated intentionally
                if name == "api_gateway":
                    new_p = start_api_gateway()
                    if new_p:
                        logger.info(f"Restarted {name}")
                elif name == "webhook_server":
                    new_p = start_webhook_server()
                    if new_p:
                        logger.info(f"Restarted {name}")
                elif name == "model_context_server":
                    new_p = start_model_context_server()
                    if new_p:
                        logger.info(f"Restarted {name}")
                elif name == "core_ukg_service":
                    new_p = start_core_ukg_service()
                    if new_p:
                        logger.info(f"Restarted {name}")
                elif name == "frontend":
                    new_p = start_frontend()
                    if new_p:
                        logger.info(f"Restarted {name}")
                
        if not processes:
            logger.error("All processes have terminated. Exiting.")
            break

        time.sleep(5)

def main():
    """Main entry point for running the UKG Enterprise system"""
    parser = argparse.ArgumentParser(description="UKG Enterprise System Runner")
    parser.add_argument("--no-frontend", action="store_true", help="Run backend services only")
    parser.add_argument("--build", action="store_true", help="Build the frontend before starting")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    parser.add_argument("--secure", action="store_true", help="Enable enhanced security features")
    args = parser.parse_args()

    # Load custom config if provided
    if args.config and os.path.exists(args.config):
        config.load_from_file(args.config)

    # Register the cleanup function
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

    logger.info("Starting UKG Enterprise Architecture...")
    logger.info(f"Using configuration: {json.dumps(config.as_dict(), indent=2)}")

    # Initialize security components if requested
    if args.secure:
        logger.info("Initializing security and compliance components...")
        try:
            # Ensure security directories exist
            os.makedirs("logs/security", exist_ok=True)
            os.makedirs("logs/compliance", exist_ok=True)
            os.makedirs("logs/audit", exist_ok=True)
            os.makedirs("data/security", exist_ok=True)
            
            # Import and initialize security components
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from backend.security import get_security_manager, get_audit_logger, get_compliance_manager
            
            security_manager = get_security_manager(config)
            audit_logger = get_audit_logger(config)
            compliance_manager = get_compliance_manager(config)
            
            logger.info("Security and compliance components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize security components: {e}")
            logger.warning("Continuing without enhanced security features")
    
    # Start all backend services
    api_gateway = start_api_gateway()
    if not api_gateway:
        logger.error("Failed to start API Gateway. Exiting.")
        sys.exit(1)
    
    # Wait for API Gateway to be ready
    if not check_health("api_gateway", max_retries=10):
        logger.error("API Gateway failed to start. Exiting.")
        cleanup()
        sys.exit(1)

    # Start other services
    webhook_server = start_webhook_server()
    time.sleep(2)  # Give webhook server time to start
    check_health("webhook_server", max_retries=5)

    model_context = start_model_context_server()
    time.sleep(2)  # Give model context server time to start
    check_health("model_context", max_retries=5)

    core_ukg = start_core_ukg_service()
    time.sleep(2)  # Give core UKG service time to start
    check_health("core_ukg", max_retries=5)

    # Build frontend if requested
    if args.build:
        logger.info("Building Next.js frontend...")
        build_process = run_command("npm run build", name="frontend_build")
        build_process.wait()  # Wait for build to complete
        logger.info("Frontend build completed")

    # Start frontend unless --no-frontend flag is provided
    if not args.no_frontend:
        frontend = start_frontend()

    # Keep the script running and monitor processes
    try:
        logger.info("UKG Enterprise Architecture is running. Press Ctrl+C to stop.")
        monitor_processes()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal.")
        sys.exit(0)

if __name__ == "__main__":
    main()
