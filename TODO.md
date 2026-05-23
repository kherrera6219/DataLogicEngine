# DataLogicEngine TODO

**Last updated:** 2026-05-23
**Status:** Canonical planning source

This is the only active TODO list for the repository. Keep open work here instead of adding separate project plans, roadmap files, assessment TODOs, or notes documents.

## Unified Backlog

Review date: 2026-05-23

No standalone `ROADMAP.md` file exists in the repository. The only roadmap-style source found during the May 22 review was `docs/archive/historical-documents/MVP Plan_ Universal Knowledge Graph (UKG) System.pdf`; actionable current and future work is consolidated below.

### Release Readiness

- [x] Finalize the in-app feature list used by `frontend/public/manifest.json`, `README.md`, and About pages. Current copy is conservative and aligned; manifest shortcuts now point to dashboard, chat, privacy controls, and provider settings.
- [x] Add or document keyboard navigation coverage across primary pages and modal/dialog workflows on the packaged Windows app.
- [ ] Execute NVDA screen reader compatibility checks on Windows using `reports/app-readiness/nvda-manual-checklist.md`.
- [ ] Provision a trusted production code-signing certificate in GitHub secrets and run `.github/workflows/release-installer-signing.yml` to produce signed release artifacts with signature reports.
- [ ] Prepare release checklist evidence: changelog entry, governance command output, CI/security scan review, artifact signing evidence, code-owner approval, rollback plan, and disaster recovery review. Local evidence is started in `reports/release-readiness/local-release-evidence-2026-05-23.md`, and `docs/DOCS_VERSION.json` is current for this docs pass.

### Product And UX

- [x] Decide whether `/register` remaining disabled is the intended local-first behavior or whether web self-registration should be reopened as a future web-mode feature. Decision: keep disabled for the current local-first desktop build; reopen only as a future web-mode product requirement.
- [x] Audit MCP and admin screens for live-data versus static metric placeholders and update any placeholder controls before release. Evidence: `reports/app-readiness/ui-placeholder-audit.md`.
- [x] Verify toolbar actions route by route and either wire, hide, or document placeholder-only actions. The graph toolbar now routes search/help/settings/history/profile actions and hides unsupported export/notification controls.
- [x] Add public architecture assets under `docs/assets/readme/` for the external README.
- [ ] Keep screenshots refreshed when primary UI changes.

### API, Contracts, And Documentation

- [ ] Tighten public API contracts, reduce legacy route aliases, and improve generated OpenAPI coverage.
- [ ] Keep generated inventory docs (`docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md`) refreshed after repository cleanup/refactors.
- [ ] Expand CI docs enforcement to include markdown linting for active files.
- [ ] Keep vendor guidance baseline (`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`) reviewed at least monthly.
- [ ] Expand deployment reference material for Kubernetes, managed Postgres, managed Redis, and managed Neo4j.

### Runtime, Testing, And Operations

- [ ] Validate the simulation engine in a provider-backed staging environment.
- [ ] Expand comprehensive integration tests beyond current targeted route and readiness evidence.
- [ ] Configure production firewall rules and network security groups.
- [ ] Set up or document the production security incident response team.
- [ ] Configure backup verification and restore testing.
- [ ] Set up continuous security scanning review evidence for release.
- [ ] Set up performance benchmarking evidence.
- [ ] Configure compliance reporting automation.
- [ ] Document production blue-green deployment, disaster recovery, read-replica, and rollback procedures where applicable.
- [ ] Configure user analytics, usage tracking, A/B testing, feature flags, and chaos testing only if they remain product requirements for the target deployment.

### MCP And Connector Roadmap

- [x] Reconcile `docs/MCP_INTEGRATION.md` future items against implemented connector/OAuth/metrics work and close stale entries.
- [ ] Add MCP sampling support for LLM completions if still required.
- [ ] Add advanced MCP resource subscriptions and real-time update notifications.
- [ ] Add external/remote MCP server connection management.
- [ ] Add dynamic MCP plugin discovery and loading.
- [ ] Validate production connector operation against real external systems.

### Long-Term Research And Platform Roadmap

- [ ] Evaluate mobile applications only if mobile becomes a product requirement; historical research is retained in `docs/archive/research/REACT_NATIVE_RESEARCH.md`.
- [ ] Evaluate local SLM/model serving for L1/L2 tasks.
- [ ] Add multi-language/i18n support if required by target users.
- [ ] Expand richer user-facing trace and compliance overlay UX.
- [ ] Validate production-scale enterprise ingestion and vector-store workflows.
- [ ] Validate production alerting evidence for `/health`, `/live`, `/ready`, `/metrics`, Sentry, and admin dashboards.
- [ ] Harden multi-tenant operations, cost controls, recursive persona evaluation, dynamic persona expansion, human feedback loops, automated axis learning, quantum-ready node research, and policy-as-code governance for larger deployments.

## Completed Local Stack QC (Phase 6 — 2026-05-15)

All five internal databases have been wired, seeded, and mutually validated in local QC mode. No cloud or external dependencies required.

| Check | Status |
| --- | --- |
| PostgreSQL migrations current | Done — `flask db current` resolves to head; `correlation_id` and `estimated_cost_usd` columns added via `d1e2f3a4b5c6` migration |
| All tracked tables exist | Done — 64 models fully migrated |
| TraceRun AuditBundle columns added | Done — `layers_executed`, `refinement_cycles`, `regulatory_pass`, `security_pass`, `truthgate_decision`, `token_cost`, `latency_ms`, `evidence_pack_hash`, `coordinate17_id` |
| Redis live | Done — Redis on port 6379 responds; session and rate-limit storage functional |
| Neo4j pillar seed | Done — `scripts/seed_neo4j.py` seeds pillar taxonomy + `HONEYCOMB_BRIDGE` crosswalk edges |
| ChromaDB collections initialized | Done — `knowledge_nodes`, `persona_profiles`, `citation_cache`, `audit_evidence` collections created at startup |
| Object storage buckets initialized | Done — `audit_logs`, `simulation_artifacts`, `deliverables`, `graphs`, `eval_data` buckets pre-created at startup |
| End-to-end Tier 2 gateway query | Done — 200 OK with `[UKG Audit Trace]` footer in response body |
| TruthAuditEvent hash-chain receipt | Done — `TruthAuditEvent` row written with valid `hash_chain` and `previous_hash` after each Tier 2+ run |
| F-CONF-01 confidence formula | Done — `TraceRun.confidence` set by `ConfidenceCalculator` (evidence × KA × persona × gate weighting), not raw LLM output |
| Circular import fixes | Done — `core/axes/axis1_knowledge.py`, `axis12_location.py`, `axis13_time.py` migrated to `from extensions import db` |
| `db.session.flush()` before FK child rows | Done — `TraceStage.run_id` now populated correctly after `TraceRun` flush |
| Audit footer coordinate guard | Done — `_audit_footer` coerces non-dict `coordinate` to `{}` before attribute access |
| TruthAuditEvent session_id FK | Done — `TruthMemoryCommitService` passes `session_id=None` (nullable column; no `truth_sessions` row in this flow) |
| Local database setup script | Done — `scripts/setup_local_databases.py` installs PostgreSQL 16, Redis, and Neo4j binaries |
| GraphStore schema constraints | Done — `ensure_schema()` creates `Pillar` and `KnowledgeNode` uniqueness constraints and code/axis indexes on connect |
| Vector store collection init | Done — `initialize_collections()` called at startup via `app.py` |
| Object storage bucket pre-creation | Done — called at startup via `app.py` |

## Completed Application-Readiness Work

| Area | Evidence |
| --- | --- |
| Privacy policy drafted | `docs/PRIVACY_POLICY.md` |
| Privacy policy published in-app | `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services page | `frontend/app/about/cloud-services/page.tsx` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| AI output labels | `frontend/components/Chat/MessageBubble.tsx` |
| Provider/model shown per response | `frontend/components/Chat/MessageBubble.tsx` |
| User data export endpoint | `routes/user_data_routes.py` |
| User data deletion endpoint | `routes/user_data_routes.py` |
| Privacy controls page | `frontend/app/settings/privacy/page.tsx` |
| Privacy links in settings and footer | `frontend/app/settings/page.tsx`, `frontend/app/layout.tsx` |
| AI processing toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Chat history opt-out toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Automated accessibility audit command | `frontend/package.json` (`test:a11y:ci`) |
| Authenticated WCAG 2.1 A/AA route evidence | `frontend/scripts/run-a11y-ci.mjs`, `reports/app-readiness/a11y-ci-report.json` |
| Failure-mode/export-delete Playwright evidence | `frontend/tests/e2e/app-readiness-evidence.spec.ts`, `reports/app-readiness/playwright-app-readiness-report.json` |
| Keyboard navigation evidence | `frontend/tests/e2e/keyboard-navigation-evidence.spec.ts`, `reports/app-readiness/keyboard-navigation-report.json` |
| NVDA manual screen reader checklist | `reports/app-readiness/nvda-manual-checklist.md` |
| UI placeholder audit | `reports/app-readiness/ui-placeholder-audit.md` |
| Local release evidence | `reports/release-readiness/local-release-evidence-2026-05-23.md` |
| Conservative copy/disclosure pass | `frontend/public/manifest.json`, `frontend/app/about/page.tsx`, `frontend/app/about/ai-limitations/page.tsx`, `frontend/app/about/cloud-services/page.tsx`, `frontend/app/legal/privacy/page.tsx`, `frontend/components/Chat/ChatInterface.tsx`, `frontend/components/settings/AiModelSettings.tsx`, `frontend/components/CloudDisclosureBanner.tsx`, `docs/PRIVACY_POLICY.md` |

## Documentation Cleanup Policy

- Keep current planning in this file only.
- Keep release go/no-go criteria in `docs/RELEASE_CHECKLIST.md`.
- Keep active documentation discoverable from `README.md` and `docs/README.md`.
- Do not add new `PROJECT.md`, `ROADMAP.md`, `current_plan.md`, assessment TODOs, or archived planning summaries without first folding actionable items into this file.
