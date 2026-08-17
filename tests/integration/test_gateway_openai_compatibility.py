"""Bounded OpenAI compatibility facade tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.llm_gateway.gateway import GatewayResponse


def _client_key(authenticated_client) -> str:
    response = authenticated_client.post(
        '/api/v1/admin/gateway/api-keys',
        json={
            'name': 'openai-compat-client',
            'scopes': ['chat', 'stream', 'models:read'],
        },
    )
    assert response.status_code == 201
    return response.get_json()['api_key']


def test_openai_models_exposes_virtual_models_not_provider_credentials(authenticated_client) -> None:
    key = _client_key(authenticated_client)
    response = authenticated_client.get(
        '/v1/models',
        headers={'Authorization': f'Bearer {key}'},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert {item['id'] for item in body['data']} == {
        'dle-standard',
        'dle-enhanced',
        'dle-local-review',
    }
    assert body['dle']['provider_credentials_exposed'] is False


def test_openai_chat_adapts_to_the_governed_contract_and_is_idempotent(
    authenticated_client,
) -> None:
    key = _client_key(authenticated_client)
    governed = GatewayResponse(
        content='Governed compatibility answer',
        run_id='00000000-0000-0000-0000-000000000777',
        provider_used='openai',
        model_used='gpt-5.6-sol',
        usage={'prompt_tokens': 10, 'completion_tokens': 5},
        confidence_measurement={'status': 'measured', 'value': 0.9},
    )
    headers = {
        'Authorization': f'Bearer {key}',
        'Idempotency-Key': 'compat-retry-key-123',
        'X-Request-ID': 'compat-request-123',
    }
    payload = {
        'model': 'dle-standard',
        'messages': [{'role': 'user', 'content': 'hello'}],
    }
    with patch(
        'backend.llm_gateway.api.LLMGateway.process',
        new=AsyncMock(return_value=governed),
    ) as process:
        response = authenticated_client.post('/v1/chat/completions', headers=headers, json=payload)
        replay = authenticated_client.post('/v1/chat/completions', headers=headers, json=payload)

    assert response.status_code == 200
    body = response.get_json()
    assert body['object'] == 'chat.completion'
    assert body['model'] == 'dle-standard'
    assert body['choices'][0]['message']['content'] == 'Governed compatibility answer'
    assert body['dle']['run_id'] == governed.run_id
    assert body['dle']['provider_used'] == 'openai'
    assert replay.headers['Idempotent-Replay'] == 'true'
    assert process.await_count == 1


def test_openai_chat_rejects_unsupported_fields_instead_of_ignoring_them(
    authenticated_client,
) -> None:
    key = _client_key(authenticated_client)
    response = authenticated_client.post(
        '/v1/chat/completions',
        headers={'Authorization': f'Bearer {key}'},
        json={
            'model': 'dle-standard',
            'messages': [{'role': 'user', 'content': 'hello'}],
            'stop': ['END'],
        },
    )
    assert response.status_code == 422
    errors = response.get_json()['error']['details']['validation_errors']
    assert 'stop' in errors
