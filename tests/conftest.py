# ruff: noqa: E402
import os
import sys
import gc
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

# Force in-memory storage for tests to avoid Redis dependencies
os.environ['IS_DESKTOP_APP'] = 'false'
os.environ['RATELIMIT_STORAGE_URI'] = 'memory://'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0' # Keep URL but we'll disable it
os.environ['USE_REDIS'] = 'False'
os.environ['SESSION_TYPE'] = 'null' # Disable flask-session for tests if possible
# DSQP persona construction must not reach a live local model during tests:
# the suite validates the deterministic scaffold, and the LLM-assisted path is
# covered separately with an injected stub client. (A machine with Ollama
# listening but a slow/unloadable model would otherwise add a 20s timeout per
# persona axis.) Tests that exercise the LLM path set this flag themselves.
os.environ['DSQP_LLM_ASSISTED'] = 'false'
os.environ.setdefault('ENCRYPTION_KEK_SECRET', 'pytest-only-encryption-kek-secret-32-bytes')
os.environ.setdefault(
    'UKG_KEY_DIR',
    str(Path(__file__).resolve().parent.parent / '.pytest_cache' / 'security_keys'),
)

# Ensure repository root is on the Python path for tests
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from flask import has_app_context
from app import app as flask_app, db
from extensions import limiter, login_manager
from sqlalchemy.engine import Engine

# Shared helpers live in a regular importable module (not this conftest) so test
# modules can import them by a collision-free name. Re-exported here for
# backward compatibility with any `from conftest import ...` call sites. See A18.
from tests._helpers import (
    TEST_DATABASE_URL,
    TEST_DB_PATH,
    authenticate_client_session,
    drop_all_test_tables,
    is_sqlite_test_db,  # noqa: F401  (re-exported for tests)
)


def _dispose_sqlalchemy_engines() -> None:
    """Dispose SQLAlchemy engines to reduce leaked sqlite handles in tests."""
    try:
        engines = db.engines
    except Exception:
        return

    for engine in list(engines.values()):
        try:
            engine.dispose()
        except Exception:
            pass


def _dispose_stray_sqlalchemy_engines() -> None:
    """Dispose any Engine instances not tracked by flask-sqlalchemy bind maps."""
    for obj in gc.get_objects():
        if isinstance(obj, Engine):
            try:
                obj.dispose()
            except Exception:
                pass


@pytest.fixture
def app():
    """Provide app fixture for tests that need app context."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URL
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['CACHE_TYPE'] = 'NullCache'
    flask_app.config['RATELIMIT_ENABLED'] = False
    flask_app.config['CORS_ORIGINS'] = "*"
    flask_app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}
    
    # Remove Limiter from before_request_funcs to avoid Redis connection
    for key in list(flask_app.before_request_funcs.keys()):
        flask_app.before_request_funcs[key] = [
            f for f in flask_app.before_request_funcs[key]
            if 'check_request_limit' not in getattr(f, '__name__', '')
        ]
    
    from limits.storage.memory import MemoryStorage
    limiter._storage = MemoryStorage() 
    limiter.enabled = False

    from models import User

    # Rebind user loader on each test app setup because the suite imports
    # multiple app factories that can overwrite global LoginManager callbacks.
    @login_manager.user_loader
    def _load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    with flask_app.app_context():
        _dispose_sqlalchemy_engines()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
        # Ensure test runs start from a clean schema even if the module-level
        # app initialization previously populated the default sqlite database.
        drop_all_test_tables()
        db.create_all()
        yield flask_app
        drop_all_test_tables()
        _dispose_sqlalchemy_engines()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


@pytest.fixture(scope="session", autouse=True)
def _final_engine_cleanup():
    """Ensure all SQLAlchemy pools are disposed once at the end of the test session."""
    yield
    with flask_app.app_context():
        db.session.remove()
        _dispose_sqlalchemy_engines()
        _dispose_stray_sqlalchemy_engines()

@pytest.fixture
def client(app):
    """Create test client."""
    with app.test_client() as test_client:
        yield test_client


def create_test_user(
    *,
    username="testuser",
    email="test@example.com",
    password="SecureTest789$#@",
    role="user",
    is_admin=False,
    active=True,
    sid=None,
):
    """Create or update a local test user and return its database id."""
    if not has_app_context():
        with flask_app.app_context():
            return create_test_user(
                username=username,
                email=email,
                password=password,
                role=role,
                is_admin=is_admin,
                active=active,
                sid=sid,
            )

    from models import User

    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User()
        user.username = username
        db.session.add(user)

    # Test fixtures should not depend on field-encryption audit side effects.
    user._email = email
    # `role`/`is_admin` params are accepted for call-site back-compat but no longer
    # persisted — the columns were removed under single-mode (auth-deprecation Phase E).
    user.active = active
    user.sid = sid
    if password:
        from werkzeug.security import generate_password_hash

        user.password_hash = generate_password_hash(password)

    db.session.commit()
    return user.id


def seed_login_session(client, app, *, username='testuser', email=None,
                       role='user', is_admin=False, sid=None):
    """Provision a local user and seed a Flask-Login session.

    Route-independent test login helper. The app is local-first / desktop-only;
    the public web ``/register`` and ``/login`` routes were intentionally
    removed in favour of the desktop auto-login flow, which ends by calling
    ``flask_login.login_user(user)``. This helper reproduces that end state
    without depending on removed routes or Windows identity resolution.
    """
    email = email or f'{username}@local.ukg'
    sid = sid or f'S-1-5-21-{username.upper()}'
    with app.app_context():
        user_id = create_test_user(
            username=username,
            email=email,
            password='SecureTest789$#@',
            role=role,
            is_admin=is_admin,
            sid=sid,
        )
    authenticate_client_session(client, user_id)
    return user_id


def login_test_client(
    client,
    *,
    username="testuser",
    email="test@example.com",
    password="SecureTest789$#@",
    role="user",
    is_admin=False,
    active=True,
):
    """Create a test user and authenticate the client without legacy web auth routes."""
    user_id = create_test_user(
        username=username,
        email=email,
        password=password,
        role=role,
        is_admin=is_admin,
        active=active,
    )
    return authenticate_client_session(client, user_id)


@pytest.fixture
def authenticated_client(app, client):
    """Create an authenticated test client.

    This app is local-first / desktop-only: the public web ``/register`` and
    ``/login`` routes were intentionally removed (see commit
    ``refactor(auth): remove dead web-app auth routes; keep desktop-only
    endpoints``). The real authentication entry point is the desktop
    auto-login flow, which resolves a Windows identity, auto-provisions a
    local ``User``, and then calls ``flask_login.login_user(user)`` to
    establish a Flask-Login session.

    Rather than depend on removed routes (or on Windows identity resolution,
    which is unavailable in CI), this fixture reproduces that end state
    directly via :func:`seed_login_session`. This is route-independent and
    matches the session a successful desktop auto-login would produce.
    """
    seed_login_session(client, app, username='testuser', email='test@example.com')
    return client
