"""
Universal Knowledge Graph (UKG) - Main Entry Point

This module initializes the UKG application and provides the entry point
for running the system.
"""

import logging
from app import app
from config import get_config

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=config.LOG_FORMAT,
    filename=config.LOG_FILE,
    filemode='a'
)

console = logging.StreamHandler()
console.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
formatter = logging.Formatter(config.LOG_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Universal Knowledge Graph (UKG) System")
    app.run(host='0.0.0.0', port=3000, debug=config.DEBUG)