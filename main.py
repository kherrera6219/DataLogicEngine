import os
import signal
import sys
from app import app, DEFAULT_PORT
from backend.storage.database_manager import get_db_manager

def signal_handler(sig, frame):
    """Ensure databases are stopped on exit."""
    print("\nShutting down desktop databases...")
    db_manager = get_db_manager()
    db_manager.stop_all()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start databases if in desktop mode
    if os.environ.get('IS_DESKTOP_APP', 'False').lower() == 'true':
        print("Desktop Mode Detected: Initializing local databases...")
        db_manager = get_db_manager()
        db_manager.start_all()
    
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    try:
        app.run(host="127.0.0.1", port=port, debug=debug_mode, use_reloader=False)
    finally:
        if os.environ.get('IS_DESKTOP_APP', 'False').lower() == 'true':
            get_db_manager().stop_all()