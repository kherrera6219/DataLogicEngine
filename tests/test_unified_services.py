"""
Unit Tests for Unified System Services (UIDS, UNS, FROST, Trace)

Hardening verification for Truth Engine v7.4.
"""

import pytest
import uuid
from datetime import datetime
from core.system.unified_identity_service import UnifiedIdentityService
from core.system.unified_numbering_service import UnifiedNumberingService
from core.system.frost_service import FROSTService
from core.system.trace_service import TraceProvenanceService
from core.system.uae_models import UnifiedArtifactEnvelope, ConfidenceVector
from core.coordinate_system import UnifiedCoordinate

@pytest.fixture
def uids():
    return UnifiedIdentityService()

@pytest.fixture
def uns():
    return UnifiedNumberingService()

@pytest.fixture
def frost():
    return FROSTService()

@pytest.fixture
def trace():
    return TraceProvenanceService()

# --- UIDS Tests ---
def test_uids_registration(uids):
    ukgid = uids.register_entity("AV Sensor", "hardware", {"part_no": "X100"})
    assert ukgid.startswith("ukg:hardware:")
    
    resolved = uids.resolve_ukgid("part_no", "X100")
    assert resolved == ukgid

# --- UNS Tests ---
def test_uns_path_resolution(uns):
    path = uns.format_path(1, [1, 13, 2])
    assert path == "A01.1.13.2"
    
    label = uns.resolve_label("A01.1.13.2")
    assert "Pillar" in label or label == "A01.1.13.2"

# --- FROST Tests ---
def test_frost_snapshot_cycle(frost):
    state = {"key": "value"}
    snap_id = frost.snapshot(state)
    assert snap_id is not None
    
    retrieved = frost.get_snapshot(snap_id)
    assert retrieved == state
    
    # Delta check
    state["key"] = "new_value"
    diff = frost.diff(snap_id, state)
    assert diff["key"] == "new_value"

# --- Trace Tests ---
def test_trace_registration(trace):
    uae = UnifiedArtifactEnvelope(
        artifact_id="test_art",
        run_id="test_run",
        coord17=UnifiedCoordinate(),
        payload_type="test",
        payload={"data": 123},
        confidence_vector=ConfidenceVector(overall=0.9)
    )
    
    trace.register_artifact(uae)
    chain = trace.get_provenance_chain("test_art")
    assert len(chain) == 1
    assert chain[0].artifact_id == "test_art"

# --- Schema Enforcement ---
def test_uae_schema():
    with pytest.raises(Exception):
        # Missing required artifact_id
        UnifiedArtifactEnvelope(payload_type="test", payload={})
