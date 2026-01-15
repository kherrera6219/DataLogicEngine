"""
Unit Tests for Persona Scaling System

Tests the PersonaSufficiencyTool, PodOrchestrator, and related components.
"""

import pytest
import uuid
from datetime import datetime, UTC
from typing import Dict, Any

# Import the modules to test
from quad_persona.pod_models import (
    PodType,
    ExpandedPersona,
    SubsystemProfile,
    SufficiencySignals,
    ExpansionPlan,
    ScalingDecision,
    PodState,
    CrossPodConflict,
    ScalingOrchestrationState
)
from quad_persona.persona_scaling import (
    PersonaSufficiencyTool,
    HighAssuranceDetector,
    SubsystemDetector,
    DEFENSE_SUBSYSTEM_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES
)
from quad_persona.pod_orchestrator import (
    PodOrchestrator,
    PersonaBuilder,
    PodSynthesizer,
    CrossPodDeconfliction
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def simple_query():
    """A simple query that should NOT trigger expansion."""
    return "What is the capital of France?"


@pytest.fixture
def complex_query():
    """A complex defense query that SHOULD trigger expansion."""
    return "Plan an F-22 modernization: new radar modes, EW updates, new mission computer, and secure datalinks."


@pytest.fixture
def base_context():
    """Basic query context."""
    return {
        "query_id": str(uuid.uuid4()),
        "domain": "general",
        "sector": "technology",
        "location": "US"
    }


@pytest.fixture
def defense_context():
    """Defense domain context."""
    return {
        "query_id": str(uuid.uuid4()),
        "domain": "defense",
        "sector": "aerospace",
        "location": "US"
    }


@pytest.fixture
def base_axis_vector():
    """Basic 17-axis vector."""
    return {
        1: "PL10",  # Information Technology
        2: "541512",  # Technology sector
        8: True,  # Knowledge Expert
        9: True,  # Sector Expert
        10: True,  # Regulatory Expert
        11: True  # Compliance Expert
    }


@pytest.fixture
def defense_axis_vector():
    """Defense domain axis vector."""
    return {
        1: "PL16",  # Security and Defense
        2: "336411",  # Aircraft Manufacturing
        3: True,  # Honeycomb cross-links
        6: True,  # Octopus regulatory
        7: True,  # Spiderweb compliance
        8: True,
        9: True,
        10: True,
        11: True,
        12: "US"
    }


@pytest.fixture
def low_confidence_persona_results():
    """Persona results with low coverage/high conflict."""
    return {
        "knowledge": {"response": "Technical analysis...", "confidence": 0.65, "has_gaps": True},
        "sector": {"response": "Industry view...", "confidence": 0.70, "has_gaps": True},
        "regulatory": {"response": "Regulatory concerns...", "confidence": 0.85},
        "compliance": {"response": "Compliance check...", "confidence": 0.80}
    }


@pytest.fixture
def high_confidence_persona_results():
    """Persona results with good coverage."""
    return {
        "knowledge": {"response": "Technical analysis...", "confidence": 0.92},
        "sector": {"response": "Industry view...", "confidence": 0.88},
        "regulatory": {"response": "Regulatory analysis...", "confidence": 0.90},
        "compliance": {"response": "Compliance check...", "confidence": 0.91}
    }


# =============================================================================
# Pod Models Tests
# =============================================================================

class TestPodType:
    """Tests for PodType enum."""
    
    def test_from_axis(self):
        """Test creating PodType from axis number."""
        assert PodType.from_axis(8) == PodType.KNOWLEDGE
        assert PodType.from_axis(9) == PodType.SECTOR
        assert PodType.from_axis(10) == PodType.REGULATORY
        assert PodType.from_axis(11) == PodType.COMPLIANCE
        assert PodType.from_axis(99) is None
    
    def test_axis_number(self):
        """Test getting axis number from PodType."""
        assert PodType.KNOWLEDGE.axis_number == 8
        assert PodType.SECTOR.axis_number == 9
        assert PodType.REGULATORY.axis_number == 10
        assert PodType.COMPLIANCE.axis_number == 11
    
    def test_max_personas(self):
        """Test max persona caps."""
        assert PodType.KNOWLEDGE.max_personas == 6
        assert PodType.SECTOR.max_personas == 6
        assert PodType.REGULATORY.max_personas == 3
        assert PodType.COMPLIANCE.max_personas == 3


class TestExpandedPersona:
    """Tests for ExpandedPersona."""
    
    def test_create_persona(self):
        """Test creating an expanded persona."""
        persona = ExpandedPersona(
            persona_id="test_persona_1",
            pod_type=PodType.KNOWLEDGE,
            name="Radar SME",
            description="Radar systems expert"
        )
        
        assert persona.persona_id == "test_persona_1"
        assert persona.pod_type == PodType.KNOWLEDGE
        assert persona.axis_number == 8
        assert persona.persona_type == "knowledge"
        assert persona.is_active is True
    
    def test_set_component(self):
        """Test setting persona components."""
        persona = ExpandedPersona(
            persona_id="test",
            pod_type=PodType.KNOWLEDGE,
            name="Test",
            description="Test"
        )
        
        result = persona.set_component("job_role", {"title": "Engineer"})
        assert result is True
        assert persona.get_component("job_role") == {"title": "Engineer"}
        
        # Invalid component
        result = persona.set_component("invalid", {})
        assert result is False
    
    def test_to_dict(self):
        """Test serialization."""
        persona = ExpandedPersona(
            persona_id="test",
            pod_type=PodType.SECTOR,
            name="Test Persona",
            description="Description"
        )
        
        data = persona.to_dict()
        assert data["persona_id"] == "test"
        assert data["pod_type"] == "sector"
        assert "components" in data


class TestSufficiencySignals:
    """Tests for SufficiencySignals."""
    
    def test_exceeds_thresholds(self):
        """Test threshold checking."""
        signals = SufficiencySignals(
            complexity_score=70,
            stakes_score=30,
            conflict_score=0.1,
            coverage_score=0.9
        )
        
        thresholds = {"complexity": 60, "stakes": 40, "conflict": 0.2, "coverage": 0.85}
        
        # Complexity exceeds threshold
        assert signals.exceeds_thresholds(thresholds) is True
    
    def test_get_expansion_reasons(self):
        """Test getting expansion reasons."""
        signals = SufficiencySignals(
            complexity_score=70,
            stakes_score=50,
            is_defense_domain=True
        )
        
        thresholds = {"complexity": 60, "stakes": 40, "conflict": 0.2, "coverage": 0.85}
        reasons = signals.get_expansion_reasons(thresholds)
        
        assert len(reasons) >= 2
        assert any("complexity" in r.lower() for r in reasons)
        assert any("defense" in r.lower() for r in reasons)


class TestPodState:
    """Tests for PodState."""
    
    def test_add_persona(self):
        """Test adding personas to pod."""
        pod = PodState(pod_type=PodType.KNOWLEDGE)
        
        persona = ExpandedPersona(
            persona_id="p1",
            pod_type=PodType.KNOWLEDGE,
            name="Test",
            description="Test"
        )
        
        result = pod.add_persona(persona)
        assert result is True
        assert pod.persona_count == 1
    
    def test_add_wrong_type(self):
        """Test adding wrong type persona fails."""
        pod = PodState(pod_type=PodType.KNOWLEDGE)
        
        persona = ExpandedPersona(
            persona_id="p1",
            pod_type=PodType.SECTOR,  # Wrong type
            name="Test",
            description="Test"
        )
        
        result = pod.add_persona(persona)
        assert result is False
    
    def test_capacity_limit(self):
        """Test pod capacity limits."""
        pod = PodState(pod_type=PodType.REGULATORY)  # Max 3
        
        for i in range(5):
            persona = ExpandedPersona(
                persona_id=f"p{i}",
                pod_type=PodType.REGULATORY,
                name=f"Test {i}",
                description="Test"
            )
            pod.add_persona(persona)
        
        # Should only have 3
        assert pod.persona_count == 3


# =============================================================================
# High Assurance Detection Tests
# =============================================================================

class TestHighAssuranceDetector:
    """Tests for high-assurance detection."""
    
    def test_detect_defense(self, complex_query):
        """Test defense domain detection."""
        result = HighAssuranceDetector.detect(complex_query)
        
        assert result["is_high_assurance"] is True
        assert result["is_defense_domain"] is True
    
    def test_detect_simple(self, simple_query):
        """Test non-defense query."""
        result = HighAssuranceDetector.detect(simple_query)
        
        assert result["is_high_assurance"] is False
        assert result["is_defense_domain"] is False
    
    def test_detect_safety_critical(self):
        """Test safety-critical detection."""
        query = "Ensure DO-178C compliance for flight safety system"
        result = HighAssuranceDetector.detect(query)
        
        assert result["is_high_assurance"] is True
        assert result["has_safety_critical"] is True
    
    def test_detect_export_control(self):
        """Test export control detection."""
        query = "Verify ITAR classification for export license"
        result = HighAssuranceDetector.detect(query)
        
        assert result["is_high_assurance"] is True
        assert result["has_export_control"] is True


# =============================================================================
# Subsystem Detection Tests
# =============================================================================

class TestSubsystemDetector:
    """Tests for subsystem detection."""
    
    def test_detect_defense_subsystems(self, complex_query):
        """Test detecting subsystems in complex query."""
        result = SubsystemDetector.detect_subsystems(complex_query)
        
        # Should detect radar, EW, avionics, datalink
        assert len(result["knowledge"]) >= 3
        
        # Check specific subsystems
        subsystem_ids = [p.subsystem_id for p in result["knowledge"]]
        assert "radar_sme" in subsystem_ids
        assert "ew_sme" in subsystem_ids
    
    def test_detect_nothing(self, simple_query):
        """Test no subsystems in simple query."""
        result = SubsystemDetector.detect_subsystems(simple_query)
        
        assert len(result["knowledge"]) == 0
        assert len(result["sector"]) == 0


# =============================================================================
# Persona Sufficiency Tool Tests
# =============================================================================

class TestPersonaSufficiencyTool:
    """Tests for PersonaSufficiencyTool."""
    
    def test_quad_only_decision(
        self,
        simple_query,
        base_context,
        base_axis_vector,
        high_confidence_persona_results
    ):
        """Test that simple queries stay quad-only."""
        tool = PersonaSufficiencyTool()
        
        decision = tool.evaluate(
            query=simple_query,
            context=base_context,
            axis_vector=base_axis_vector,
            persona_results=high_confidence_persona_results
        )
        
        assert decision.mode == "quad_only"
        assert decision.should_expand is False
        assert decision.expansion_plan is None
    
    def test_expansion_decision(
        self,
        complex_query,
        defense_context,
        defense_axis_vector,
        low_confidence_persona_results
    ):
        """Test that complex queries trigger expansion."""
        tool = PersonaSufficiencyTool()
        
        decision = tool.evaluate(
            query=complex_query,
            context=defense_context,
            axis_vector=defense_axis_vector,
            persona_results=low_confidence_persona_results
        )
        
        assert decision.mode == "expanded_committee"
        assert decision.should_expand is True
        assert decision.expansion_plan is not None
        assert decision.threshold_mode == "high_assurance"
    
    def test_spawn_counts(
        self,
        complex_query,
        defense_context,
        defense_axis_vector,
        low_confidence_persona_results
    ):
        """Test spawn counts are calculated correctly."""
        tool = PersonaSufficiencyTool()
        
        decision = tool.evaluate(
            query=complex_query,
            context=defense_context,
            axis_vector=defense_axis_vector,
            persona_results=low_confidence_persona_results
        )
        
        plan = decision.expansion_plan
        assert plan is not None
        
        # Should spawn knowledge personas for detected subsystems
        assert plan.spawn_counts["knowledge"] >= 3
        
        # Check caps are respected
        assert plan.spawn_counts["knowledge"] <= 6
        assert plan.spawn_counts["regulatory"] <= 3


# =============================================================================
# Persona Builder Tests
# =============================================================================

class TestPersonaBuilder:
    """Tests for PersonaBuilder."""
    
    def test_build_from_profile(self):
        """Test building persona from subsystem profile."""
        persona = PersonaBuilder.build_persona(
            pod_type=PodType.KNOWLEDGE,
            subsystem_id="radar",
            context={}
        )
        
        assert persona is not None
        assert persona.name == "Radar Systems SME"
        assert persona.pod_type == PodType.KNOWLEDGE
        assert persona.subsystem_profile is not None
    
    def test_build_default(self):
        """Test building default persona."""
        persona = PersonaBuilder.build_default_persona(
            pod_type=PodType.SECTOR,
            index=0,
            context={}
        )
        
        assert persona is not None
        assert persona.pod_type == PodType.SECTOR
        assert persona.subsystem_profile is None
    
    def test_invalid_subsystem(self):
        """Test unknown subsystem returns None."""
        persona = PersonaBuilder.build_persona(
            pod_type=PodType.KNOWLEDGE,
            subsystem_id="nonexistent",
            context={}
        )
        
        assert persona is None


# =============================================================================
# Pod Orchestrator Tests
# =============================================================================

class TestPodOrchestrator:
    """Tests for PodOrchestrator."""
    
    def test_quad_only_orchestration(
        self,
        simple_query,
        base_context,
        high_confidence_persona_results
    ):
        """Test orchestration in quad-only mode."""
        orchestrator = PodOrchestrator()
        
        decision = ScalingDecision(mode="quad_only")
        
        state = orchestrator.orchestrate(
            query=simple_query,
            context=base_context,
            scaling_decision=decision,
            base_persona_results=high_confidence_persona_results
        )
        
        assert state.status == "completed"
        assert len(state.pods) == 0  # No pods spawned
    
    def test_expanded_orchestration(
        self,
        complex_query,
        defense_context
    ):
        """Test orchestration with expansion."""
        orchestrator = PodOrchestrator()
        
        # Create expansion decision
        expansion_plan = ExpansionPlan(
            spawn_counts={
                "knowledge": 3,
                "sector": 2,
                "regulatory": 1,
                "compliance": 1
            },
            subsystems_to_spawn={
                "knowledge": ["radar", "ew", "avionics"],
                "sector": ["program", "sustainment"],
                "regulatory": ["export"],
                "compliance": ["rmf"]
            }
        )
        
        signals = SufficiencySignals(is_high_assurance=True)
        decision = ScalingDecision(
            mode="expanded_committee",
            signals=signals,
            expansion_plan=expansion_plan
        )
        
        state = orchestrator.orchestrate(
            query=complex_query,
            context=defense_context,
            scaling_decision=decision,
            base_persona_results={}
        )
        
        assert state.status == "completed"
        assert len(state.pods) > 0
        assert state.final_synthesis != ""


# =============================================================================
# Cross-Pod Deconfliction Tests
# =============================================================================

class TestCrossPodDeconfliction:
    """Tests for cross-pod deconfliction."""
    
    def test_detect_conflicts(self):
        """Test conflict detection between pods."""
        deconfliction = CrossPodDeconfliction()
        
        # Create pods with confidence discrepancy
        k_pod = PodState(pod_type=PodType.KNOWLEDGE)
        k_pod.collective_confidence = 0.95
        
        r_pod = PodState(pod_type=PodType.REGULATORY)
        r_pod.collective_confidence = 0.60
        
        pods = {
            "knowledge": k_pod,
            "regulatory": r_pod
        }
        
        conflicts, all_resolved = deconfliction.deconflict(pods)
        
        # Should detect constraint uncertainty
        assert len(conflicts) > 0
    
    def test_resolve_low_severity(self):
        """Test automatic resolution of low severity conflicts."""
        deconfliction = CrossPodDeconfliction()
        
        conflict = CrossPodConflict(
            source_pod=PodType.KNOWLEDGE,
            target_pod=PodType.SECTOR,
            conflict_type="alignment_gap",
            severity="low"
        )
        
        k_pod = PodState(pod_type=PodType.KNOWLEDGE)
        k_pod.collective_confidence = 0.9
        
        s_pod = PodState(pod_type=PodType.SECTOR)
        s_pod.collective_confidence = 0.8
        
        pods = {"knowledge": k_pod, "sector": s_pod}
        
        resolved = deconfliction._try_resolve(conflict, pods)
        
        assert resolved is True
        assert conflict.resolved is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestPersonaScalingIntegration:
    """Integration tests for the full persona scaling flow."""
    
    def test_f22_upgrade_query(self):
        """Test the F-22 modernization example query."""
        query = "Plan an F-22 modernization: new radar modes, EW updates, new mission computer, and secure datalinks."
        context = {"domain": "defense", "sector": "aerospace"}
        axis_vector = {1: "PL16", 8: True, 9: True, 10: True, 11: True}
        
        # Simulate low-confidence base results
        base_results = {
            "knowledge": {"response": "General analysis", "confidence": 0.7, "has_gaps": True},
            "sector": {"response": "Industry view", "confidence": 0.68},
            "regulatory": {"response": "Regulatory", "confidence": 0.75},
            "compliance": {"response": "Compliance", "confidence": 0.72}
        }
        
        # Run sufficiency check
        tool = PersonaSufficiencyTool()
        decision = tool.evaluate(query, context, axis_vector, base_results)
        
        # Should expand
        assert decision.should_expand is True
        assert decision.threshold_mode == "high_assurance"
        
        # Run orchestration
        orchestrator = PodOrchestrator()
        state = orchestrator.orchestrate(
            query=query,
            context=context,
            scaling_decision=decision,
            base_persona_results=base_results
        )
        
        # Verify results
        assert state.status == "completed"
        assert len(state.pods) >= 2  # At least knowledge and regulatory pods
        
        # Check that knowledge pod has the expected SMEs
        if "knowledge" in state.pods:
            k_pod = state.pods["knowledge"]
            assert k_pod.persona_count >= 3
        
        # Verify final synthesis was created
        assert state.final_synthesis != ""
        assert "Committee Response" in state.final_synthesis
