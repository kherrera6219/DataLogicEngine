
from app import app
import logging
from utils.logging_config import setup_logging
import os

if __name__ == "__main__":
    setup_logging()
    logging.info("Starting UKG System with full backend...")
    # Force set the paths to make them consistent
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.run(host="0.0.0.0", port=3000, debug=True)
