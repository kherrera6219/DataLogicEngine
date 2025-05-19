
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Setup base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with our base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Setup secret key (required for sessions)
app.secret_key = os.environ.get("SESSION_SECRET", "universal-knowledge-graph-secret")

# Configure the PostgreSQL database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize app with SQLAlchemy
db.init_app(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Register the UKG API blueprint
from backend.ukg_api import ukg_api
app.register_blueprint(ukg_api)

# Initialize models and create tables
with app.app_context():
    # Import all models
    import models
    
    # Create all tables
    db.create_all()
    logging.info(f"[{datetime.now()}] Database tables created successfully")

# Root route
@app.route('/')
def index():
    return render_template('index.html', title="Universal Knowledge Graph System")

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "name": "Universal Knowledge Graph System",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })

# Run the application
if __name__ == "__main__":
    logging.info(f"[{datetime.now()}] Starting UKG System with full backend...")
    
    # Force set the paths to make them consistent
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    # Start the server
    app.run(host="0.0.0.0", port=5000, debug=True)
