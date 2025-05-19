from app import app
import logging
from utils.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    logging.info("Starting UKG System...")
    app.run(host="0.0.0.0", port=5000, debug=True)
