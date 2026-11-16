"""Optional tracking cannot be pointed at a network service or UNC path."""

import pytest

from backend.dmrf.mlflow_tracker import DMRFMLflowTracker
from backend.truth_engine.truth_memory.mlflow_tracker import TruthMemoryMLflowTracker
from core.security.egress_guard import EgressDenied


@pytest.mark.parametrize("tracker", [DMRFMLflowTracker, TruthMemoryMLflowTracker])
@pytest.mark.parametrize(
    "uri",
    [
        "https://outside.example/tracking",
        "http://127.0.0.1:5001",
        "databricks://profile",
        "s3://bucket/runs",
        "file://outside.example/share",
        "file:////outside.example/share",
        "file:/%2foutside.example/share",
        "//outside.example/share",
        r"\\outside.example\share",
    ],
)
def test_network_tracking_is_denied_before_recording(tracker, uri):
    with pytest.raises(EgressDenied):
        tracker(tracking_uri=uri)


@pytest.mark.parametrize("tracker", [DMRFMLflowTracker, TruthMemoryMLflowTracker])
@pytest.mark.parametrize(
    "uri", ["./mlruns", "/tmp/mlruns", "file:///tmp/mlruns", r"C:\mlruns"]
)
def test_local_tracking_configuration_is_accepted(tracker, uri):
    assert tracker(tracking_uri=uri).tracking_uri == uri


@pytest.mark.parametrize("tracker", [DMRFMLflowTracker, TruthMemoryMLflowTracker])
def test_remote_environment_configuration_is_denied(monkeypatch, tracker):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://outside.example")
    with pytest.raises(EgressDenied):
        tracker()


@pytest.mark.parametrize(
    ("tracker", "method"),
    [(DMRFMLflowTracker, "record"), (TruthMemoryMLflowTracker, "record_session")],
)
def test_remote_tracking_changes_are_denied_before_recording(tracker, method):
    instance = tracker(tracking_uri="./mlruns")
    instance.tracking_uri = "https://outside.example"
    with pytest.raises(EgressDenied):
        getattr(instance, method)({})
