# Operational Runbooks

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.10.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | SRE + Security Operations |
| Review cadence | Every 30 days |

## Purpose

Provide incident-response procedures for common DataLogicEngine security, runtime, AI control-plane, local-first desktop, storage, trace/export, packaging, and release-governance failures.

## Audience

1. On-call engineers
2. Security operations
3. SRE/platform operations
4. Compliance operations
5. Release engineers
6. Desktop support maintainers

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/API.md`
3. `docs/DEPLOYMENT.md`
4. `docs/DATABASE_SCHEMA.md`
5. `docs/TESTING.md`
6. `docs/PRODUCTION_READINESS.md`
7. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
8. `docs/diagrams/12_end_to_end_request_lifecycle.md`
9. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
10. `docs/diagrams/06_local_first_security_model.md`

---

## Severity model

| Severity | Definition | Examples |
|---|---|---|
| `SEV-1` | Active data exposure, auth compromise, signed-release integrity failure, sustained outage, or export/audit integrity failure. | PII leak, invalid signed installer, local data-store exposure, trace integrity failure. |
| `SEV-2` | Partial outage, degraded reasoning quality, repeated control failure, provider outage, connector failure, or local-first runtime degradation. | TruthGate false negatives, local object store unavailable, DMRF convergence failure surge. |
| `SEV-3` | Localized issue with no broad customer or data-integrity impact. | Single user desktop auth issue, isolated trace export failure with no audit impact. |

---

## Global incident workflow

### Phase 3 data-plane operating boundary

The authenticated Storage surface and backend actions use the singleton runtime
supervisor for service status, start, stop, restart, and verification. Operators
must treat supervisor identity, expected/observed image digest, state, endpoint,
uptime, and safe reason as authoritative; an open port alone is never health.
Foreign identity or an unhealthy required protocol operation keeps production
not ready.

Managed Podman backup/restore is deliberately refused with
`coordinated_data_plane_backup_requires_phase_4` until Phase 4 implements one
manifest and recovery transaction across PostgreSQL, Redis, Neo4j, ChromaDB,
and object storage. Do not bypass this refusal with per-store copies and call the
result a production backup. Qualification resources use a separate identity and
may be removed only by the qualification cleanup command after verifying they
are not installed-production resources.

1. Acknowledge incident and assign severity.
2. Capture correlation IDs, run IDs, trace IDs, session IDs, user scope, and timestamps.
3. Contain impact before optimizing or debugging.
4. Execute the incident-specific runbook below.
5. Validate recovery with `/health`, `/live`, `/ready`, `/metrics`, and relevant user-path checks.
6. Generate a support bundle when escalation is needed.
7. Attach sanitized evidence to the incident record.
8. Create post-incident report with root cause, corrective actions, owner, and due date.
9. Add or update regression tests when the incident exposes a product/control defect.

---

## Support bundle capture

Use the support-bundle generator to collect bounded diagnostics:

```powershell
python .\scripts\generate_support_bundle.py
```

Offline collection:

```powershell
python .\scripts\generate_support_bundle.py --skip-http --max-files-per-group 5
```

Bundle contents include:

1. sanitized environment snapshot;
2. Git and runtime precheck snapshots;
3. recent logs and bounded reports;
4. optional `/health`, `/ready`, and `/metrics` probe output;
5. report artifacts where available.

Do not attach raw secrets, provider keys, unredacted PII, or private customer data to support bundles.

---

## Incident 1: DMRF injection-defense block or bypass

**Trigger:** DMRF `InjectionDefense` blocks a request, or a suspected prompt-injection attempt reaches downstream reasoning.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for confirmed bypass/exfiltration.

1. Confirm whether DMRF returned `ok=false` with `blocked:<category>` warning.
2. Capture `run_id`, query digest, trace ID, and user/session metadata.
3. Inspect DMRF step records for `injection_defense`.
4. Inspect TruthGate decision if the request reached gate evaluation.
5. Confirm no sensitive output reached the client.
6. If repeated attacks exceed policy threshold, revoke API key/session or suspend account.
7. Add/update detection patterns and regression tests.
8. Re-run security and DMRF tests before reopening affected path.

Relevant files:

- `backend/dmrf/injection_defense.py`
- `backend/dmrf/orchestrator.py`
- `tests/security/`
- `tests/truth_engine/`

---

## Incident 2: TruthGate or policy-gate failure

**Trigger:** TruthGate blocks valid traffic unexpectedly, fails to block invalid traffic, or reports budget/compliance/security anomalies.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for data exposure or safety bypass.

1. Capture request context, user, budget state, and TruthGate output.
2. Check TruthGate stats and budget routes where available.
3. Inspect compliance markers, PII detection, blocked patterns, and priority/budget logic.
4. Confirm whether DMRF correctly stopped or continued based on gate result.
5. Add targeted regression tests for the specific gate behavior.
6. Re-run canonical route/security/Truth Engine tests.

Relevant files:

- `backend/truth_engine/truth_gate/gateway.py`
- `backend/dmrf/truth_integration/gate_adapter.py`
- `backend/truth_engine/api.py`

---

## Incident 3: Low confidence or hallucination risk

**Trigger:** Truth Engine confidence, evidence freshness, or DMRF convergence policy indicates unsafe answer quality for a critical query.

**Default severity:** `SEV-2`.

1. Open Trace Explorer for the run.
2. Inspect claims vs evidence.
3. Inspect DMRF `axis_router`, `dsqp_personas`, `truth_core_plan`, and `convergence_policy` steps.
4. Check Axis 15 risk domain and Axis 17 FROST depth.
5. Re-run with higher tier or stricter evidence gate where supported.
6. If grounding remains insufficient, return safe fallback instead of unverifiable answer.
7. Identify root cause: retrieval gap, coordinate mapping gap, stale evidence, model/provider issue, or DSQP persona gap.
8. Add corrective tests or data updates.

Relevant files:

- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`
- `backend/dmrf/router.py`
- `backend/truth_engine/truth_core/engine.py`

---

## Incident 4: PII leakage risk

**Trigger:** Privacy controls, audit review, user report, or operator review identifies PII in outgoing response, logs, traces, exports, or notifications.

**Default severity:** `SEV-1`.

1. Block streaming/output path if active.
2. Contain affected sessions, traces, exports, notifications, and logs.
3. Record correlation IDs, run IDs, affected users, and export IDs.
4. Notify privacy/compliance owner.
5. Verify downstream channels did not persist raw PII.
6. Revoke or rotate affected export links/artifacts if applicable.
7. Run leakage scan over recent outputs/logs/exports.
8. Add regression coverage for the failing redaction path.

Relevant files:

- `backend/security/`
- `backend/tracing/`
- `backend/security/export_integrity.py`
- `frontend/app/settings/privacy/`

---

## Incident 5: LLM provider outage or failover

**Trigger:** Provider error rate/latency spikes, circuit breaker opens, or gateway-backed path fails.

**Default severity:** `SEV-2`; upgrade for broad outage.

1. Confirm provider status and gateway route behavior.
2. Verify the configured cloud model. The app uses one user-selected cloud model (OpenAI `gpt-5.5` or Google `gemini-3.1-pro-preview`); a key must be saved in Settings → AI/Model (or set via `OPENAI_API_KEY` / `GOOGLE_API_KEY`). With no reachable provider, gateway chat returns a clear "No active providers found" error — it does not fail silently.
3. Check `/metrics` for AI latency/error signals.
4. Confirm DMRF/TruthCore does not silently return synthetic success.
5. For provider outages (rate limit / 5xx / network): the gateway classifies the error (`invalid_api_key` 401, `rate_limited` 429, `invalid_model` 422, `network_error` 504) and surfaces it to the client. Confirm the saved key is valid and the provider's status page is healthy.
6. Post internal status update.
7. Re-enable primary provider only after sustained health.
8. Capture incident metrics for reliability review.

Relevant files:

- `backend/llm_gateway/gateway.py` — `LLMGateway`, circuit breaker, provider routing
- `backend/llm_gateway/active_model.py` — active cloud model resolution
- `backend/llm_gateway/model_defaults.py` — default model IDs per provider
- `backend/llm_gateway/api.py`
- `backend/dmrf/orchestrator.py`

---

## Incident 6: Unauthorized access attempt

**Trigger:** Unauthorized attempts on privileged endpoints, MCP tools, retention/privacy routes, or trace exports.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for data access.

1. Verify the single-owner desktop-auth gate (loopback + signed challenge; OS-level auth) is enforced on the affected route.
2. Revoke the affected session/API key and require re-authentication.
3. Revoke suspicious sessions/API keys/tokens.
4. Confirm no unauthorized read/write/export occurred.
5. Inspect canonical API auth behavior for JSON `401`/`403` response correctness.
6. Add/update route contract and security regression tests.

Relevant test areas:

- `tests/contract/`
- `tests/security/`
- `tests/integration_routes/`

---

## Incident 7: Desktop local-auth failure

**Trigger:** Desktop/Electron user cannot auto-login, signed loopback requests fail, or desktop auth is accepted outside intended runtime.

**Default severity:** `SEV-2`; upgrade to `SEV-1` if cloud mode accepts desktop trust.

1. Confirm runtime mode: local, hybrid, or cloud.
2. Confirm the listener is bound to loopback and Host/Origin are approved.
3. Check the protected desktop install secret exists and its ACL grants only the current user and LocalSystem.
4. Validate challenge nonce TTL, per-request nonce replay state, timestamp skew, and HMAC signatures.
5. If the secret is unreadable or expired, close the app, retain the encrypted file for incident evidence, and let the desktop rotate/recover it on the next controlled start. Existing sessions will be invalidated.
6. Confirm constant-time comparison and main-process IPC capability signatures are used.
7. Re-run desktop auto-login, listener, Electron, and secret-storage security tests.

Relevant files:

- `backend/security/desktop_local_auth.py`
- `frontend/lib/runtime/policy.ts`
- `frontend/contexts/AuthContext.tsx`
- `tests/integration_routes/test_desktop_auto_login_security.py`

---

## Incident 8: Local object/vector/graph store failure

**Trigger:** object store write failure, ChromaDB vector path failure, Neo4j graph connectivity failure, USKD graph load failure, or UnifiedMemory persistence failure.

**Default severity:** `SEV-2`; downgrade to `SEV-3` if isolated and non-critical.

1. Identify failing store: SQL, Redis, Neo4j, ChromaDB, object store, USKD, UnifiedMemory, or TruthMemory.
2. Check local path permissions and disk space.
3. Check object-store path validation failures: null byte, absolute path, `..` traversal, containment failure.
4. Check ChromaDB path under `./databases/chroma`.
5. Check object path under `./databases/objects`.
6. Check memory path `databases/memory/memory_graph.json`.
7. Re-run local data stack validation and schema parity checks.
8. Attach relevant report artifacts.

Relevant files:

- `backend/storage/object_store.py`
- `backend/storage/vector_store.py`
- `backend/storage/graph_store.py`
- `backend/storage/uskd_memory_graph.py`
- `backend/memory/unified_memory_service.py`
- `scripts/verify_local_data_stack.py`

---

## Incident 9: Runtime precheck or deterministic startup gate failure

**Trigger:** `runtime_precheck.py --strict` fails in CI, deploy, local release prep, or production startup.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for production boot blocker.

1. Compare `/live` and `/ready`. A live process that reports not ready is an
   expected fail-closed state, not permission to bypass startup.
2. Review readiness blockers and authenticated
   `/api/v1/system/capabilities`; record phase, service state, safe reason,
   expected/observed identity, and active lifecycle operation.
3. Review generated runtime precheck JSON report and address blocker/action findings.
4. Confirm production uses PostgreSQL, `AUTO_CREATE_SCHEMA=true` is absent, and
   every required service is configured.
5. Confirm `SESSION_SECRET` and required secrets are configured through an
   approved protected source.
6. If `runtime_already_owned` is reported, identify the owning DataLogicEngine
   process/session. Do not delete the lock while that owner is alive.
7. If the installation owner/version differs, stop and use repair/update; never
   attach one Windows user or version to another runtime root.
8. If a configured port is foreign, stop/configure the named product or select
   an approved DataLogicEngine port. Never reuse the listener as healthy.
9. Confirm dependency and lockfile metadata are aligned.
10. Re-run precheck with matching flags:
   ```powershell
   python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
   ```
11. Re-run the startup-side-effect and deterministic failure matrix before the
    CI/deploy workflow after remediation.

Relevant files:

- `scripts/runtime_precheck.py`
- `scripts/verify_lockfiles.py`
- `scripts/verify_environment_parity.py`
- `scripts/verify_startup_side_effects.py`
- `backend/runtime/`

---

## Incident 10: Schema parity or migration failure

**Trigger:** schema parity validation fails, migration fails, or startup detects DB/schema mismatch.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for sustained production outage.

1. Capture DB backend type and schema report.
2. Run:
   ```powershell
   python .\scripts\validate_schema_parity.py --report reports\schema_parity_report_incident.json
   ```
3. Confirm migrations were applied where migration-managed SQL is used.
4. Confirm `AUTO_CREATE_SCHEMA=true` was not used as a production workaround.
5. Inspect recent model/migration changes.
6. Add regression or migration test coverage.

Relevant files:

- `models.py`
- `migrations/`
- `scripts/validate_schema_parity.py`

---

## Incident 11: Installer signature verification failure

**Trigger:** Windows signing workflow reports invalid/missing Authenticode signatures.

**Default severity:** `SEV-1` for release blockers; `SEV-2` for pre-release smoke failures.

1. Review `reports/installer_signature_report.json`.
2. Confirm certificate validity window and thumbprint against release policy.
3. Re-run verification locally:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts
   ```
4. If signature is missing/invalid, rerun signing workflow after correcting certificate secret material.
5. Block release distribution until signature status is valid for all installer artifacts.

Relevant files:

- `.github/workflows/release-installer-signing.yml`
- `scripts/windows/verify_signing_certificate_health.ps1`
- `scripts/windows/sign_release_installers.ps1`
- `scripts/windows/verify_installer_signature.ps1`

---

## Incident 12: Packaging smoke, installer integrity, or NSIS governance failure

**Trigger:** Windows packaging smoke fails, installer integrity verification fails, installer launch/install/uninstall smoke fails, or NSIS governance check fails.

**Default severity:** `SEV-2`; `SEV-1` if release distribution is blocked.

1. Review packaging smoke, installer integrity, installer-mode smoke, and NSIS governance reports.
2. Re-run locally:
   ```powershell
   .\.venv\Scripts\python.exe scripts\build_backend.py
   $env:CSC_SKIP = "true"
   npm --prefix frontend run electron:dist
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
   .\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
   ```
3. Check backend executable build output.
4. Check Electron distribution output.
5. Check antivirus/file-lock issues.
6. Block release until smoke passes.

Relevant files:

- `scripts/windows/run_packaging_smoke.ps1`
- `scripts/windows/verify_nsis_governance.ps1`
- `scripts/verify_installer_integrity.py`
- `.github/workflows/ci.yml`

---

## Incident 13: Export authenticity or audit integrity failure

**Trigger:** trace export signing/encryption/hash validation fails, audit chain continuity fails, or immutable audit replica check fails.

**Default severity:** `SEV-1` for evidence integrity impact; `SEV-2` for isolated export failure.

1. Capture failing run/export/audit identifiers.
2. Capture manifest, section hashes, bundle hash, signature, and encryption metadata.
3. Verify HMAC secret and encryption key source.
4. Re-run integrity tests:
   ```powershell
   python -m pytest -q --no-cov tests/unit/test_export_authenticity_controls.py tests/security/test_audit_logger_immutable_replica.py
   ```
5. Regenerate affected export bundles if safe.
6. Verify audit chain continuity before closing incident.

Relevant files:

- `backend/security/export_integrity.py`
- `backend/truth_engine/truth_memory/manager.py`
- `backend/tracing/`

---

## Incident 14: MCP connector scope or contract failure

**Trigger:** repeated `MCP_SCOPE_DENIED`, connector contract validation errors, connector credential/token-source failures, or connector output schema drift.

**Default severity:** `SEV-2`.

1. Capture connector, tool, payload, user context, and contract error.
2. Confirm scope denial is expected policy behavior rather than auth regression.
3. Validate principal-to-scope mapping and connector credential/token-source state.
4. Check declared input/output schemas.
5. Roll back connector/tool contract change if regression was introduced.
6. Add/update MCP route and contract tests.

Relevant files:

- `backend/mcp_server/`
- `backend/routes/mcp_routes.py`
- `frontend/components/mcp/`
- `tests/contract/`

---

## Incident 15: AI, connector, or route latency SLO violation

**Trigger:** `/metrics` reports sustained p95/p99 SLO violations for AI, connector, or canonical API route paths.

**Default severity:** `SEV-2`; upgrade to `SEV-1` for broad service degradation.

1. Inspect AI/connector latency metrics.
2. Inspect route-level request telemetry:
   - `datalogicengine_http_requests_by_route_total{route="...",status="5xx"}`
   - `datalogicengine_http_request_latency_ms_avg{route="..."}`
   - `datalogicengine_http_request_latency_ms_max{route="..."}`
   - unmatched `4xx` route noise.
3. Correlate with provider/connector error rate and fallback activity.
4. Check DMRF tier counts and FROST depth metrics if reasoning requests are slow.
5. Apply mitigation: traffic shaping, provider failover, connector backoff, temporary routing constraints, or degraded safe mode.
6. Re-baseline thresholds only after postmortem and governance approval.

---

## Incident 16: Frontend API boundary or trace-review failure

**Trigger:** frontend fails to render answer, trace, run detail, graph view, Truth Engine monitor, MCP hub, admin page, or privacy/disclosure page.

**Default severity:** `SEV-2`; `SEV-3` for isolated non-critical UI failure.

1. Capture browser console and client error telemetry.
2. Confirm `ApiErrorBoundary` rendered recoverable failure state.
3. Check frontend API client route and backend response shape.
4. Validate `/api/v1/*` canonical route behavior.
5. Check SWR retry/caching behavior.
6. Re-run frontend unit/E2E/visual tests.

Relevant files:

- `frontend/components/ui/api-error-boundary.tsx`
- `frontend/lib/api/`
- `frontend/app/runs/`
- `frontend/app/chat/`
- `frontend/app/truth-engine/`

---

## Incident 17: Electron file capability, secret, or listener boundary failure

**Trigger:** expired/invalid picker token, renderer path submission, failed ACL,
secret value in a log/backup, untrusted Host/Origin, or attempted non-loopback bind.

**Default severity:** `SEV-1` for secret disclosure or listener exposure;
otherwise `SEV-2`.

1. Stop the desktop backend and preserve redacted evidence.
2. Do not work around the failure with `0.0.0.0`, wildcard CORS, disabled web
   security, plaintext `.env`, or relaxed ACLs.
3. Run the four Phase 1 mandatory gates and the focused network/secret suites.
4. Verify picker tokens are single-use/expiring and path operations carry the
   main-process purpose signature.
5. Verify provider/internal credentials remain DPAPI-protected and the backup
   contains none of `.env`, settings, logs, secret, or key files.
6. Private listener requests remain blocked until Phase 8 qualification.

---

## Incident 18: Runtime ownership, readiness, or shutdown failure

**Trigger:** second launch is refused unexpectedly, the shell opens before
readiness, a service is reported ready under foreign identity, mutation traffic
continues during drain, Windows lifecycle events are not reconciled, or an app
listener remains after shutdown.

**Default severity:** `SEV-1` for cross-user/foreign-service attachment, data
corruption, or continued writes during shutdown; otherwise `SEV-2`.

1. Stop new user activity and preserve redacted `/ready`, capabilities, runtime
   logs, `installation.json`, and lock metadata.
2. Do not delete installation/lock files or kill an unrelated port owner until
   process, user, session, version, and product identity are verified.
3. Confirm Electron waited on `/ready` and did not substitute `/health`.
4. Verify the event was one of suspend, hibernate, resume, logoff, shutdown,
   time change, or forced termination and that signed desktop auth was present.
5. During drain, confirm new mutations receive `RUNTIME_NOT_ACCEPTING_WORK`.
6. Run bounded stop, then verify ports 3000/5000 and app-owned child processes
   are closed. Use forced cleanup only after the graceful budget expires.
7. Run the repeated start/status/stop, crash/stale-lock, cross-user, lifecycle,
   foreign-identity, low/read-only disk, and Electron active-request tests.
8. Do not claim production recovery until every required service returns the
   expected identity and `ready` state.

Relevant files:

- `backend/runtime/application.py`
- `backend/runtime/ownership.py`
- `backend/runtime/supervisor.py`
- `frontend/electron/main.ts`
- `frontend/electron/lifecycle.ts`
- `scripts/windows/start_local_stack.ps1`
- `scripts/windows/stop_local_stack.ps1`

---

## Validation checklist after any incident

1. `GET /health` is healthy.
2. `GET /live` is healthy.
3. `GET /ready` is healthy.
4. Authenticated `GET /metrics` returns expected metrics.
5. Core auth flow works for the expected owner/principal path.
6. Gateway/DMRF request path returns expected policy behavior.
7. Truth Engine health/status is normal where enabled.
8. Trace Explorer can open relevant run or appropriate fallback.
9. Object/vector/graph stores are healthy if incident touched data path.
10. Error rates and latency return to baseline.
11. New regression test exists when incident exposed a product defect.
12. Incident report and follow-up actions are recorded.

## Change notes for v2.10.0

1. Added the supervisor-authoritative five-service operating boundary and
   foreign-resource refusal rule.
2. Documented the intentional managed-backup refusal pending Phase 4 coordinated
   recovery, preventing partial backups from being treated as safe.

## Change notes for v2.9.0

1. Added runtime ownership/readiness/shutdown incident response and expanded
   startup triage for phase failure, lock/version/user conflicts, foreign service
   identity, mutation drain, and stale-owner recovery.

## Change notes for v2.8.0

1. Added replay/rotation recovery steps and the Electron file/secret/listener incident runbook.

## Change notes for v2.7.0

1. Expanded packaging incident handling to include backend rebuild, installer integrity verification, and installer-mode install/uninstall smoke.
2. Replaced stale MCP OAuth/role language with connector credential, token-source, principal, and scope wording.
3. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated runbooks for current DMRF, Truth Engine, local-first desktop auth, multi-store data, trace/export integrity, and packaging architecture.
3. Added incidents for DMRF injection defense, TruthGate, desktop local auth, schema parity, packaging smoke, frontend trace review, and local storage failures.
4. Updated support bundle and validation checklist guidance.
5. Added implementation file references for each incident path.
