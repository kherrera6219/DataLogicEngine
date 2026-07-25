# DataLogicEngine AI system card

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-003 |
| Title | AI system card and evaluation report |
| Document version | v1.1.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Users, evaluators, AI assurance reviewers, risk reviewers, and release authority |
| Owner | AI Assurance |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented governed request path, evaluation protocol, model records, and acceptance evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-25 |
| Next-review trigger | Model/provider, evaluation method, risk, limitation, metric, or release-status change |
| Requirements and evidence | Evaluation suite, golden corpus, model manifest, risk records, and Phase 12 evidence |

## Intended purpose and operating boundary

DataLogicEngine is an app-owned governed reasoning and evidence-trace system for
desktop chat, retrieval, structured analysis, and auditable Knowledge Algorithm
workflows. It helps a human examine supplied information and the system's
recorded reasoning controls. It is not an autonomous authority and is not
approved to replace qualified medical, legal, financial, safety, or regulatory
judgment.

The supported product is the local Windows desktop application and its approved
private client-gateway profile. Public multi-user web/cloud hosting, implicit
provider failover, background model training, and autonomous high-impact
decision-making are excluded. The configured owner remains responsible for the
lawful use of source material, provider and connector terms, human review, and
release decisions.

## Governed AI lifecycle

Requests pass the API/security envelope, injection defense, TruthGate admission,
tier classification, 17-axis routing, deterministic DSQP persona construction,
production-enabled TruthCore KAs, bounded local retrieval, and a configured
OpenAI or Google model when needed. Output controls, claim/citation validation,
bounded convergence, and transactional trace persistence follow execution.

The current 11-entry production-enabled KA subset is a Phase 6 safety boundary,
not final subsystem completion. Phase 18 retained a reconciled 213-capability
authority, one runtime/controller, 213 unique implementation owners, zero source
gaps, and a 721-test KA baseline, but its whole-application wiring audit failed.
Phase 19 now owns the canonical selector/DAG, ten-layer, L9/L10, Quad
Persona/DSQP, 12-step, Truth/data/knowledge, extended-subsystem, API/SDK/desktop,
per-KA, and installed integration proof. The signed rebuild is paused through
CP19-L. No catalog entry, imported module, or nonproduction opt-in alone
establishes production capability.

The trace records request and workflow identity, provider/model selection,
policy and routing decisions, evidence and claim relationships, convergence,
usage, and typed failure/cancellation states. A provider result is not released
as successful when its required durable usage or trace record cannot be written.
Local deterministic workflows use no provider call. Selected prompts and
retrieved context may leave the device only when the owner initiates a workflow
that uses the configured provider.

## Providers, models, cost, and quota controls

The provider manifest is the only production model allowlist. It currently
declares OpenAI through the Responses API and Google through `generate_content`;
unknown providers and undeclared models fail closed. One selected provider/model
is used for a request, and the application does not silently switch providers.
Native stream capability and buffered renderer delivery are identified
separately.

| Provider | Supported default model | API contract |
|---|---|---|
| OpenAI | `gpt-5.5` | `responses` |
| Google | `gemini-3.1-pro-preview` | `generate_content` |

Server-owned per-request, session, daily, and monthly call/token ceilings apply.
Retries and refinements consume the same allowance. At the warning threshold the
owner must confirm that one request; confirmation cannot exceed a hard ceiling.
A ledger failure is fail-closed. Cost is only an estimate from dated,
owner-reviewed model pricing. Missing, stale, malformed, or unmatched pricing is
reported as `unknown`, never zero, and a simulation with an explicit cost limit
is rejected before provider use when the estimate cannot be established.

## Evaluation method

The versioned synthetic golden corpus covers normal chat, retrieval, graph
paths, contradiction, stale evidence, abstention, prompt injection, Knowledge
Algorithms, simulation boundaries, and provider-disabled behavior. Evaluation
compares semantic claims, evidence links, uncertainty, trace stages, policy
outcomes, and convergence rather than exact answer strings. Every
provider/model/workflow row records its corpus, prompt, formula, evaluator,
versions, structured outcomes, thresholds, and approval without credentials.

Release thresholds require factual-support precision of at least 0.95,
grounded-citation precision of 1.00, unsupported factual-claim rate no greater
than 0.02, contradiction and required-abstention correctness of 1.00, retrieval
relevance of at least 0.90, graph-path correctness and production KA invariants
of 1.00, complete required trace stages, and no metric regression greater than
0.02 from the approved baseline. A displayed `dle-confidence.v1` number is named
evidence-support coverage, not a probability of correctness. Missing quality,
freshness, provenance, claim support, or validator inputs produce `not measured`.

Phase 19 requires a per-KA evidence matrix: canonical identity/version, typed
schemas, representative semantic fixture, individually named functional test,
positive/negative selector fixture, real owning call path, dependency/failure/
side-effect/seed rules, performance budget, limitation, and causal trace
assertions. Effect-oriented KAs must return a receipt from the authoritative
app-owned service; plausible metadata or a simulated operation is a failure.

## Risk management and human oversight

Tier, risk/threat, ethics/trust, and FROST/TruthCore routing controls increase
review depth for higher-risk requests. The system can block, abstain, return a
typed provider/tool failure, or require owner confirmation. Prompt injection,
PII and prohibited-content checks, connector scope and consent, trace review,
incident handling, regression tests, and release gates form the operating risk
treatment. Human oversight is mandatory for high-risk use, material provider or
model changes, exception acceptance, and release approval.

This system card is an assurance record, not an ISO/IEC 42001 certification,
Microsoft approval, legal opinion, or accessibility/security certification.
Material changes to models, providers, prompts, corpus, KAs, risk controls,
storage, connectors, or evaluation method require impact review and re-evaluation.

## Known limitations and failure modes

Known failure modes include incomplete or stale sources, retrieval misses,
provider drift/outage, ambiguous claims, imperfect deterministic term-overlap
support checks, prompt injection, connector/tool failure, ledger or trace
persistence failure, and human disagreement. Synthetic evaluation cannot prove
fitness for every real corpus or high-impact use. Provider terms, behavior,
pricing, regional handling, and availability may change outside the application.
The user must review cited evidence and uncertainty instead of treating fluent
output or a numeric score as truth.

## Current assurance disposition

The deterministic local contract suite and corpus schema are automated.
Rebuilt-installed OpenAI and Google rows, representative-corpus results,
provider quota/latency/cancellation/restart reconciliation, and the blinded human
acceptance sample are retained release gates. Until those exact-artifact results
and the final independent/owner dispositions pass, production/public release is
**NO-GO**.
