"""
Universal Knowledge Graph (UKG) System - Deployment Tool

This script handles deployment tasks for the UKG system
following Microsoft enterprise deployment standards.
"""

import os
import sys
import argparse
import logging
import subprocess
import datetime
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment.log")
    ]
)
logger = logging.getLogger("UKG-Deployment")

# Load environment variables
load_dotenv()

def check_prerequisites():
    """Check that all prerequisites are installed."""
    logger.info("Checking deployment prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8+ is required. Current version: %s.%s.%s", 
                     python_version.major, python_version.minor, python_version.micro)
        return False
    
    # Check required environment variables
    required_env_vars = [
        "FLASK_ENV",
        "DATABASE_URL",
        "SECRET_KEY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error("Missing required environment variables: %s", ", ".join(missing_vars))
        return False
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed")
        return False
    
    # Check Azure integration if in production
    if os.environ.get("FLASK_ENV") == "production":
        azure_vars = [
            "AZURE_AD_TENANT_ID",
            "AZURE_AD_CLIENT_ID",
            "AZURE_AD_CLIENT_SECRET",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY"
        ]
        
        missing_azure_vars = [var for var in azure_vars if not os.environ.get(var)]
        if missing_azure_vars:
            logger.warning("Missing Azure integration variables: %s", ", ".join(missing_azure_vars))
            logger.warning("Azure integration features may not work properly")
    
    logger.info("All prerequisites checked successfully")
    return True

def check_database_connection():
    """Check database connection."""
    try:
        logger.info("Checking database connection...")
        
        # Import here to avoid circular imports
        from app import db
        
        # Simple query to check connection
        db.engine.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    
    except Exception as e:
        logger.error("Database connection error: %s", str(e))
        return False

def run_database_migrations():
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    try:
        # Simple approach - use db.create_all()
        from app import app, db
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
        
        # For more complex migrations, you would use Alembic/Flask-Migrate
        # subprocess.run(["flask", "db", "upgrade"], check=True)
        
        return True
    
    except Exception as e:
        logger.error("Database migration error: %s", str(e))
        return False

def build_frontend():
    """Build the React frontend."""
    logger.info("Building frontend assets...")
    
    try:
        # Navigate to frontend directory and run build command
        frontend_dir = os.path.join(os.getcwd(), "frontend")
        if not os.path.exists(frontend_dir):
            logger.error("Frontend directory not found: %s", frontend_dir)
            return False
        
        # Build frontend
        subprocess.run(
            ["npm", "run", "build"], 
            cwd=frontend_dir, 
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("Frontend built successfully")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error("Frontend build error: %s", e.stderr)
        return False
    
    except Exception as e:
        logger.error("Frontend build error: %s", str(e))
        return False

def collect_static_files():
    """Collect static files for serving."""
    logger.info("Collecting static files...")
    
    try:
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.getcwd(), "static")
        os.makedirs(static_dir, exist_ok=True)
        
        # Copy built frontend files to static directory
        frontend_build_dir = os.path.join(os.getcwd(), "frontend", "build")
        if not os.path.exists(frontend_build_dir):
            logger.error("Frontend build directory not found: %s", frontend_build_dir)
            return False
        
        # Use subprocess to copy files
        subprocess.run(
            ["cp", "-r", f"{frontend_build_dir}/*", static_dir], 
            check=True,
            shell=True
        )
        
        logger.info("Static files collected successfully")
        return True
    
    except Exception as e:
        logger.error("Static file collection error: %s", str(e))
        return False

def run_tests():
    """Run tests before deployment."""
    logger.info("Running tests...")
    
    try:
        # Set environment to testing
        os.environ["FLASK_ENV"] = "testing"
        
        # Run tests using pytest
        result = subprocess.run(
            ["pytest", "-xvs", "tests/"], 
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("Tests failed: %s", result.stderr)
            return False
        
        logger.info("All tests passed successfully")
        return True
    
    except Exception as e:
        logger.error("Test execution error: %s", str(e))
        return False
    
    finally:
        # Restore original environment
        os.environ["FLASK_ENV"] = os.environ.get("FLASK_ENV", "development")

def create_deployment_record():
    """Create a deployment record."""
    logger.info("Creating deployment record...")
    
    try:
        deployment_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "environment": os.environ.get("FLASK_ENV", "development"),
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "deployer": os.environ.get("USER", "unknown"),
            "database_url": os.environ.get("DATABASE_URL", "").split("@")[-1]  # Hide credentials
        }
        
        # Write deployment record to file
        record_file = os.path.join(os.getcwd(), "deployment_records.json")
        
        existing_records = []
        if os.path.exists(record_file):
            with open(record_file, "r") as f:
                try:
                    existing_records = json.load(f)
                except json.JSONDecodeError:
                    existing_records = []
        
        existing_records.append(deployment_data)
        
        with open(record_file, "w") as f:
            json.dump(existing_records, f, indent=2)
        
        logger.info("Deployment record created successfully")
        return True
    
    except Exception as e:
        logger.error("Error creating deployment record: %s", str(e))
        return False

def deploy():
    """Main deployment function."""
    logger.info("Starting UKG system deployment...")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Aborting deployment.")
        return False
    
    # Run tests if not disabled
    if not args.skip_tests:
        if not run_tests():
            logger.error("Tests failed. Aborting deployment.")
            return False
    
    # Build frontend if not disabled
    if not args.skip_frontend_build:
        if not build_frontend():
            logger.error("Frontend build failed. Aborting deployment.")
            return False
        
        if not collect_static_files():
            logger.error("Static file collection failed. Aborting deployment.")
            return False
    
    # Run database migrations
    if not run_database_migrations():
        logger.error("Database migrations failed. Aborting deployment.")
        return False
    
    # Create deployment record
    create_deployment_record()
    
    logger.info("UKG system deployed successfully!")
    logger.info("Environment: %s", os.environ.get("FLASK_ENV", "development"))
    logger.info("Start the application with 'gunicorn main:app' or 'python main.py'")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UKG System Deployment Tool")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-frontend-build", action="store_true", help="Skip building frontend")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if deploy():
        sys.exit(0)
    else:
        sys.exit(1)