from flask import Flask, render_template, request, jsonify
from backend import create_app
import os
import logging
from config import AppConfig

# Initialize the Flask app with our backend
app = create_app()

# Load configuration
config = AppConfig()

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

# API routes are now handled by the backend blueprints

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)