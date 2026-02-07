#!/usr/bin/env python3
"""
Enterprise Development Environment Setup Script
DataLogicEngine v2.0.0

This script automates the setup of the local development environment.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    print(f"\n{Colors.HEADER}➤ {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def check_python_version():
    print_step("Checking Python Version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python 3.11+ is required. You are running {version.major}.{version.minor}")
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor} detected")

def setup_virtualenv():
    print_step("Setting up Virtual Environment")
    venv_path = Path(".venv")
    if not venv_path.exists():
        subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
        print_success("Created .venv")
    else:
        print_success(".venv already exists")

def install_dependencies():
    print_step("Installing Dependencies")
    pip_cmd = ".venv/bin/pip" if platform.system() != "Windows" else ".venv\\Scripts\\pip"

    requirements = Path("requirements.txt")
    pyproject = Path("pyproject.toml")

    # Core dependencies
    subprocess.check_call([pip_cmd, "install", "--upgrade", "pip"])

    if requirements.exists():
        subprocess.check_call([pip_cmd, "install", "-r", str(requirements)])
        print_success("Dependencies installed from requirements.txt")
        return

    if pyproject.exists():
        subprocess.check_call([pip_cmd, "install", "-e", "."])
        print_success("Dependencies installed from pyproject.toml (editable mode)")
        return

    raise FileNotFoundError("No dependency manifest found (requirements.txt or pyproject.toml)")

def setup_env_file():
    print_step("Configuring Environment")
    env_path = Path(".env")
    template_path = Path(".env.template")
    
    if not env_path.exists() and template_path.exists():
        shutil.copy(template_path, env_path)
        print_success("Created .env from template")
        print(f"{Colors.WARNING}IMPORTANT: Please edit .env and update your keys!{Colors.ENDC}")
    elif env_path.exists():
        print_success(".env already exists")
    else:
        print_error("No .env.template found")

def check_node():
    print_step("Checking Node.js (Frontend)")
    try:
        version = subprocess.check_output(["node", "--version"]).decode("utf-8").strip()
        print_success(f"Node.js {version} detected")
    except FileNotFoundError:
        print(f"{Colors.WARNING}Node.js not found. Frontend setup skipped.{Colors.ENDC}")

def main():
    print(f"{Colors.BOLD}DataLogicEngine Enterprise Setup{Colors.ENDC}")
    print("==================================")
    
    try:
        check_python_version()
        setup_virtualenv()
        install_dependencies()
        setup_env_file()
        check_node()
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}Setup Complete!{Colors.ENDC}")
        print("\nTo start the backend:")
        if platform.system() == "Windows":
            print("  .venv\\Scripts\\activate")
        else:
            print("  source .venv/bin/activate")
        print("  python app.py")
        
    except Exception as e:
        print_error(f"Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
