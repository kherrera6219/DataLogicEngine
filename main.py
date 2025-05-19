
from app import app
import logging
from utils.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    logging.info("Starting UKG System with full backend...")
    app.run(host="0.0.0.0", port=3000, debug=True)
