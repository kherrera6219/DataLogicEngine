"""Phase 8 external trace ownership and response-scope tests."""

from extensions import db
from models import AIAuditEvent, ExternalAPIKey, TraceEvidence, TraceRun, TraceStage
from tests.conftest import create_test_user


def _client_key(*, user_id: int, name: str, scopes: list[str]) -> tuple[ExternalAPIKey, str]:
    full_key, prefix, key_hash = ExternalAPIKey.generate_key()
    record = ExternalAPIKey(
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        user_id=user_id,
        permissions={'scopes': scopes},
        rate_limit_rpm=60,
        max_concurrent_requests=2,
    )
    db.session.add(record)
    db.session.flush()
    return record, full_key


def test_external_trace_read_is_client_owned_and_evidence_scoped(app) -> None:
    with app.app_context():
        user_id = create_test_user(username='gateway-trace-owner')
        key, full_key = _client_key(
            user_id=user_id,
            name='trace-reader',
            scopes=['trace:read', 'evidence:read'],
        )
        other_key, other_full_key = _client_key(
            user_id=user_id,
            name='other-trace-reader',
            scopes=['trace:read'],
        )
        run = TraceRun(user_id=user_id, status='completed', model_name='gpt-5.5')
        db.session.add(run)
        db.session.flush()
        db.session.add(AIAuditEvent(
            run_id=run.run_id,
            user_id=user_id,
            api_key_id=key.id,
            provider='openai',
            model='gpt-5.5',
            model_version='gpt-5.5',
            success=True,
        ))
        db.session.add(TraceStage(
            run_id=run.run_id,
            name='validation',
            stage_type='step',
            step_index=9,
            status='pass',
            duration_ms=14,
        ))
        db.session.add(TraceEvidence(
            run_id=run.run_id,
            source_type='document',
            source_id='source-1',
            source_title='Approved source',
            authority='high',
            content_hash='a' * 64,
            snippet='content that is intentionally not returned by the gateway trace summary',
        ))
        db.session.commit()
        run_id = str(run.run_id)
        assert other_key.id != key.id

    client = app.test_client()
    response = client.get(
        f'/api/v1/gateway/traces/{run_id}',
        headers={'Authorization': f'Bearer {full_key}'},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body['stages'][0]['name'] == 'validation'
    assert body['evidence'][0]['source_id'] == 'source-1'
    assert 'snippet' not in body['evidence'][0]

    foreign = client.get(
        f'/api/v1/gateway/traces/{run_id}',
        headers={'Authorization': f'Bearer {other_full_key}'},
    )
    assert foreign.status_code == 404
