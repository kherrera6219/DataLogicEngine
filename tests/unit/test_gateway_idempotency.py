"""Phase 8 durable gateway idempotency authority tests."""

from __future__ import annotations

from tests.conftest import create_test_user
from extensions import db
from models import ExternalAPIKey, GatewayIdempotencyRecord

from backend.llm_gateway.idempotency import (
    begin_idempotent_request,
    complete_idempotent_request,
    request_fingerprint,
)


def test_request_fingerprint_ignores_retry_transport_ids_only() -> None:
    base = {
        "messages": [{"role": "user", "content": "hello"}],
        "virtual_model": "dle-standard",
        "request_id": "request-123",
        "idempotency_key": "retry-key-123",
    }
    retried = {**base, "request_id": "request-456", "idempotency_key": "retry-key-456"}
    changed = {
        **retried,
        "messages": [{"role": "user", "content": "changed"}],
    }
    assert request_fingerprint(base) == request_fingerprint(retried)
    assert request_fingerprint(base) != request_fingerprint(changed)


def test_durable_idempotency_create_conflict_complete_and_replay(app) -> None:
    with app.app_context():
        user_id = create_test_user(username="idempotency-owner")
        client = ExternalAPIKey(
            name="idempotency-client",
            key_prefix="ukg_12345678",
            key_hash="a" * 64,
            user_id=user_id,
            permissions={"scopes": ["chat"]},
        )
        db.session.add(client)
        db.session.commit()
        payload = {
            "messages": [{"role": "user", "content": "hello"}],
            "virtual_model": "dle-standard",
        }

        created = begin_idempotent_request(
            db.session,
            GatewayIdempotencyRecord,
            api_key_id=client.id,
            idempotency_key="retry-key-123",
            request_id="request-123",
            payload=payload,
        )
        assert created.disposition == "created"

        pending = begin_idempotent_request(
            db.session,
            GatewayIdempotencyRecord,
            api_key_id=client.id,
            idempotency_key="retry-key-123",
            request_id="request-456",
            payload=payload,
        )
        assert pending.disposition == "in_progress"

        conflict = begin_idempotent_request(
            db.session,
            GatewayIdempotencyRecord,
            api_key_id=client.id,
            idempotency_key="retry-key-123",
            request_id="request-789",
            payload={**payload, "virtual_model": "dle-enhanced"},
        )
        assert conflict.disposition == "conflict"

        complete_idempotent_request(
            db.session,
            created.record,
            response_payload={
                "response": "governed result",
                "run_id": "00000000-0000-0000-0000-000000000111",
            },
            response_status=200,
            run_id="00000000-0000-0000-0000-000000000111",
        )
        replay = begin_idempotent_request(
            db.session,
            GatewayIdempotencyRecord,
            api_key_id=client.id,
            idempotency_key="retry-key-123",
            request_id="request-new",
            payload=payload,
        )
        assert replay.disposition == "replay"
        assert replay.record.response_status == 200
        assert replay.record.response_payload["response"] == "governed result"
