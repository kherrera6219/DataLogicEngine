
import pytest
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from models import (
    KnowledgeGraphEdge, OAuthAccount, PasswordHistory, AuditLog,
    LLMProviderUsage, ExternalAPIKey, ChatSession, ChatMessage,
    TraceEvidence, TraceClaim, TraceAxisVector, TracePersona,
    TraceKAInvocation, TracePolicyDecision, TraceMemoryEvent, TraceArtifact
)
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

# --- KnowledgeGraphEdge ---
def test_graph_edge_dict(app):
    edge = KnowledgeGraphEdge(
        id=1, 
        edge_id="e1", 
        source_node_id="n1", 
        target_node_id="n2", 
        edge_type="related_to",
        weight=0.5
    )
    d = edge.to_dict()
    assert d['edge_id'] == "e1"
    assert d['source_id'] == "n1"
    assert d['target_id'] == "n2"
    assert d['edge_type'] == "related_to"
    assert d['weight'] == 0.5

# --- OAuthAccount ---
def test_oauth_account_repr(app):
    acc = OAuthAccount(provider="google", provider_user_id="123")
    assert "OAuthAccount" in repr(acc) # Assuming default repr or updated

# --- PasswordHistory ---
def test_password_history_repr(app):
    ph = PasswordHistory(user_id=1, password_hash="hash")
    assert "PasswordHistory" in repr(ph)

# --- AuditLog ---
def test_audit_log_dict(app):
    log = AuditLog(
        action="login", 
        ip_address="127.0.0.1", 
        details="Success",
        # timestamp is default, might differ if not committed. 
        # But to_dict handles None check (if we look at model).
        # We can mock it or check other fields.
        user_id=1
    )
    d = log.to_dict()
    assert d['action'] == "login"
    assert d['details'] == "Success"

# --- LLMProviderUsage ---
def test_provider_usage_basic(app):
    pid = uuid.uuid4()
    u = LLMProviderUsage(provider_id=pid, tokens_in=10, tokens_out=20, latency_ms=100)
    assert u.tokens_in == 10
    assert u.provider_id == pid

# --- ExternalAPIKey ---
def test_external_api_key_dict(app):
    expires_at = datetime.now(UTC) + timedelta(days=7)
    k = ExternalAPIKey(
        id=uuid.uuid4(),
        name="Test Client",
        key_prefix="ukg_test",
        key_hash="hash",
        user_id=1,
        is_active=True,
        expires_at=expires_at
    )
    d = k.to_dict()
    assert d['name'] == "Test Client"
    assert d['prefix'] == "ukg_test"
    assert d['expires_at'] == expires_at.isoformat()
    assert 'key_hash' not in d

def test_external_api_key_verify_rejects_expired_key(app):
    full_key, _prefix, key_hash = ExternalAPIKey.generate_key()
    expired = ExternalAPIKey(
        id=uuid.uuid4(),
        name="Expired Client",
        key_prefix="ukg_test",
        key_hash=key_hash,
        user_id=1,
        is_active=True,
        expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    query = MagicMock()
    query.filter_by.return_value.first.return_value = expired
    setattr(ExternalAPIKey, 'query', query)
    try:
        assert ExternalAPIKey.verify_key(full_key) is None
    finally:
        delattr(ExternalAPIKey, 'query')

# --- ChatSession & ChatMessage ---
def test_chat_session_basic(app):
    sid = uuid.uuid4()
    s = ChatSession(id=sid, user_id=1, title="My Chat", model="gpt-test", mode="chat")
    assert s.title == "My Chat"
    assert s.id == sid
    d = s.to_dict()
    assert d['id'] == str(sid)
    assert d['user_id'] == 1
    assert d['title'] == "My Chat"
    assert d['model'] == "gpt-test"
    assert d['mode'] == "chat"

def test_chat_message_basic(app):
    mid = uuid.uuid4()
    m = ChatMessage(id=mid, role="user", content="hello")
    assert m.role == "user"
    assert m.content == "hello"

# --- Trace Models (remaining) ---
def test_trace_evidence_dict(app):
    eid = uuid.uuid4()
    rid = uuid.uuid4()
    ev = TraceEvidence(evidence_id=eid, run_id=rid, source_type="doc", snippet="fact")
    d = ev.to_dict()
    assert d['evidence_id'] == str(eid)
    assert d['snippet'] == "fact"
    assert d['source']['type'] == "doc"

def test_trace_claim_dict(app):
    cid = uuid.uuid4()
    rid = uuid.uuid4()
    c = TraceClaim(claim_id=cid, run_id=rid, text="sky is blue", confidence=0.9)
    d = c.to_dict()
    assert d['text'] == "sky is blue"
    assert d['support']['confidence'] == 0.9

def test_trace_axis_vector_dict(app):
    vid = uuid.uuid4()
    rid = uuid.uuid4()
    av = TraceAxisVector(vector_id=vid, run_id=rid, axes={"dim1": 0.5})
    d = av.to_dict()
    assert d['axes'] == {"dim1": 0.5}

def test_trace_persona_dict(app):
    pid = uuid.uuid4()
    rid = uuid.uuid4()
    p = TracePersona(persona_id=pid, run_id=rid, persona_type="analyst", persona_name="Expert", confidence=0.8)
    d = p.to_dict()
    assert d['persona_name'] == "Expert"
    assert d['draft']['confidence'] == 0.8

def test_trace_ka_invocation_dict(app):
    kid = uuid.uuid4()
    rid = uuid.uuid4()
    k = TraceKAInvocation(invocation_id=kid, run_id=rid, ka_id="ka_01", inputs={"q": "hi"})
    d = k.to_dict()
    assert d['ka_id'] == "ka_01"
    assert d['inputs'] == {"q": "hi"}

def test_trace_policy_decision_dict(app):
    did = uuid.uuid4()
    rid = uuid.uuid4()
    pd = TracePolicyDecision(
        decision_id=did, 
        run_id=rid, 
        policy_id="pol_1", 
        policy_name="NoPll", 
        decision="pass"
    )
    d = pd.to_dict()
    assert d['policy']['name'] == "NoPll"
    assert d['decision'] == "pass"

def test_trace_memory_event_dict(app):
    mid = uuid.uuid4()
    rid = uuid.uuid4()
    me = TraceMemoryEvent(
        event_id=mid, 
        run_id=rid, 
        event_type="recall", 
        memory_type="long", 
        content={"k": "v"}
    )
    d = me.to_dict()
    assert d['type'] == "recall"
    assert d['memory_type'] == "long"
    assert d['content'] == {"k": "v"}


def test_trace_artifact_dict(app):
    aid = uuid.uuid4()
    rid = uuid.uuid4()
    ta = TraceArtifact(artifact_id=aid, run_id=rid, label="doc", content="data")
    d = ta.to_dict()
    assert d['label'] == "doc"
    assert d['content'] == "data"
