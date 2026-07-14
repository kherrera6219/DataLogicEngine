# Versioned AI quality evaluation

Corpus `2026.07.13.1` contains repository-authored synthetic cases for normal
chat, retrieval, graph paths, contradiction, stale evidence, abstention, prompt
injection, Knowledge Algorithms, simulation boundaries, and provider-disabled
behavior. Evaluation compares semantic claims, evidence links, uncertainty,
trace stages, policy outcomes, and convergence decisions; it does not require an
exact answer string.

Release thresholds are: factual-support precision >= 0.95; grounded-citation
precision = 1.00; unsupported factual-claim rate <= 0.02; contradiction handling
= 1.00; required abstention correctness = 1.00; retrieval relevance >= 0.90;
graph-path correctness = 1.00; production KA invariants = 1.00; required trace
stage completeness = 1.00; and no metric may regress more than 0.02 from the
approved baseline.

Every provider/model/workflow row is evaluated separately. Results must record
corpus, workflow, prompt, formula, evaluator, provider and model versions, raw
structured outcomes, thresholds, and approval without credentials. A manifest
change creates a drift mismatch and quarantines the affected row until the same
evaluation and owner approval pass again.

The deterministic local contract suite is automated. OpenAI, Google, and the
blinded acceptance sample remain pending until the rebuilt application is
installed and exercised; the matrix therefore correctly reports release not
ready.
