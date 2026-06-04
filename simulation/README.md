# Simulation Compatibility Package

The primary application simulation engines belong under `core/simulation`.
This root `simulation` package remains for legacy imports used by demos, scripts,
tests, and older integration points.

Current migration status:

- `POVEngine` moved to `core.simulation.pov_engine`.
- Legacy Layer 8 quantum simulation moved to
  `core.simulation.layer8_quantum_computer`.
- Legacy Layer 9 recursive AGI simulation moved to
  `core.simulation.layer9_recursive_agi`.
- Layer 7 AGI simulation is sourced from `core.simulation.layer7_agi_system`;
  the root module is a compatibility wrapper.
- `layer2_knowledge.py` remains in this package for now because it mixes graph
  models, YAML/file loading, Quad Persona orchestration, and legacy demo APIs.
  It should be split before being moved into core modules.

Do not add new runtime implementation code here. New simulation domain code
should go under `core/simulation`; backend HTTP/API adapters should stay under
`backend/`.
