# CU-4 terminology evidence inventory

| Field | Value |
|---|---|
| Inventory date | 2026-08-18 |
| Source HEAD | `254be21ffe4b8b0ff9233e975530ee12c7ac7c8d` |
| Scope | Live source, tests, SDKs, active documentation, and generated authority |
| Archived input | `docs/archive/audits/TERMINOLOGY_MODERNIZATION_PLAN_2026-08-18.md` |
| Result | Inventory and classification complete; no terminology adoption authorized |
| Release effect | None; production/public release remains **NO-GO** |

## Evidence boundary

The archived draft proposed public-copy, UI, API, schema, and internal renames.
Several proposed names would add mathematical, certification, deployment, model,
or compliance claims not supported by the live implementation. This inventory
therefore separates factual display descriptions from compatibility identifiers
and rejects unsupported equivalences.

The scan found the following current-term footprint in live, non-archived files:

| Current term or family | Files containing term | Live behavior observed |
|---|---:|---|
| Simulated Quantum Computer | 4 | NumPy/random belief-state sampling, keyword-based relationships, weighted confidence, entropy/decay, and a stochastic collapse |
| Schrödinger Confidence | 1 | A named confidence processor over sampled/weighted values; no conformal calibration or coverage proof |
| Superposition Logic Engine | 1 | Multiple candidate belief states before stochastic selection |
| Quantum Entanglement Manager | 1 | In-memory node relationships and change propagation |
| AGI Planner | 2 | A Layer 7 planning class and logs; no evidence of general intelligence |
| FROST mode | 4 | Tier-to-layer-depth and TruthCore-mode mapping |
| TruthCore / Truth Engine | 141 | Widely bound source, test, documentation, route, and trace terminology |
| Quad Persona / DSQP | 169 | Widely bound seven-part persona/review contract |
| Octopus / Spiderweb / Honeycomb names | 32 | Axis identifiers for regulatory aggregation, compliance constraints, and cross-domain semantic bridges |
| SEKRE | 17 | Post-L10 analysis and owner-controlled improvement suggestions; automatic improvement is off by default |
| DMRF | 71 | Widely bound router, model, trace, SDK, and canonical 12-step refinement contracts |

Counts are file counts, not raw occurrence counts. They exclude archived
documentation, reports, dependency trees, generated file inventory, and lock
files. Compatibility tests and historical negative-path fixtures were retained
in the review because they demonstrate contract reachability.

## Classification and decision record

| Proposal | Classification | Evidence-based disposition |
|---|---|---|
| SQC to Bayesian Uncertainty Quantification Engine | Internal refactor plus public-copy change | **Reject as a canonical equivalence.** The current implementation samples and combines confidence but does not establish a reviewed Bayesian model. Safe future display copy: “uncertainty sampling.” Preserve module, class, result-key, trace, and evidence identifiers unless a versioned contract change is approved. |
| Schrödinger Confidence to Calibrated Conformal Prediction Score | Mathematical claim | **Reject.** No nonconformity score, calibration set, coverage target, empirical coverage gate, or finite-sample proof exists. Safe future display copy: “sampled confidence.” |
| Superposition Logic Engine to Multi-Hypothesis State Estimator | Public-copy clarification | **Eligible only as descriptive display copy:** “multi-hypothesis analysis.” Do not imply a formal state-estimation method without a specification and tests. |
| Quantum Entanglement Manager to Cross-Domain Correlation Graph | UI/SDK description plus potential schema change | **Eligible only as descriptive display copy:** “cross-domain relationship mapping.” Preserve current identifiers and do not claim PROV-O or ontology conformance. |
| AGI Planner to Hierarchical Goal Decomposer | Public-copy clarification | **Eligible:** “bounded hierarchical planner” accurately narrows the claim. Preserve source identifiers until a separately approved internal refactor. |
| FROST depth to Execution Assurance Level/EAL | Standards term | **Reject.** Common Criteria EAL is a certification/evaluation concept, not this tier-to-depth selector. Safe future display copy: “tiered reasoning depth.” |
| TruthCore to Deterministic Factuality Engine | Broad internal/API refactor | **Reject the “factuality” guarantee.** Safe future descriptive copy may say “evidence and policy validation.” Preserve existing contract identifiers. |
| Quad Persona/DSQP to Multi-Perspective Adversarial Review Ensemble | UI/SDK description | **Eligible only as a plain description:** “multi-perspective review.” Preserve the seven-part DSQP contract and do not imply independent model agents when execution does not provide them. |
| Octopus/Spiderweb/Honeycomb to standards-oriented names | Display alias or internal refactor | Descriptive subtitles already exist and are sufficient. Preserve axis identifiers; do not attach ISO, FedRAMP, or jurisdictional compliance claims without control evidence. |
| SEKRE to Continuous Model Distillation and Dataset Synthesis | Product-scope expansion | **Reject.** Live SEKRE is post-run analysis/refinement with owner control. The app has no in-app trainer, and database/UI DPO remains fail-closed without rejected-candidate provenance. Safe future copy: “post-run knowledge refinement.” |
| DMRF to Bounded Auto-Correction and Verification Loop | UI/SDK description | **Eligible with qualification:** “bounded 12-step refinement workflow.” Do not claim IEEE medical-AI conformance or autonomous correction beyond the recorded steps. |
| Air-gapped positioning | Deployment/security claim | **Reject.** The product is local-first with optional provider, connector, client, export, and telemetry egress. Active security/privacy documentation already states that local-first does not mean air-gapped. |
| GDCH, Gemma, Med-Gemma, or local open weights | Provider/product expansion | **Reject under current authority.** The supported generative path is cloud BYOK OpenAI/Google. No active live file adds these proposed providers. |
| Complete SFT/DPO fine-tuning pipeline | Product/training claim | **Reject.** The product prepares candidate dataset exports and does not train or host models. Library-level DPO conversion requires real chosen/rejected provenance; database/UI DPO remains unavailable. |

The `DPO` abbreviation in `data/ukg/compliance_standards.yaml` refers to a data
protection officer and is unrelated to Direct Preference Optimization. It must
not be mechanically renamed.

## Safe adoption set

The following plain descriptions are evidence-compatible candidates for a later
owner-approved copy-only pass:

- uncertainty sampling;
- sampled confidence;
- multi-hypothesis analysis;
- cross-domain relationship mapping;
- bounded hierarchical planning;
- tiered reasoning depth;
- evidence and policy validation;
- multi-perspective review;
- post-run knowledge refinement; and
- bounded 12-step refinement workflow.

No source, API, SDK, schema, database, trace, or historical evidence identifier
was changed in this batch. That preserves compatibility and avoids presenting
an inventory as owner approval.

## Remaining approval and validation gate

CU-4 adoption remains blocked until the owner chooses an exact subset and scope.
Any approved copy-only subset still requires documentation and frontend tests.
Any contract or internal identifier change requires versioned API/SDK/schema,
migration, trace, and installed-regression evidence appropriate to its reach.
