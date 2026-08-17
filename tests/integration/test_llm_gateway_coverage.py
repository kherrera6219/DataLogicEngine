
def test_gateway_health_rejects_anonymous_client(client):
    """Gateway health is not an anonymous topology probe."""
    assert client.get('/api/v1/gateway/health').status_code == 401


def test_gateway_health(authenticated_client):
    """Authenticated desktop health reports the local provider state."""
    response = authenticated_client.get('/api/v1/gateway/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] in ['healthy', 'degraded']
    assert 'active_providers' in data

def test_list_providers(authenticated_client):
    """Test standard provider listing."""
    response = authenticated_client.get('/api/v1/gateway/providers')
    assert response.status_code == 200
    data = response.get_json()
    assert 'providers' in data

def test_list_api_keys(authenticated_client):
    """Test API key management via admin endpoint."""
    response = authenticated_client.get('/api/v1/admin/gateway/api-keys')
    assert response.status_code == 200
    data = response.get_json()
    assert 'api_keys' in data

def test_get_usage(authenticated_client):
    """Test usage statistics."""
    response = authenticated_client.get('/api/v1/admin/gateway/usage')
    assert response.status_code == 200

def test_llm_admin_requires_json_session_auth(client):
    """LLM admin endpoints should reject unauthenticated clients with JSON 401."""
    response = client.get('/api/v1/admin/gateway/api-keys')
    assert response.status_code == 401
    body = response.get_json()
    assert body['success'] is False
    assert body['code'] == 'UNAUTHORIZED'

def test_gateway_chat_validation(authenticated_client):
    """Test chat endpoint with invalid data."""
    # Test missing messages
    response = authenticated_client.post('/api/v1/gateway/chat', 
                                json={'model': 'gpt-4'})
    assert response.status_code == 400

def test_create_api_key(authenticated_client):
    """Test External API key creation."""
    response = authenticated_client.post('/api/v1/admin/gateway/api-keys',
                                json={'name': 'test-key-new', 'scopes': ['run:read']})
    assert response.status_code == 201
    data = response.get_json()
    assert 'api_key' in data


def test_phase8_client_key_rotation_revoke_expire_delete_lifecycle(authenticated_client, app):
    import uuid

    from extensions import db
    from models import AuditLog, ExternalAPIKey

    created = authenticated_client.post(
        '/api/v1/admin/gateway/api-keys',
        json={
            'name': 'phase8-client',
            'scopes': ['chat', 'models:read'],
            'rate_limit_rpm': 20,
        },
    )
    assert created.status_code == 201
    created_body = created.get_json()
    original_id = created_body['id']
    assert created_body['scopes'] == ['chat', 'models:read']
    assert created_body['api_key'].startswith('ukg_')

    active_delete = authenticated_client.delete(f'/api/v1/admin/gateway/api-keys/{original_id}')
    assert active_delete.status_code == 409
    assert active_delete.get_json()['code'] == 'CLIENT_KEY_STILL_ACTIVE'

    rotated = authenticated_client.post(
        f'/api/v1/admin/gateway/api-keys/{original_id}/rotate',
        json={'overlap_seconds': 0},
    )
    assert rotated.status_code == 201
    rotated_body = rotated.get_json()
    replacement_id = rotated_body['id']
    assert rotated_body['api_key'].startswith('ukg_')
    assert rotated_body['replaced_key_id'] == original_id
    assert rotated_body['rotated_from_id'] == original_id

    revoked = authenticated_client.post(
        f'/api/v1/admin/gateway/api-keys/{replacement_id}/revoke',
        json={'reason': 'compromise drill'},
    )
    assert revoked.status_code == 200

    deleted = authenticated_client.delete(f'/api/v1/admin/gateway/api-keys/{replacement_id}')
    assert deleted.status_code == 200

    expiring = authenticated_client.post(
        '/api/v1/admin/gateway/api-keys',
        json={'name': 'phase8-expire', 'scopes': ['run:read']},
    ).get_json()
    expired = authenticated_client.post(
        f"/api/v1/admin/gateway/api-keys/{expiring['id']}/expire",
        json={'reason': 'expiry drill'},
    )
    assert expired.status_code == 200

    with app.app_context():
        original = db.session.get(ExternalAPIKey, uuid.UUID(original_id))
        assert original.is_active is False
        assert original.revoked_reason == 'rotated'
        expiring_record = db.session.get(ExternalAPIKey, uuid.UUID(expiring['id']))
        assert expiring_record.is_active is False
        assert expiring_record.expires_at is not None
        deleted_record = db.session.get(ExternalAPIKey, uuid.UUID(replacement_id))
        assert deleted_record.deleted_at is not None
        assert deleted_record.key_hash.startswith('deleted:')
        assert deleted_record.permissions == {}
        assert ExternalAPIKey.verify_key(rotated_body['api_key']) is None
        actions = {
            row.action
            for row in AuditLog.query.filter(AuditLog.action.like('gateway_client_key_%')).all()
        }
        assert {
            'gateway_client_key_created',
            'gateway_client_key_rotated',
            'gateway_client_key_revoked',
            'gateway_client_key_expired',
            'gateway_client_key_deleted',
        }.issubset(actions)


def test_phase8_sync_idempotency_replays_without_duplicate_provider_spend(authenticated_client):
    from unittest.mock import AsyncMock, MagicMock, patch

    created = authenticated_client.post(
        '/api/v1/admin/gateway/api-keys',
        json={'name': 'phase8-idempotency', 'scopes': ['chat']},
    ).get_json()
    headers = {'Authorization': f"Bearer {created['api_key']}"}
    payload = {
        'idempotency_key': 'retry-key-12345',
        'messages': [{'role': 'user', 'content': 'Idempotent hello'}],
    }
    governed = MagicMock()
    governed.ok = True
    governed.content = 'governed result'
    governed.run_id = '00000000-0000-0000-0000-000000000111'
    governed.provider_used = 'openai'
    governed.model_used = 'gpt-5.6-sol'
    governed.usage = {'tokens_in': 3, 'tokens_out': 2}
    governed.coordinate = None
    governed.warnings = []
    governed.trace = []
    governed.confidence = None
    governed.confidence_measurement = None
    governed.convergence = None
    governed.claims = []
    governed.citations = []
    governed.validators = []
    governed.evidence_count = 0
    governed.explainability = {}
    governed.contract_version = 'governed.v1'
    governed.status = 'completed'
    governed.failure = None
    governed.meta = {'source_ids': []}

    with patch('backend.llm_gateway.api.LLMGateway') as gateway_cls:
        gateway_cls.return_value.process = AsyncMock(return_value=governed)
        first = authenticated_client.post(
            '/api/v1/gateway/chat',
            headers=headers,
            json=payload,
        )
        replay = authenticated_client.post(
            '/api/v1/gateway/chat',
            headers=headers,
            json=payload,
        )
        conflict = authenticated_client.post(
            '/api/v1/gateway/chat',
            headers=headers,
            json={
                **payload,
                'messages': [{'role': 'user', 'content': 'Different request'}],
            },
        )

    assert first.status_code == 200
    assert first.get_json()['data']['response'] == 'governed result'
    assert replay.status_code == 200
    assert replay.headers['Idempotent-Replay'] == 'true'
    assert replay.get_json() == first.get_json()
    assert conflict.status_code == 409
    assert conflict.get_json()['code'] == 'IDEMPOTENCY_CONFLICT'
    gateway_cls.return_value.process.assert_awaited_once()
