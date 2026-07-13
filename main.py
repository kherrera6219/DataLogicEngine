# ruff: noqa: E402
import signal
import sys
import os

from backend.bootstrap_compat import apply_runtime_compatibility_patches

apply_runtime_compatibility_patches()

from app import create_app, DEFAULT_PORT
from backend.security.listener_policy import resolve_loopback_listener_host

app = None

def signal_handler(sig, frame):
    """Ensure the application-owned runtime shuts down on exit."""
    print("\nShutting down desktop databases...")
    if app is not None:
        app.extensions["dle_runtime"].shutdown()
    sys.exit(0)

if __name__ == "__main__":
    app = create_app(start_runtime=True)
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    port = int(app.config.get("PORT", DEFAULT_PORT))
    listener_host = resolve_loopback_listener_host(os.environ.get('FLASK_RUN_HOST'))
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    try:
        app.run(host=listener_host, port=port, debug=debug_mode, use_reloader=False)
    finally:
        app.extensions["dle_runtime"].shutdown()
