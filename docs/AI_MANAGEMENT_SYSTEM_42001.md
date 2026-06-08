# AI Management System: ISO/IEC 42001 Mapping

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | AI Governance + Security Engineering |
| Review cadence | Every 60 days |

## Purpose

Map DataLogicEngine to an ISO/IEC 42001-style Artificial Intelligence Management System (AIMS) operating model.

This is not a certification claim. It is an internal alignment document showing how current platform controls, documentation, testing, auditability, and governance artifacts support an AIMS-like management system.

## Audience

1. AI governance reviewers
2. Security and compliance teams
3. Platform leadership
4. Product owners
5. Auditors and external technical reviewers
6. Contest, sponsor, and enterprise evaluators

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/API.md`
3. `docs/SECURITY.md`
4. `docs/TESTING.md`
5. `docs/PRODUCTION_READINESS.md`
6. `docs/OPERATIONAL_RUNBOOKS.md`
7. `docs/SDLC_SSDF_MAPPING.md`
8. `docs/diagrams/05_truth_engine_architecture.md`
9. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
10. `docs/diagrams/12_end_to_end_request_lifecycle.md`

---

## Management-system scope

DataLogicEngine is an AI governance and knowledge-reasoning platform with:

1. local-first desktop and controlled web/cloud deployment modes;
2. governed AI request lifecycle;
3. DMRF control plane;
4. Truth Engine v7.3;
5. 17-axis coordinate routing;
6. DSQP persona construction;
7. trace, audit, and export integrity;
8. multi-store data and memory architecture;
9. CI/release governance;
10. security, privacy, and operational runbooks.

AIMS scope for this mapping:

```text
AI-enabled reasoning workflows
  -> request classification
  -> risk/impact controls
  -> evidence and trace management
  -> model/provider/tool execution
  -> memory/audit persistence
  -> release and operational governance
```

---

## ISO/IEC 42001 alignment overview

| AIMS area | DataLogicEngine alignment |
|---|---|
| Organizational context | Architecture docs, deployment modes, data architecture, risk/criticality axes, production readiness scorecard. |
| Leadership and accountability | Security/AI governance ownership in docs, release gates, role/admin controls, audit/reviewer paths. |
| Planning and risk treatment | DMRF tiering, Axis 15 risk/threat, Axis 16 ethics/trust, TruthGate, EvidenceModel, ConvergencePolicy. |
| Support and resources | Developer guide, testing guide, runbooks, local-first architecture, CI, runtime precheck, packaging smoke. |
| Operation | End-to-end governed request lifecycle, DMRF/Truth Engine execution, MCP governance, trace review. |
| Performance evaluation | Metrics, Trace Explorer, TruthMemory, contract/security/parity tests, release governance reports. |
| Improvement | Change notes, regression testing, incident runbooks, release checklists, documentation versioning. |
| Annex-style AI controls | Security, privacy, data quality, transparency, human review, auditability, lifecycle, and supplier/provider controls. |

---

## 1. Leadership and governance

Current governance artifacts:

1. `docs/ARCHITECTURE.md` — system architecture and reviewer path.
2. `docs/SECURITY.md` — security controls and reviewer path.
3. `docs/PRODUCTION_READINESS.md` — readiness scorecard and release decision model.
4. `docs/TESTING.md` — validation and release gates.
5. `docs/OPERATIONAL_RUNBOOKS.md` — incident-response procedures.
6. `docs/RELEASE_CHECKLIST.md` — release evidence requirements.

Governance mechanisms:

- explicit document owners and review cadences;
- version/date metadata in active docs;
- release-governance verifier;
- protected-branch CI gates;
- admin/RBAC surfaces;
- audit and trace artifacts;
- issue/remediation tracking through TODO/release artifacts.

---

## 2. Planning and AI risk assessment

Risk and impact are handled through both architecture and runtime controls.

Runtime risk controls:

1. `TierClassifier` classifies requests into `trivial`, `moderate`, `high_stakes`, `extreme`, or `autonomous`.
2. Axis 15 represents risk/threat domain context.
3. Axis 16 represents ethics/trust/criticality context.
4. Axis 17 maps tier to FROST depth and TruthCore mode.
5. TruthGate evaluates security, budget, compliance, priority, and trust context.
6. EvidenceModel scores evidence freshness.
7. ConvergencePolicy determines refinement/convergence thresholds.
8. Trace Explorer exposes evidence, claims, personas, policy decisions, and memory events.

Relevant implementation:

- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/router.py`
- `core/axes/axis15_risk_threat.py`
- `core/axes/axis16_ethics_trust.py`
- `core/axes/axis17_frost_mode.py`
- `backend/truth_engine/truth_gate/gateway.py`
- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`

---

## 3. Support, competence, and resources

Support and competence controls include:

1. developer onboarding guide;
2. architecture diagrams;
3. testing standards;
4. operational runbooks;
5. local-first deployment runbooks;
6. CI parity guidance;
7. security and production readiness guides;
8. DSQP persona construction for structured expert roles.

DSQP supports competence modeling by converting axes 8-11 into structured expert personas:

```text
knowledge expert
sector expert
regulatory expert
compliance expert
```

Each DSQP persona has seven components:

```text
job_role
education
certifications
skills
training
career_path
related_jobs
```

This is stronger than ad-hoc role prompting because personas are structured, serializable, validated, and traceable.

---

## 4. AI system operation

The governed operational lifecycle is:

```text
request
  -> API/security envelope
  -> DMRF injection defense
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP persona construction
  -> TruthCore workflow planning
  -> model/tool execution where required
  -> evidence/convergence policy
  -> memory/audit/artifact persistence
  -> TruthLink event publication
  -> Trace Explorer review
  -> integrity-protected export
```

Operational controls:

- no silent synthetic success on provider/gateway failure;
- fail-closed behavior for injection and gate failures;
- traceable policy decisions;
- evidence and claims review;
- export integrity manifest;
- incident runbooks for AI/control-plane failures.

Relevant diagrams:

- `docs/diagrams/12_end_to_end_request_lifecycle.md`
- `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
- `docs/diagrams/05_truth_engine_architecture.md`

---

## 5. Performance evaluation and monitoring

Performance and evaluation controls include:

1. `/health`, `/live`, `/ready`, `/metrics` operational endpoints.
2. Truth Engine health/status routes.
3. DMRF observability metrics.
4. route-level request metrics.
5. LLM/connector latency SLO signals.
6. Trace Explorer and run exports.
7. TruthMemory metrics and explainability outputs.
8. CI test and report artifacts.
9. packaging smoke reports.
10. release checklist evidence.

Testing and evaluation layers:

- backend pytest;
- API contract tests;
- local-mode parity tests;
- security regression tests;
- Truth Engine tests;
- Knowledge Algorithm tests;
- 17-axis tests;
- frontend unit/E2E/a11y/visual tests;
- Windows packaging smoke;
- environment/lockfile/schema/docs governance checks.

---

## 6. Continuous improvement

Improvement mechanisms:

1. versioned documentation with change notes;
2. incident postmortems and corrective actions;
3. regression tests for production/security defects;
4. release-governance verifier;
5. schema parity checks;
6. runtime precheck;
7. docs reference validation;
8. lockfile and environment parity checks;
9. operational runbooks and support bundles;
10. roadmap/TODO tracking for known release blockers.

---

## Annex-style AI control mapping

| Control area | DataLogicEngine implementation |
|---|---|
| AI policy | Architecture, Security, Production Readiness, Testing, and Operational Runbooks define governance expectations. |
| Roles and responsibilities | Document metadata owners, admin/RBAC surfaces, release checklist ownership, incident runbook owners. |
| Risk management | TierClassifier, Axis 15, Axis 16, Axis 17, TruthGate, EvidenceModel, ConvergencePolicy. |
| Impact assessment | risk/criticality axes, high-stakes/extreme/autonomous tiers, trace review, policy decisions. |
| Data for AI | SQL/Neo4j/USKD/Chroma/object-store architecture, ingestion controls, schema parity, trace evidence. |
| Transparency | Trace Explorer, run detail views, evidence/claims/persona/policy tracking, AI limitations disclosure. |
| Human oversight | Admin/compliance surfaces, release gates, operational runbooks, manual accessibility and signing evidence requirements. |
| Information security | desktop local auth, CSRF/CORS/trusted hosts, rate limits, DPAPI, export integrity, TruthGate, injection defense. |
| Supplier/provider management | LLM Gateway provider config, MCP connector governance, provider validation scripts, connector scope/contract controls. |
| Logging and audit | TruthMemory, trace tables, audit logs, export manifests, support bundles, release evidence artifacts. |
| Lifecycle management | CI, deploy workflows, release checklist, production readiness scorecard, packaging smoke, code signing. |
| Monitoring and measurement | `/metrics`, Truth Engine stats, DMRF observability, latency SLO metrics, CI reports. |
| Incident management | `docs/OPERATIONAL_RUNBOOKS.md`, support bundle generator, post-incident validation checklist. |
| Improvement | regression tests, docs versioning, governance scripts, postmortem corrective actions. |

---

## Evidence register

| Evidence type | Location |
|---|---|
| Architecture evidence | `docs/ARCHITECTURE.md`, `docs/diagrams/` |
| API contract evidence | `docs/API.md`, `tests/contract/` |
| Security evidence | `docs/SECURITY.md`, `tests/security/`, `backend/security/` |
| Data governance evidence | `docs/DATABASE_SCHEMA.md`, `scripts/validate_schema_parity.py` |
| Operational evidence | `docs/OPERATIONAL_RUNBOOKS.md`, support bundles, `/metrics` |
| Production readiness evidence | `docs/PRODUCTION_READINESS.md`, `docs/RELEASE_CHECKLIST.md` |
| Release evidence | `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, signing workflow, packaging reports |
| AI traceability evidence | Trace Explorer, `backend/tracing/`, TruthMemory, export manifests |
| AI control-plane evidence | `backend/dmrf/`, `backend/truth_engine/`, `backend/dsqp/`, `core/axes/` |

---

## Gaps and certification caveats

This document does not claim ISO/IEC 42001 certification.

Known caveats:

1. A formal external ISO/IEC 42001 audit has not been completed.
2. Some management-system procedures may require organizational policies outside the repository.
3. Manual accessibility evidence is still required before signed production distribution.
4. Trusted Windows signing credentials and signed artifact validation are required before production installer distribution.
5. Field-level encryption now writes AES-256-GCM payloads; legacy Fernet-encrypted values remain decryptable for backward compatibility.
6. Provider-backed staging tests must be run with configured provider credentials before production release claims.

---

## Reviewer verification path

An AI governance reviewer should inspect:

1. `docs/ARCHITECTURE.md`
2. `docs/SECURITY.md`
3. `docs/PRODUCTION_READINESS.md`
4. `docs/TESTING.md`
5. `docs/OPERATIONAL_RUNBOOKS.md`
6. `docs/diagrams/12_end_to_end_request_lifecycle.md`
7. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
8. `docs/diagrams/05_truth_engine_architecture.md`
9. `backend/dmrf/orchestrator.py`
10. `backend/truth_engine/api.py`
11. `backend/truth_engine/truth_gate/gateway.py`
12. `backend/dsqp/dsqp_chain.py`
13. `core/axes/axis15_risk_threat.py`
14. `core/axes/axis16_ethics_trust.py`
15. `.github/workflows/ci.yml`
16. `docs/RELEASE_CHECKLIST.md`

---

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed the document as an AIMS-style management-system mapping, not a certification claim.
3. Added current DMRF, Truth Engine, 17-axis, DSQP, trace, memory, and release-governance architecture.
4. Added Annex-style control mapping.
5. Added evidence register and known certification caveats.
6. Added reviewer verification path tied to implementation files and governance artifacts.
