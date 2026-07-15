# DataLogicEngine KA and TruthCore validation dossier

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-004 |
| Title | KA and TruthCore validation dossier |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | AI assurance, quality, product owner, architecture, independent reviewers, and evaluators |
| Owner | AI Assurance |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Live KA registry/classification, governed orchestration, evidence contracts, evaluation corpus, tests, and Phase 6 evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-14 |
| Next-review trigger | KA registry/implementation/classification, TruthCore, evidence/confidence, evaluation, provider/model, or risk change |
| Requirements and evidence | Product requirements, production catalog, semantic fixtures, golden corpus, Phase 6 reports, and AI system card |

## Assurance boundary

Knowledge Algorithms (KAs), DSQP personas, 17-axis routing, TruthGate, and
TruthCore are controlled reasoning components. Their deterministic or validated
contract does not prove that an answer is factually correct. Production approval
requires traceable evidence, measured quality inputs, provider/model evaluation,
human review, and release authority for the exact installed artifact.

## Registry and classification

The live registry contains 125 KAs. `production_catalog.py` is the production
classification overlay and is merged into API/UI metadata at startup. Every
entry declares category, production-enabled state, determinism, version, input
contract, evidence requirement, guarantee, limitation, performance budget,
semantic test reference, and documentation reference.

Only `production_validator` and selected `deterministic_heuristic` entries may be
enabled for production. The Phase 6 snapshot classified all 125 and enabled 11
that met the contract. Experimental methods, presentation helpers, placeholders,
stochastic code, missing implementations, or incomplete contract metadata remain
disabled. Owner opt-in may execute a disabled entry for explicit nonproduction
work, but governed production traces reject it.

## KA validation controls

| Control | Required evidence |
|---|---|
| Registry completeness | Every registered ID resolves to implementation and complete production metadata |
| Classification policy | Enabled category is allowed and no placeholder/experimental entry is promoted |
| Determinism | Same normalized input/config yields the same result for deterministic entries |
| Semantic invariant | Named fixture proves only the documented transformation/validation guarantee |
| Evidence rule | Required evidence inputs and missing-input behavior are explicit and tested |
| Limitations | API/UI/catalog state the boundary and do not imply factual certainty |
| Performance | Named bounded fixture meets the recorded runtime budget |
| Trace binding | Execution records exact KA ID/version/input/result/evidence and causal run identity |
| Failure behavior | Invalid input, missing evidence, disabled KA, timeout, exception, and budget failure are explicit |

The authoritative invariant suite is
`tests/knowledge_algorithms/test_production_invariants.py`; broader registry,
route, orchestration, and trace suites provide cross-system coverage.

## DSQP and 17-axis boundary

DSQP constructs structured personas/context for axes 8-11 through a deterministic
activation protocol; it does not train a model or create independent expertise.
The 17-axis router records coordinate decisions and source state. Persona and
axis output remains context to governed execution, not evidence by itself.

The trace must distinguish planned versus executed personas/stages and retain
only actual decisions. Missing or unsupported axis/persona inputs fail or remain
not measured according to the contract.

## TruthCore and evidence model

The backend-owned causal orchestrator drives preflight, TruthGate, routing,
personas, provider/tool execution, evidence and claim validation, convergence,
memory/audit, and response. TruthCore does not choose an undocumented model or
route around policy.

Typed persisted contracts bind sources, evidence, evidence links, claims,
citations, validator outcomes, confidence components, and convergence decisions
to the causal trace. `dle-confidence.v1` produces a numeric result only when all
required components are measured; otherwise status is `not_measured` with a null
score. The number represents evidence-support coverage, not probability of
correctness.

Evidence-required runs may finalize, perform at most one bounded refinement call,
abstain when insufficiency persists, or block on policy. Provider/refinement
failure remains explicit and cannot be replaced with synthetic confidence or
hash-derived convergence.

## Phase 6 checkpoint evidence

| Checkpoint | Engineering result | Retained release evidence |
|---|---|---|
| CP6-A evidence model | Passed persisted source/claim/citation causality tests | Installed provider/evidence trace walkthrough |
| CP6-B no synthetic metrics | Passed strict null/not-measured API/UI tests | Packaged visual/manual interpretation review |
| CP6-C bounded refinement | Passed finalize/refine/abstain/block/failure tests | Live installed provider cancellation/budget evidence |
| CP6-D KA catalog | 125 classified; 11 enabled entries passed invariants | Exact release registry/hash and installed performance sample |
| CP6-E TruthCore | Passed preflight/state/failure/orchestrator tests | Installed end-to-end causal traces |
| CP6-F quality evaluation | Local deterministic corpus contract exists | OpenAI/Google rows, blinded sample, second reviewer, owner approval |

The Phase 6 snapshot recorded 1,915 backend passes, 46 focused/cross-system
passes, 402 frontend passes across 81 files, 25 SDK passes, and passing static,
schema, documentation, route, Electron-security, and governance checks. Those
counts are historical evidence for that commit, not the current release result.

## Evaluation protocol

Corpus `2026.07.13.1` contains synthetic normal chat, retrieval, graph,
contradiction, stale evidence, abstention, prompt injection, KA, simulation, and
provider-disabled cases. It evaluates semantic claims, evidence links,
uncertainty, trace stages, policy outcomes, and convergence rather than exact
strings.

Thresholds include factual-support precision at least 0.95, grounded-citation
precision 1.00, unsupported factual-claim rate at most 0.02, contradiction and
required-abstention correctness 1.00, retrieval relevance at least 0.90, graph-
path and KA invariant correctness 1.00, required trace-stage completeness 1.00,
and no approved-baseline regression greater than 0.02.

Each provider/model/workflow row records corpus, prompt/workflow, formula,
evaluator, provider/model versions, structured outcomes, threshold result, and
approval. Manifest drift quarantines the row until rerun and approval.

## Human review

The blinded sample contains at least 20 balanced cases. Reviewers score factual
support, citation grounding, contradiction disclosure, calibrated uncertainty,
policy compliance, useful clarity, and trace/evidence correspondence. Invented
citations, missed safety blocks, undisclosed material contradictions, or facts
asserted without required evidence are critical failures.

Acceptance requires mean at least 1.8 per dimension, all critical categories
passing, no more than one noncritical disagreement per case, no unresolved
critical disagreement, and recorded owner disposition. A named independent
second reviewer is still pending.

## Current disposition

Repository and deterministic components support CP6-A through CP6-E and the
local portion of CP6-F. Installed OpenAI and Google rows, blinded human sample,
independent reviewer, exact release-registry binding, packaged interpretation,
and owner release approval remain open. Production/public release is **NO-GO**.
