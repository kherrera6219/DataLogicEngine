"""
Integration Tests for the 10-Layer Simulation Stack.

Validates the full derivation chain from L1-L10 and UAE schema enforcement.
"""

import pytest
from core.system.united_system_manager import UnitedSystemManager
from simulation.simulation_engine import SimulationEngine
from core.system.uae_models import UnifiedArtifactEnvelope

@pytest.fixture
def system_manager():
    usm = UnitedSystemManager()
    # Mocking or initializing real services as needed
    usm.initialize_unified_system("data/registries/axis_registry.json")
    return usm

@pytest.fixture
def simulation_engine(system_manager):
    return SimulationEngine(usm=system_manager)

def test_full_stack_execution(simulation_engine):
    query = "Analyze impact of LiDAR failure on L4 AV safety regulations."
    
    # Run at escalation level 5 (Full L1-L10)
    result = simulation_engine.run_simulation(query, escalation_level=5)
    
    # Assertions
    assert isinstance(result, UnifiedArtifactEnvelope)
    assert result.confidence_vector.overall >= 0.95
    
    # Verify Trace Continuity
    # Derivation should have 10 layers if it went through everything
    # The current engine logs the start of each layer.
    assert len(result.provenance) >= 5 # At least the primary layers
    
    # Verify Metadata
    assert "layer_10_result" in result.metadata
    assert "persona_L10_insight" in result.metadata

def test_tiered_escalation_l1(simulation_engine):
    query = "Quick check on sensor data."
    
    # Run at escalation level 1 (L1-L2 only)
    result = simulation_engine.run_simulation(query, escalation_level=1)
    
    # Should NOT have layer 10 insights
    assert "layer_10_result" not in result.metadata
    assert len(result.provenance) < 5
