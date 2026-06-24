
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import uuid
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
import base64

from models import (
    User, SimulationSession, LLMProvider, ExternalAPIKey, 
    TraceRun, TraceStage, KnowledgeGraphNode
)

from backend import create_legacy_app

# --- Fixtures ---

@pytest.fixture
def app():
    # Create app using the factory to ensure environment consistency
    # But for isolated model tests, we might want a lightweight app
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    # Valid 32 byte base64 key
    app.config['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(b'0'*32)
    
    # We need to push context for db to work if models uses it
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

# --- User Model Tests ---

def test_user_email_encryption(app):
    user = User()
    mock_enc = MagicMock()
    mock_enc.encrypt.return_value = "encrypted_email"
    mock_enc.decrypt.return_value = "plain@example.com"
    
    # Patch the real encryption_manager object in extensions module
    with patch('extensions.encryption_manager', mock_enc):
        # Setter
        user.email = "plain@example.com"
        assert user._email == "encrypted_email"
        mock_enc.encrypt.assert_called_with("plain@example.com", field_name='email')
        
        # Getter
        assert user.email == "plain@example.com"
        mock_enc.decrypt.assert_called_with("encrypted_email", field_name='email')
        
        # Setter None
        user.email = None
        assert user._email is None
        
        # Getter None
        user._email = None
        assert user.email is None

        # Getter Fallback
        mock_enc.decrypt.side_effect = ValueError("Bad key")
        user._email = "plain_legacy"
        assert user.email == "plain_legacy"

def test_user_password(app):
    user = User()
    with patch('backend.security.password_security.PasswordSecurity.validate_password_strength') as mock_val:
        # Weak
        mock_val.return_value = (False, ["Too short"])
        with pytest.raises(ValueError, match="weak"):
            user.set_password("weak")
            
        # Strong
        mock_val.return_value = (True, [])
        user.set_password("StrongP@ss1")
        assert user.password_hash is not None
        assert user.check_password("StrongP@ss1")
        assert not user.check_password("Wrong")
        
        # Check expired
        with patch('backend.security.password_security.PasswordSecurity.is_password_expired') as mock_exp:
            mock_exp.return_value = True
            assert user.is_password_expired()

def test_user_login_atomic(app):
    user = User(id=1, username="test", failed_login_attempts=0)
    
    # Patch db.session on the models module where it is used
    with patch('models.db.session') as mock_session:
        with patch('models.db.update'):
             # record_failed_login
             user.record_failed_login()
             mock_session.execute.assert_called()
             mock_session.commit.assert_called()
             mock_session.refresh.assert_called_with(user)
             
             # Test Lockout logic
             user.failed_login_attempts = 10 
             with patch('backend.config.settings.settings.MAX_FAILED_LOGIN_ATTEMPTS', 5):
                 user.record_failed_login()
                 assert mock_session.commit.call_count >= 2 

             # record_successful_login
             user.record_successful_login()
             mock_session.commit.assert_called()

def test_user_login_error_handling(app):
    user = User(id=1)
    with patch('models.db.session') as mock_session:
        # Mock ALL executions to fail
        mock_session.execute.side_effect = SQLAlchemyError("DB Error")
        
        with pytest.raises(SQLAlchemyError):
            user.record_failed_login()
        mock_session.rollback.assert_called()

def test_user_dict(app):
    user = User(id=1, username="u", created_at=datetime(2023,1,1), last_successful_login=datetime(2023,1,2))
    d = user.to_dict()
    assert d['username'] == "u"
    assert d['created_at'].startswith("2023-01-01")
    
    u2 = User.from_dict({"username": "u2"})
    assert u2.username == "u2"

# --- Simulation Session Tests ---

def test_sim_encryption(app):
    sim = SimulationSession()
    mock_enc = MagicMock()
    mock_enc.encrypt.return_value = "enc_val"
    mock_enc.decrypt.return_value = "plain_val"
    
    with patch('extensions.encryption_manager', mock_enc):
        sim.name = "My Sim"
        assert sim._name == "enc_val"
        assert sim.name == "plain_val"

def test_sim_dict(app):
    sim = SimulationSession(
        id=1, session_id="uuid", user_id=1, status="pending",
        created_at=datetime(2023,1,1)
    )
    d = sim.to_dict()
    assert d['session_id'] == "uuid"

# --- LLM Provider Tests ---

def test_llm_provider_key(app):
    p = LLMProvider()
    p.set_api_key("secret_key")
    assert p.api_key_encrypted is not None
    assert p.get_api_key() == "secret_key"

def test_llm_provider_dict(app):
    p = LLMProvider(id=uuid.uuid4(), name="GPT", is_active=True)
    d = p.to_dict()
    assert d['name'] == "GPT"

# --- API Key Tests ---

def test_ext_api_key_methods(app):
    full, prefix, h = ExternalAPIKey.generate_key()
    assert prefix.startswith("ukg_")
    
    mock_query = MagicMock()
    with patch.object(ExternalAPIKey, 'query', mock_query):
        mock_query.filter_by.return_value.first.return_value = "found_key"
        assert ExternalAPIKey.verify_key("prefix_secret") == "found_key"

# --- Trace Model Tests ---

def test_trace_run_dict(app):
    run = TraceRun(run_id=uuid.uuid4(), status="pass", confidence=0.9)
    d = run.to_dict()
    assert d['status'] == "pass"

def test_trace_stage_dict(app):
    stage = TraceStage(stage_id=uuid.uuid4(), name="S1", duration_ms=100)
    d = stage.to_dict()
    assert d['name'] == "S1"

# --- Graph Model Tests ---

def test_graph_node_dict(app):
    node = KnowledgeGraphNode(id=1, node_id="n1", label="Node 1")
    d = node.to_dict()
    assert d['node_id'] == "n1"

#def test_graph_edge_dict(app):
    #edge = KnowledgeGraphEdge(id=1, edge_id="e1", source_node_id="n1", target_node_id="n2")
    # d = edge.to_dict()
    # assert d['edge_id'] == "e1"

# --- App Factory Tests ---

def test_create_legacy_app():
    test_env = {
        "PYTEST_CURRENT_TEST": "tests/unit/test_models.py::test_create_legacy_app",
        "CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000,app://-",
    }
    with patch('extensions.db.init_app') as mock_db, \
            patch('backend.JWTManager') as mock_jwt, \
            patch('backend.CORS') as mock_cors, \
            patch.dict('os.environ', test_env, clear=True):

        modules_to_mock = [
            'routes.auth_routes', 'backend.chat', 'backend.ukg_api',
            'routes.user_data_routes', 'backend.routes.settings_routes',
            'backend.routes.location_routes', 'routes.admin_routes',
            'routes.api_routes', 'routes.ka_routes', 'backend.truth_engine.api',
            'backend.tracing.api', 'backend.routes.search_routes',
            'backend.llm_gateway.api', 'backend.pillar_api', 'backend.rest_api'
        ]

        mock_modules = {}
        for m in modules_to_mock:
            mock_modules[m] = MagicMock()

        with patch.dict('sys.modules', mock_modules):
            app = create_legacy_app()
            assert isinstance(app, Flask)
            assert app.config['SECRET_KEY'] == 'dev-secret-key'

            mock_db.assert_called_with(app)
            mock_jwt.assert_called_with(app)
            mock_cors.assert_called_with(
                app,
                resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000", "app://-"]}},
                supports_credentials=True,
            )


def test_create_legacy_app_requires_secrets_outside_pytest():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(RuntimeError, match="SECRET_KEY must be configured"):
            create_legacy_app()


# --- ORM surface regression guard ---
#
# Regression guard for the models.py truncation in 6c7cf68b: an unrelated MFA
# commit accidentally dropped 47 db.Model classes, which broke top-level imports
# across the backend (api_routes, gateway, node_repository) yet `import models`
# still succeeded, so nothing failed loudly. This test pins the full ORM surface
# so any future deletion/rename of a model class is caught at collection time.
EXPECTED_MODEL_CLASSES = frozenset({
    "AIAuditEvent", "APIKey", "ArtifactRedaction", "AuditLog", "ChatMessage",
    "ChatSession", "ClaimEvidenceLink", "ComplianceMapping", "Domain", "Edge",
    "EvidenceConflict", "ExternalAPIKey", "FeatureFlag", "FeatureFlagAuditEvent",
    "IntegratedView", "KAArtifactLink", "KAExecution", "KnowledgeAlgorithm",
    "KnowledgeGraphEdge", "KnowledgeGraphNode", "LLMProvider", "LLMProviderUsage",
    "Location", "MCPPrompt", "MCPResource", "MCPServer", "MCPTool", "MemoryEntry",
    "MethodNode", "ModelRoutingPolicy", "Node", "PasswordHistory",
    "Persona", "PersonaEvidenceLink", "Perspective", "PillarLevel", "PromptTemplate",
    "Sector", "SimulationSession", "StageArtifactLink", "StageLog", "TimeContext",
    "TraceArtifact", "TraceAxisVector", "TraceClaim", "TraceEvidence", "TraceExport",
    "TraceKAInvocation", "TraceMemoryEvent", "TracePersona", "TracePolicyDecision",
    "TraceRun", "TraceSpan", "TraceStage", "TruthArtifact", "TruthAuditEvent",
    "TruthBudget", "TruthLinkMessage", "TruthMetric", "TruthSession", "UkgSession",
    "User", "UserAIPreferences", "UserNotificationPreference",
})


def test_models_orm_surface_is_complete():
    """All expected db.Model classes are present and are real ORM models.

    Guards against an accidental truncation of models.py (see 6c7cf68b).
    """
    import models as models_module

    missing = sorted(
        name for name in EXPECTED_MODEL_CLASSES
        if not hasattr(models_module, name)
    )
    assert not missing, f"models.py is missing expected ORM classes: {missing}"

    # Each expected symbol must actually be a mapped ORM model, not a stub/shadow.
    for name in EXPECTED_MODEL_CLASSES:
        cls = getattr(models_module, name)
        assert hasattr(cls, "__tablename__"), f"{name} is not a mapped db.Model"
