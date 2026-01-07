"""
Universal Knowledge Graph (UKG) System - Run Script

This script provides a custom way to run the UKG system on port 8080
to avoid conflicts with port 3000 on the Replit platform.
"""

import os
import sys
import subprocess
import signal
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UKG-Runner")

# Process management
running_processes = []

def cleanup(signum=None, frame=None):
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

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_command(command, env=None):
    """Run a command as a subprocess"""
    try:
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)
            
        logger.info(f"Running command: {command}")
        process = subprocess.Popen(
            command,
            env=env_vars,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        running_processes.append(process)
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                
        return process.poll()
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return 1

def initialize_database():
    """Initialize the database with required tables"""
    logger.info("Initializing database...")
    
    # Create database tables
    from app import app, db
    import db_models  # Make sure db_models is imported
    
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

def start_backend():
    """Start the Flask backend on port 8080"""
    logger.info("Starting Flask backend on port 8080...")
    
    # First initialize the database
    initialize_database()
    
    # Set environment variables
    env = {
        "PORT": "8080",
        "FLASK_APP": "wsgi.py",
        "FLASK_ENV": "development",
        "PYTHONUNBUFFERED": "1"
    }
    
    # Start the backend using gunicorn
    return run_command("gunicorn --bind 0.0.0.0:8080 --reuse-port --reload wsgi:app", env)

if __name__ == "__main__":
    try:
        logger.info("Starting Universal Knowledge Graph system...")
        
        # Run the backend
        exit_code = start_backend()
        
        if exit_code != 0:
            logger.error(f"Backend exited with code {exit_code}")
            sys.exit(exit_code)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        cleanup()
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        cleanup()
        sys.exit(1)