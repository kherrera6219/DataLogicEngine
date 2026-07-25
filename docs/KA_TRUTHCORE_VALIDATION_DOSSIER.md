# DataLogicEngine KA and TruthCore validation dossier

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-004 |
| Title | KA and TruthCore validation dossier |
| Document version | v1.1.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | AI assurance, quality, product owner, architecture, independent reviewers, and evaluators |
| Owner | AI Assurance |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Live KA registry/classification, governed orchestration, evidence contracts, evaluation corpus, tests, and Phase 6 evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-25 |
| Next-review trigger | KA registry/implementation/classification, TruthCore, evidence/confidence, evaluation, provider/model, or risk change |
| Requirements and evidence | Product requirements, production catalog, semantic fixtures, golden corpus, Phase 6 reports, and AI system card |

## Assurance boundary

Knowledge Algorithms (KAs), DSQP personas, 17-axis routing, TruthGate, and
TruthCore are controlled reasoning components. Their deterministic or validated
contract does not prove that an answer is factually correct. Production approval
requires traceable evidence, measured quality inputs, provider/model evaluation,
human review, and release authority for the exact installed artifact.

## Registry and classification

The pre-Phase 18 executable registry exposed 125 IDs: 117 numeric KAs, seven
Layer-10 KAs, and KA-Master. Seven implemented Layer-9 KAs were absent and
silently skipped by their caller; a 277-row historical/generated metadata file
was merged by numeric ID despite name/purpose conflicts; and the Python SDK
retained a separate 114-row registry and sample handlers. Those counts are
historical evidence, not current authority.

Retained CP18-A/CP18-B work now provides the lossless 213-capability crosswalk,
one generated manifest, typed execution/effect/trace contracts, one canonical
controller, generated Python/TypeScript clients, thin compatibility adapters,
one confirmed scoped alias, and zero unresolved duplicate candidates,
unclassified surfaces, or canonical collisions. CP18-C source batches provide
213 unique implementation owners, zero source gaps, and a 721-test KA baseline.
No unverified numeric metadata match may define a KA's identity or purpose.

Phase 18 nevertheless closed incomplete. Its CP18-D audit proved that source
availability did not establish dynamic product integration: only a small subset
has detected call sites, callers consume an obsolete result shape, ten-layer
and 12-step paths are not canonical product paths, L9/L10 IDs and failure
semantics drift, and persona, simulation, and broad owning-subsystem integration
remain incomplete. CP18-C's broader effect/pre-existing qualification and
CP18-E-H transferred without waiver to Phase 19.

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
| Identity parity | Canonical ID/name/purpose/version resolves identically in runtime, API, UI, SDK, trace, tests, and documentation |
| Call-path coverage | Every canonical KA has at least one reachable owning-subsystem path and positive/negative selector fixture |
| Individual proof | Every canonical KA has its own named functional test of the production entry point |
| Side-effect truth | Effectful KAs use an authoritative app-owned service port and return a policy/idempotency-bound receipt |
| Capability preservation | Every distinct historical or executable capability is implemented or compatibly aliased before old identity removal |

`tests/knowledge_algorithms/test_production_invariants.py` remains Phase 6
evidence. It is insufficient by itself for Phase 19. The manifest,
per-KA-function, selector/call-path, side-effect, route/SDK/UI, orchestration,
security, performance, and trace/replay suites collectively become the
authority.

## Phase 19 system integration contract

KAs are selected when needed; they are not all run for every request. A single
versioned selector evaluates intent, domain, risk, tier/layer/persona, evidence
state, dependencies, policy, budget, and live service capabilities, then
validates a bounded dependency DAG. Every selected execution receives
server-owned principal, request/run/session, deadline, cancellation, budget,
configuration, capability, and seed context.

Pure KAs return typed analysis/validation proposals. Effectful KAs use only the
approved app-owned service adapter after authorization, confirmation,
idempotency, and transaction checks and return the authoritative receipt. The
orchestrator remains the single writer. Planned, selected, executed, skipped
with reason, blocked, failed, and applied-effect states are separate, and only
executed outputs may affect answers, evidence, confidence, state, or traces.

One `GovernedExecutionOrchestrator` owns the product lifecycle. Layers 1-5
prepare and assess a candidate; the candidate gateway decides whether the
request may proceed; Layers 6-10 validate, refine, govern, and release it.
Layer 9 may invoke one bounded canonical 12-step refinement subgraph when policy
and evidence require it. Quad Persona/DSQP supplies causal perspectives for
axes 8-11 through governed KA calls; persona output is context, not evidence.

Every KA has exactly one implementation owner and one primary owning subsystem.
Other subsystems consume it through the canonical controller. TruthGate,
TruthCore, ingestion, retrieval, graph, memory, simulation, MCP, provider,
security, operations, and effect services keep authority over their own state;
effect-oriented KAs may propose work but may claim application only from a
policy- and idempotency-bound owning-service receipt. CP19-L is the clean
source/integration gate that may authorize one rebuild. CP19-M is exact
rebuilt-installed acceptance and cannot be replaced by source evidence.

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
| CP6-D KA catalog | Historical safety classification: 125 classified and 11 enabled entries passed limited invariants | Identity/source authority retained from Phase 18; system integration and installed acceptance owned by Phase 19 CP19-A through CP19-M |
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
local portion of CP6-F. Retained Phase 18 evidence establishes 213 canonical
capabilities, 213 unique implementation owners, and zero source gaps, but the
whole subsystem does not yet meet `DLE-FR-011`. CP18-D failed and
no unresolved finding was waived.

Phase 19 CP19-A passed with one primary subsystem owner and governed
consumer/evidence destinations for all 213 KAs, 16 workflow dispositions, zero
new runtime registries, and 726 passing KA tests. CP19-B typed result-contract
parity is active. CP19-C-M still must establish manifest selection and bounded
dependency DAG execution, the canonical ten-layer and 12-step paths, correct
fail-closed L9/L10, causal KA-backed Quad Persona/DSQP, Truth/data/knowledge and
extended-subsystem integration, API/SDK/desktop workflows, one semantic
production test and real call-path/effect/trace proof per KA, clean source
qualification, and exact rebuilt-installed acceptance. The signed rebuild
remains paused through CP19-L.

Installed OpenAI and Google rows, the blinded-human sample, independent
reviewer, exact release-registry binding, packaged interpretation, and owner
release approval also remain open. Production/public release is **NO-GO**.
