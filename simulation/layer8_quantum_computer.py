"""Compatibility wrapper for the core legacy Layer 8 quantum simulation module."""

from core.simulation.layer8_quantum_computer import (
    FidelityProjectionModule,
    QuantumCollapseSimulator,
    QuantumEntanglementManager,
    SchrodingerConfidenceProcessor,
    SimQOSKernel,
    SimulatedQuantumComputer,
    SuperpositionLogicEngine,
)

__all__ = [
    "FidelityProjectionModule",
    "QuantumCollapseSimulator",
    "QuantumEntanglementManager",
    "SchrodingerConfidenceProcessor",
    "SimQOSKernel",
    "SimulatedQuantumComputer",
    "SuperpositionLogicEngine",
]
