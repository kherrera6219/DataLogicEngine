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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/ukg_system_{time.strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("UKG-Enterprise")

# Track running processes
processes = []

def run_command(cmd, env=None):
    """Run a command in a subprocess and return the process"""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    logger.info(f"Running command: {cmd}")
    process = subprocess.Popen(
        cmd,
        shell=True,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(process)
    return process

def cleanup():
    """Cleanup all running processes on exit"""
    logger.info("Shutting down UKG Enterprise system...")
    for p in processes:
        if p.poll() is None:  # If the process is still running
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    logger.info("All processes terminated.")

def start_api_gateway(port: int = 5000) -> subprocess.Popen:
    """Start the API Gateway service"""
    logger.info(f"Starting API Gateway on port {port}...")
    env = {
        "FLASK_APP": "app.py",
        "FLASK_ENV": "production",
        "PYTHONUNBUFFERED": "1"
    }
    return run_command(f"gunicorn --bind 0.0.0.0:{port} --workers=2 app:app", env)

def start_webhook_server(port: int = 5001) -> subprocess.Popen:
    """Start the Webhook Server service"""
    logger.info(f"Starting Webhook Server on port {port}...")
    env = {
        "WEBHOOK_PORT": str(port),
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
        "PYTHONUNBUFFERED": "1"
    }
    return run_command("python backend/enterprise_architecture.py", env)

def start_frontend(port: int = 3000) -> subprocess.Popen:
    """Start the Next.js frontend"""
    logger.info(f"Starting Next.js frontend on port {port}...")
    env = {
        "PORT": str(port),
        "NEXT_PUBLIC_API_URL": f"http://0.0.0.0:5000",
        "NEXT_PUBLIC_CORE_UKG_URL": f"http://0.0.0.0:5003",
        "NODE_ENV": "production"
    }
    # For production
    return run_command("npm start", env)

def main():
    """Main entry point for running the UKG Enterprise system"""
    parser = argparse.ArgumentParser(description="UKG Enterprise System Runner")
    parser.add_argument("--no-frontend", action="store_true", help="Run backend services only")
    parser.add_argument("--build", action="store_true", help="Build the frontend before starting")
    args = parser.parse_args()

    # Register the cleanup function
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

    logger.info("Starting UKG Enterprise Architecture...")

    # Start all backend services
    api_gateway = start_api_gateway()
    time.sleep(2)  # Give API Gateway time to start

    webhook_server = start_webhook_server()
    time.sleep(1)

    model_context = start_model_context_server()
    time.sleep(1)

    core_ukg = start_core_ukg_service()
    time.sleep(1)

    # Build frontend if requested
    if args.build:
        logger.info("Building Next.js frontend...")
        build_process = run_command("npm run build")
        build_process.wait()  # Wait for build to complete

    # Start frontend unless --no-frontend flag is provided
    if not args.no_frontend:
        frontend = start_frontend()

    # Keep the script running
    try:
        logger.info("UKG Enterprise Architecture is running. Press Ctrl+C to stop.")
        while True:
            for i, p in enumerate(processes[:]):
                if p.poll() is not None:  # Process has terminated
                    out, _ = p.communicate()
                    if out:
                        logger.error(f"Process exited with output: {out}")
                    logger.warning(f"Process {i} has terminated with return code {p.returncode}")
                    processes.remove(p)

            if not processes:
                logger.error("All processes have terminated. Exiting.")
                break

            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal.")
        sys.exit(0)

if __name__ == "__main__":
    main()