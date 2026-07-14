from __future__ import annotations

import json

import pytest

from backend.mcp_server.live_state import MCPLiveStateUnavailable, RedisMCPLiveState


class _Pipeline:
    def __init__(self, owner):
        self.owner = owner

    def set(self, key, value, **kwargs):
        self.owner.calls.append(("set", key, value, kwargs))
        return self

    def xadd(self, key, value, **kwargs):
        self.owner.calls.append(("xadd", key, value, kwargs))
        return self

    def execute(self):
        if self.owner.fail:
            raise RuntimeError("redis unavailable")
        self.owner.calls.append(("execute",))


class _Redis:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = []

    def pipeline(self, **kwargs):
        self.calls.append(("pipeline", kwargs))
        return _Pipeline(self)


def test_lifecycle_and_execution_events_are_content_free_and_bounded():
    redis = _Redis()
    live = RedisMCPLiveState(redis)

    live.record_lifecycle("server-1", "started", "healthy")
    live.record_execution("server-1", "execution-1", "completed")

    set_payloads = [json.loads(call[2]) for call in redis.calls if call[0] == "set"]
    assert set_payloads[0] == {
        "event_type": "started",
        "kind": "lifecycle",
        "server_id": "server-1",
        "status": "healthy",
        "updated_at_epoch": set_payloads[0]["updated_at_epoch"],
    }
    assert set_payloads[1]["execution_id"] == "execution-1"
    assert all("content" not in payload and "arguments" not in payload for payload in set_payloads)
    xadds = [call for call in redis.calls if call[0] == "xadd"]
    assert all(call[3]["maxlen"] == 10_000 for call in xadds)


def test_live_state_fails_closed_when_redis_update_fails():
    live = RedisMCPLiveState(_Redis(fail=True))

    with pytest.raises(MCPLiveStateUnavailable):
        live.record_lifecycle("server-1", "started", "healthy")
