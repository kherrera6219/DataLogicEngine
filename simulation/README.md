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
- Legacy Layer 2 knowledge graph/simulator APIs moved to
  `core.simulation.layer2_legacy_knowledge`.
- Layer 7 AGI simulation is sourced from `core.simulation.layer7_agi_system`;
  the root module is a compatibility wrapper.
- `layer2_knowledge.py` is now a compatibility wrapper. The legacy Layer 2
  implementation still mixes graph models, YAML/file loading, Quad Persona
  orchestration, and legacy demo APIs; split those concerns before merging it
  with the modern `core.simulation.layer2_knowledge.Layer2KnowledgeEngine`.

Do not add new runtime implementation code here. New simulation domain code
should go under `core/simulation`; backend HTTP/API adapters should stay under
`backend/`.
