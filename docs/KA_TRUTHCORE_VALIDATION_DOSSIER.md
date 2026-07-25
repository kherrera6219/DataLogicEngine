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

The current executable registry exposes 125 IDs: 117 numeric KAs, seven
Layer-10 KAs, and KA-Master. That count is not yet the canonical capability
count. Seven implemented Layer-9 KAs are absent and silently skipped by their
live caller; a 277-row historical/generated metadata file is merged by numeric
ID despite many name/purpose conflicts; and the Python SDK retains a separate
114-row registry and sample handlers.

Phase 6 classified the 125 then-registered entries and enabled 11 that met its
limited deterministic invariant contract. That was a truthful safety boundary,
not proof that every KA was production implemented or wired. Phase 18 now owns
the lossless crosswalk across every distinct documented/executable capability,
historical alias, duplicate and generic scaffold; one canonical manifest;
production implementation; dynamic call-path coverage; individual functional
tests; and rebuilt-installed acceptance. CP18-A passed on 2026-07-25 with an
approved machine-verified authority for 213 distinct capabilities: 132 existing
implementations to qualify and 81 implementation gaps. One confirmed semantic
duplicate is a scoped alias; exact name/purpose/contract collisions, unresolved
duplicate candidates, and unclassified definitions/surfaces are zero. No
unverified numeric metadata match may define a KA's name or purpose. CP18-B
passed with one generated manifest, typed execution/effect/trace contracts, one
canonical controller, generated Python/TypeScript clients, thin compatibility
adapters, no private SDK handler runtime, and zero duplicate canonical
collisions. CP18-C is active for implementation parity.

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
evidence. It is insufficient by itself for Phase 18. The new manifest,
per-KA-function, selector/call-path, side-effect, route/SDK/UI, orchestration,
security, performance, and trace/replay suites collectively become the
authority.

## Phase 18 production completion contract

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
| CP6-D KA catalog | Historical safety classification: 125 classified and 11 enabled entries passed limited invariants | Superseded for subsystem-completion scope by Phase 18 CP18-A through CP18-H |
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
local portion of CP6-F. Phase 18 CP18-A passed its identity/capability authority
gate, but the whole KA subsystem does not yet meet `DLE-FR-011`; CP18-B is
complete and CP18-C Batch 01 qualified 11 existing KAs with 469 KA tests passing
and zero static randomness/mock-honesty flags. Batch 02 restored eight distinct
analysis KAs, advancing the authority to 140 implementations/73 gaps with 493
KA tests passing and zero duplicate findings. CP18-C is still active, CP18-D
through CP18-H remain open, and the signed rebuild is paused.
Batch 03 adds eight governed decision-support KAs, advancing the verified
authority to 148 implementations/65 gaps and 517 passing KA tests without
changing the release decision.
Batch 04 adds six knowledge-evolution KAs with bounded deterministic
drift/alignment, lineage, composition, patch-plan, and conflict-resolution
semantics. It advances the authority to 154 implementations/59 gaps and 536
passing KA tests while keeping mutation claims false and the no-duplicate gate
clean.
Batch 05 adds ten lifecycle-governance KAs and advances the authority to 164
implementations/49 gaps and 567 passing KA tests. Provenance remains distinct
from lineage, privacy output excludes declared non-public values, and all
mutation-oriented results remain unapplied proposals.
Installed OpenAI and Google rows, blinded human sample,
independent reviewer, exact release-registry binding, packaged interpretation,
and owner release approval also remain open. Production/public release is
**NO-GO**.
