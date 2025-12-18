import os
from app import app, DEFAULT_PORT

import routes  # noqa: F401 - Import routes to register all route handlers

if __name__ == "__main__":
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host="0.0.0.0", port=port, debug=debug_mode)