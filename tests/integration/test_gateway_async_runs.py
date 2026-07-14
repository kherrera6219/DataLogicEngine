"""Phase 8 durable asynchronous gateway route tests."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from unittest.mock import MagicMock, patch
import uuid

from extensions import db
from models import GatewayAsyncRun

from backend.llm_gateway.payload_cipher import decrypt_payload, encrypt_payload


def _request_payload(content: str = 'Run governed work') -> dict:
    return {
        'messages': [{'role': 'user', 'content': content}],
        'virtual_model': 'dle-standard',
        'idempotency_key': 'async-retry-key-123',
        'request_id': 'async-request-123',
    }


def test_async_run_create_is_encrypted_idempotent_and_cancellable(
    authenticated_client,
    app,
) -> None:
    runner = MagicMock()
    with patch('backend.llm_gateway.api.get_gateway_job_runner', return_value=runner):
        created = authenticated_client.post('/api/v1/gateway/runs', json=_request_payload())
        assert created.status_code == 202
        created_body = created.get_json()
        job_id = created_body['job_id']
        assert created.headers['Location'].endswith(job_id)
        runner.submit.assert_called_once_with(job_id)

        replayed = authenticated_client.post('/api/v1/gateway/runs', json=_request_payload())
        assert replayed.status_code == 202
        assert replayed.headers['Idempotent-Replay'] == 'true'
        assert replayed.get_json()['job_id'] == job_id
        runner.submit.assert_called_once()

        conflict = authenticated_client.post(
            '/api/v1/gateway/runs',
            json=_request_payload('Changed governed work'),
        )
        assert conflict.status_code == 409
        assert conflict.get_json()['code'] == 'IDEMPOTENCY_CONFLICT'

        status = authenticated_client.get(f'/api/v1/gateway/runs/{job_id}')
        assert status.status_code == 200
        assert status.get_json()['status'] == 'queued'

        cancelled = authenticated_client.post(f'/api/v1/gateway/runs/{job_id}/cancel')
        assert cancelled.status_code == 202
        assert cancelled.get_json()['status'] == 'cancelled'
        runner.cancel.assert_called_once()

    with app.app_context():
        record = db.session.get(GatewayAsyncRun, uuid.UUID(job_id))
        assert record.request_ciphertext
        assert 'Run governed work' not in record.request_ciphertext
        decrypted = decrypt_payload(record.request_encryption, record.request_ciphertext)
        assert decrypted['messages'][0]['content'] == 'Run governed work'


def test_async_result_is_returned_only_from_authenticated_ciphertext(
    authenticated_client,
    app,
) -> None:
    runner = MagicMock()
    with patch('backend.llm_gateway.api.get_gateway_job_runner', return_value=runner):
        created = authenticated_client.post('/api/v1/gateway/runs', json=_request_payload())
    job_id = created.get_json()['job_id']

    with app.app_context():
        record = db.session.get(GatewayAsyncRun, uuid.UUID(job_id))
        encryption, ciphertext = encrypt_payload({
            'response': 'Validated governed answer',
            'request_id': record.request_id,
            'run_id': '00000000-0000-0000-0000-000000000888',
            'gateway_contract_version': 'dle-gateway.v1',
        })
        record.status = 'completed'
        record.response_encryption = encryption
        record.response_ciphertext = ciphertext
        record.response_status = 200
        record.completed_at = datetime.now(UTC)
        db.session.commit()

    result = authenticated_client.get(f'/api/v1/gateway/runs/{job_id}/result')
    assert result.status_code == 200
    assert result.get_json()['response'] == 'Validated governed answer'
    assert result.get_json()['job']['status'] == 'completed'


def test_large_async_result_is_verified_from_app_owned_object_store(
    authenticated_client,
    app,
) -> None:
    runner = MagicMock()
    with patch('backend.llm_gateway.api.get_gateway_job_runner', return_value=runner):
        created = authenticated_client.post('/api/v1/gateway/runs', json=_request_payload())
    job_id = created.get_json()['job_id']

    with app.app_context():
        record = db.session.get(GatewayAsyncRun, uuid.UUID(job_id))
        encryption, ciphertext = encrypt_payload({
            'response': 'Object-backed governed answer',
            'request_id': record.request_id,
        })
        encoded = ciphertext.encode('utf-8')
        record.status = 'completed'
        record.response_encryption = encryption
        record.response_storage = 'minio_ciphertext'
        record.response_object_bucket = 'gateway-results'
        record.response_object_key = f'jobs/{record.id}/result.enc'
        record.response_sha256 = hashlib.sha256(encoded).hexdigest()
        record.response_size_bytes = len(encoded)
        record.response_status = 200
        record.completed_at = datetime.now(UTC)
        db.session.commit()

    object_store = MagicMock()
    object_store.exists.return_value = True
    object_store.get.return_value = encoded
    with patch('backend.storage.get_object_store', return_value=object_store):
        result = authenticated_client.get(f'/api/v1/gateway/runs/{job_id}/result')

    assert result.status_code == 200
    assert result.get_json()['response'] == 'Object-backed governed answer'
    assert result.get_json()['job']['result_storage'] == 'minio_ciphertext'


def test_async_job_runner_does_not_replay_interrupted_provider_work(app) -> None:
    from tests.conftest import create_test_user
    from backend.llm_gateway.jobs import GatewayJobRunner

    with app.app_context():
        user_id = create_test_user(username='async-reconcile-owner')
        encryption, ciphertext = encrypt_payload(_request_payload())
        interrupted = GatewayAsyncRun(
            request_id='interrupted-request-123',
            idempotency_key='interrupted-key-123',
            request_sha256='a' * 64,
            user_id=user_id,
            status='running',
            virtual_model='dle-standard',
            request_encryption=encryption,
            request_ciphertext=ciphertext,
            expires_at=datetime.now(UTC),
        )
        db.session.add(interrupted)
        db.session.commit()
        interrupted_id = interrupted.id

    runner = GatewayJobRunner(app, max_workers=1)
    runner.start()
    runner.stop()

    with app.app_context():
        reconciled = db.session.get(GatewayAsyncRun, interrupted_id)
        assert reconciled.status == 'failed'
        assert reconciled.error_code == 'JOB_INTERRUPTED_RETRY_UNSAFE'
