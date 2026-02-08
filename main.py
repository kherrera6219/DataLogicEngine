import signal
import sys
import collections
import os

# Polyfill for MutableMapping (moved to collections.abc in Python 3.10+)
if not hasattr(collections, 'MutableMapping'):
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Mapping = collections.abc.Mapping
    collections.Sequence = collections.abc.Sequence
    collections.Iterable = collections.abc.Iterable
    collections.Callable = collections.abc.Callable

# Polyfill for GraphQL-core 3.x vs flask-graphql 2.x incompatibility
try:
    import graphql
    if not hasattr(graphql, 'get_default_backend'):
        def get_default_backend():
            return None
        graphql.get_default_backend = get_default_backend
    
    import graphql.error
    if not hasattr(graphql.error, 'format_error'):
        # Mock format_error for flask-graphql compatibility
        graphql.error.format_error = lambda e: str(e)
except ImportError:
    pass

from app import app, DEFAULT_PORT
from backend.storage.database_manager import get_db_manager
from backend.storage.runtime_settings import get_auto_start_databases

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
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    try:
        app.run(host="127.0.0.1", port=port, debug=debug_mode, use_reloader=False)
    finally:
        if os.environ.get('IS_DESKTOP_APP', 'False').lower() == 'true':
            get_db_manager().stop_all()
