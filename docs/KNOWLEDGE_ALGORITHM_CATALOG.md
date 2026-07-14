# Knowledge Algorithm production catalog

The live registry contains 125 Knowledge Algorithms. `production_catalog.py` is
the authoritative production classification overlay and is merged into the KA
API/UI metadata at startup.

Every entry declares its category, production-enabled state, determinism,
version, input contract, evidence requirement, guarantee, limitation,
performance budget, semantic test reference, and this documentation reference.

Only `production_validator` and selected `deterministic_heuristic` entries may be
production enabled. Experimental methods, presentation helpers, and placeholders
are disabled by default. Direct API execution of a disabled entry requires the
explicit `allow_nonproduction: true` owner opt-in, and governed production traces
reject disabled entries even when called internally.

Production-enabled semantic invariants live in
`tests/knowledge_algorithms/test_production_invariants.py`. The registry gate
fails on missing implementations, category violations, stochastic production
code, missing contract metadata, or missing test/documentation references.

The category guarantee never means factual correctness. Validators check only
their documented inputs; deterministic heuristics are repeatable but are not
calibrated probabilities or independent evidence.
