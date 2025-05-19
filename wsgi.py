"""
WSGI entry point for the UKG system

This file serves as the entry point for Gunicorn to run the UKG application
"""

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)