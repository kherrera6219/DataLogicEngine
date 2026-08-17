from __future__ import annotations

import sys
from datetime import timedelta
from types import SimpleNamespace

import pytest


class _Redis:
    def __init__(self):
        self.values = {}
        self.sorted = {}
        self.events = []

    def ping(self):
        return True

    def zadd(self, key, values, nx=False):
        self.sorted.setdefault(key, {}).update(values)

    def zrem(self, key, value):
        self.sorted.get(key, {}).pop(value, None)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        return int(key in self.values)

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
        return len(keys)

    def eval(self, _script, _count, key, owner):
        if self.values.get(key) == owner:
            self.values.pop(key)
            return 1
        return 0

    def pipeline(self, transaction=True):
        return self

    def xadd(self, key, event, **_values):
        self.events.append((key, event))
        return "1-0"

    def execute(self):
        return []


def test_redis_simulation_coordination_lifecycle(monkeypatch):
    from backend.simulation.job_coordination import RedisSimulationJobCoordinator

    redis = _Redis()
    coordinator = RedisSimulationJobCoordinator(redis, prefix=" jobs ")
    assert coordinator.queue_key == "jobs:queue"
    assert coordinator.events_key == "jobs:events"
    coordinator.enqueue("sim-1")
    assert coordinator.get_state("sim-1")["state"] == "queued"
    assert coordinator.acquire("sim-1", worker_id="worker", lease_seconds=1) is True
    assert coordinator.acquire("sim-1", worker_id="other", lease_seconds=1) is False
    assert coordinator.release("sim-1", worker_id="other") is False
    assert coordinator.release("sim-1", worker_id="worker") is True

    coordinator.request_control("sim-1", " PAUSE ")
    assert coordinator.requested_control("sim-1") == "pause"
    coordinator.request_control("sim-1", "cancel")
    assert coordinator.requested_control("sim-1") == "cancel"
    coordinator.clear_controls("sim-1")
    assert coordinator.requested_control("sim-1") is None
    with pytest.raises(ValueError, match="unsupported"):
        coordinator.request_control("sim-1", "resume")
    with pytest.raises(ValueError, match="Simulation id"):
        coordinator._key(" ", "state")

    fake_module = SimpleNamespace(Redis=SimpleNamespace(from_url=lambda *_args, **_kwargs: redis))
    monkeypatch.setitem(sys.modules, "redis", fake_module)
    assert RedisSimulationJobCoordinator.from_url("redis://local").redis is redis


def test_redis_simulation_coordination_fail_closed(monkeypatch):
    from backend.simulation.job_coordination import (
        RedisSimulationJobCoordinator,
        SimulationJobCoordinatorUnavailable,
    )

    with pytest.raises(SimulationJobCoordinatorUnavailable):
        RedisSimulationJobCoordinator(None)

    class Broken:
        def __getattr__(self, _name):
            raise RuntimeError("redis offline")

    coordinator = RedisSimulationJobCoordinator(Broken())
    operations = [
        lambda: coordinator.enqueue("sim"),
        lambda: coordinator.acquire("sim", worker_id="w", lease_seconds=5),
        lambda: coordinator.release("sim", worker_id="w"),
        lambda: coordinator.record_state("sim", "running", 1, 2),
        lambda: coordinator.get_state("sim"),
        lambda: coordinator.request_control("sim", "pause"),
        lambda: coordinator.requested_control("sim"),
        lambda: coordinator.clear_controls("sim"),
    ]
    for operation in operations:
        with pytest.raises(SimulationJobCoordinatorUnavailable):
            operation()

    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=SimpleNamespace(from_url=lambda *_a, **_k: Broken())))
    with pytest.raises(SimulationJobCoordinatorUnavailable):
        RedisSimulationJobCoordinator.from_url("redis://offline")


class _MetricQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter_by(self, **_values):
        return self

    def filter(self, *_values):
        return self

    def order_by(self, *_values):
        return self

    def limit(self, _value):
        return self

    def all(self):
        return self.rows


class _MetricSession:
    def __init__(self, rows=(), fail=False):
        self.rows = list(rows)
        self.fail = fail
        self.added = []

    def add(self, value):
        if self.fail:
            raise RuntimeError("db offline")
        self.added.append(value)

    def commit(self):
        return None

    def query(self, _model):
        if self.fail:
            raise RuntimeError("db offline")
        return _MetricQuery(self.rows)


def test_metrics_tracker_records_aggregates_breakdowns_and_requests():
    from backend.truth_engine.truth_memory.metrics import MetricsTracker

    tracker = MetricsTracker()
    first = tracker.record("latency_ms", 10, "s1", "standard", "model", {"route": "chat"})
    tracker.record("latency_ms", 30, "s2", "deep")
    tracker.record("custom", 5)
    assert first["metric_unit"] == "ms"
    assert len(tracker.get_metric("latency_ms", tier="standard")) == 1
    assert tracker.get_aggregate("latency_ms")["avg"] == 20
    assert tracker.get_aggregate("missing")["count"] == 0
    assert tracker.get_summary()["aggregates"]["custom"]["sum"] == 5
    assert tracker.get_tier_breakdown("latency_ms")["standard"]["avg"] == 10

    tracker.record_request("s3", "standard", 50, tokens=100, confidence=0.8, success=False)
    assert tracker.get_aggregate("request_count")["count"] == 1
    assert tracker.get_aggregate("error_count")["count"] == 1

    for index in range(1001):
        tracker.record("trimmed", float(index))
    assert len(tracker.in_memory_metrics["trimmed"]) == 500


def test_metrics_tracker_database_success_and_failure(monkeypatch):
    import models
    from backend.truth_engine.truth_memory.metrics import MetricsTracker

    class MetricColumn:
        def desc(self):
            return self

        def __ge__(self, _value):
            return self

    class TruthMetric:
        timestamp = MetricColumn()

        def __init__(self, **values):
            self.values = values

        def to_dict(self):
            return self.values

    monkeypatch.setattr(models, "TruthMetric", TruthMetric)
    stored = TruthMetric(metric_name="latency_ms", metric_value=4)
    session = _MetricSession([stored])
    tracker = MetricsTracker(session)
    tracker.record("latency_ms", 4, tier="standard")
    assert session.added
    assert tracker.get_metric("latency_ms", timedelta(hours=1), tier="standard")[0]["metric_value"] == 4

    broken = MetricsTracker(_MetricSession(fail=True))
    broken.record("latency_ms", 1)
    assert broken.get_metric("latency_ms") == []


def test_soak_collection_growth_and_filesystem_helpers(tmp_path, monkeypatch):
    import backend.observability.soak as module

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "app.log").write_bytes(b"12345")
    bundles = tmp_path / "support-bundles"
    bundles.mkdir()
    (bundles / "support_bundle_one.zip").write_bytes(b"x")
    (bundles / "ignore.txt").write_bytes(b"x")

    fake_process = SimpleNamespace(
        memory_info=lambda: SimpleNamespace(rss=100),
        num_threads=lambda: 3,
        num_handles=lambda: 4,
        children=lambda recursive=True: [object()],
    )
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(Process=lambda: fake_process))
    sample = module.collect_resource_sample(tmp_path)
    assert sample["rss_bytes"] == 100 and sample["log_bytes"] == 5
    assert sample["support_archive_count"] == 1

    profile = module.SoakProfile("test", 10, 1, 20, 2, 2, 1, 20, 2)
    second = {**sample, "rss_bytes": 110, "thread_count": 4, "handle_count": 5, "log_bytes": 10}
    qualified = module.evaluate_soak(profile, [sample, second], observed_duration_seconds=10, installed_application=True)
    assert qualified["qualifies_cp13_e"] is True
    failed = module.evaluate_soak(profile, [{**sample, "sample_error": "error"}], observed_duration_seconds=1, installed_application=False)
    assert failed["status"] == "engineering_observation_only"
    assert module._directory_size(tmp_path / "missing") == 0
    assert module._support_archive_count(tmp_path / "missing") == 0


def test_soak_native_and_proc_measurements(tmp_path, monkeypatch):
    import backend.observability.soak as module

    monkeypatch.setattr(module.platform, "system", lambda: "Other")
    monkeypatch.setattr(module.Path, "is_dir", lambda self: False if str(self) == "/proc" else self.exists())
    monkeypatch.setattr(module.os, "sysconf", lambda _name: 4096, raising=False)
    fallback = module._native_process_measurements()
    assert fallback["thread_count"] >= 1

    proc = tmp_path / "proc"
    (proc / "self" / "fd").mkdir(parents=True)
    (proc / "self" / "statm").write_text("10 2", encoding="ascii")
    (proc / "self" / "status").write_text("Threads:\t4\n", encoding="ascii")
    (proc / "self" / "fd" / "1").write_text("", encoding="ascii")
    (proc / "123").mkdir()
    (proc / "123" / "stat").write_text("123 x x 999999", encoding="ascii")
    (proc / "bad").mkdir()
    measured = module._proc_process_measurements(proc)
    assert measured["thread_count"] == 4 and measured["handle_count"] == 1
