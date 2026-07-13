# ruff: noqa: E402
import signal
import sys
import os

from backend.bootstrap_compat import apply_runtime_compatibility_patches

apply_runtime_compatibility_patches()

from app import app, DEFAULT_PORT
from backend.storage.database_manager import get_db_manager
from backend.storage.runtime_settings import get_auto_start_databases
from backend.security.listener_policy import resolve_loopback_listener_host

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

    # Start databases in desktop mode only if preference is enabled.
    if os.environ.get('IS_DESKTOP_APP', 'False').lower() == 'true':
        if get_auto_start_databases():
            print("Desktop Mode Detected: Initializing local databases...")
            db_manager = get_db_manager()
            db_manager.start_all()
        else:
            print("Desktop Mode Detected: Database auto-start disabled by settings.")
    
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    listener_host = resolve_loopback_listener_host(os.environ.get('FLASK_RUN_HOST'))
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    try:
        app.run(host=listener_host, port=port, debug=debug_mode, use_reloader=False)
    finally:
        if os.environ.get('IS_DESKTOP_APP', 'False').lower() == 'true':
            get_db_manager().stop_all()
