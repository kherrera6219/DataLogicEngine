from app import app, orchestrator
import logging
from utils.logging_config import setup_logging
from core.app_orchestrator import AppOrchestrator
from config import AppConfig

if __name__ == "__main__":
    setup_logging()
    logging.info("Starting UKG System with full backend...")
    
    # Initialize configuration
    config = AppConfig()
    
    # Initialize orchestrator and set it in app
    app.orchestrator = AppOrchestrator(config)
    app.config['orchestrator'] = app.orchestrator
    
    # Update the module-level reference for API access
    import app as app_module
    app_module.orchestrator = app.orchestrator
    
    logging.info("UKG System components initialized")
    app.run(host="0.0.0.0", port=3000, debug=True)