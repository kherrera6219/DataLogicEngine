# Operational Runbooks

## Purpose

Provide incident-response procedures for common DataLogicEngine security and runtime failures.

## Audience

1. On-call engineers
2. Security operations
3. SRE/platform operations
4. Compliance operations

## Document control

1. Owner: SRE + Security Operations
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/SECURITY.md`
2. `docs/PRODUCTION_READINESS.md`
3. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
4. `docs/DEPLOYMENT.md`

## Severity model

1. `SEV-1`: Active data exposure, sustained outage, or auth compromise.
2. `SEV-2`: Partial outage, degraded reasoning quality, or repeated security control failures.
3. `SEV-3`: Localized issue with no broad customer impact.

## Global incident workflow

1. Acknowledge incident and set severity.
2. Capture correlation IDs, tenant/user scope, and event timestamps.
3. Contain impact before optimization.
4. Execute incident-specific runbook.
5. Validate recovery with health checks and user-path checks.
6. Create post-incident report with remediation actions.
7. Generate and attach a sanitized support bundle for incident evidence.

## Support bundle capture

Use the support-bundle generator to collect bounded diagnostics for handoff/escalation:

```powershell
python .\scripts\generate_support_bundle.py
```

Options for offline collection:

```powershell
python .\scripts\generate_support_bundle.py --skip-http --max-files-per-group 5
```

Bundle content includes:

1. Sanitized environment snapshot.
2. Git and runtime precheck snapshots.
3. Recent logs and reports (bounded size).
4. Optional health/ready/metrics probe output.

## Incident 1: Prompt-injection attempt detected

**Trigger:** `KA-61 Adversarial Input Shield` logs a high-severity injection attempt.
**Default severity:** `SEV-2` (upgrade to `SEV-1` for active bypass/exfiltration)

1. Confirm request was blocked.
2. Retrieve session trace and audit logs.
3. Extract `user_id`, `tenant_id`, source IP, and request payload metadata.
4. Suspend account or key when repeated attacks exceed policy threshold.
5. Add detection signature updates and open a security follow-up task.
6. Validate no sensitive output was returned to client.

## Incident 2: Low-confidence/hallucination risk

**Trigger:** Truth engine confidence below policy threshold for critical query class.
**Default severity:** `SEV-2`

1. Re-run using higher reasoning depth/tier with stricter evidence gating.
2. Inspect trace "claims vs evidence" chain.
3. If grounding is insufficient, return safe fallback response (no unverifiable answer).
4. Identify root cause:
   - retrieval gap
   - coordinate mapping gap
   - provider degradation
5. File corrective action for retrieval/model/routing owner.

## Incident 3: PII leakage risk in response

**Trigger:** Privacy controls flag PII in outgoing response.
**Default severity:** `SEV-1`

1. Block streaming/output response path immediately.
2. Apply redaction/sanitization policy.
3. Notify privacy/compliance contact.
4. Record event in audit log with trace correlation.
5. Verify downstream channels (logs/webhooks/notifications) did not persist raw PII.
6. Run post-incident leakage scan over recent outputs.

## Incident 4: LLM provider outage/failover

**Trigger:** Circuit breaker opens for a configured provider.
**Default severity:** `SEV-2`

1. Confirm automatic failover is active.
2. Validate latency, error rate, and cost on fallback provider.
3. Post status update to internal operations channel.
4. Monitor primary provider and re-enable only after sustained health.
5. Capture incident metrics for reliability review.

## Incident 5: Unauthorized access / RBAC violation

**Trigger:** Unauthorized access attempts on privileged endpoints.
**Default severity:** `SEV-2` (upgrade to `SEV-1` for privilege escalation evidence)

1. Verify role/permission mapping for the principal.
2. Force re-authentication and MFA challenge for affected account.
3. Revoke suspicious tokens/keys.
4. Confirm no unauthorized data read/write occurred.
5. Capture logs for security investigation and policy refinement.

## Incident 6: MCP connector scope denial surge

**Trigger:** Repeated `MCP_SCOPE_DENIED` errors from MCP tool calls.
**Default severity:** `SEV-2`

1. Confirm scope denials are expected policy outcomes (not auth regression).
2. Validate role-to-scope mapping and API key permission payloads.
3. Check whether tenant/user context propagation is missing from calling surface.
4. Review denied tool list and required scopes for noisy patterns.
5. If legitimate business flow is blocked, open controlled RBAC/scope change request.

## Incident 7: SSRF protection blocks upstream integration

**Trigger:** API gateway returns blocked-upstream error due to SSRF policy.
**Default severity:** `SEV-2`

1. Capture blocked URL, requested host, and calling endpoint.
2. Validate target host is expected and mapped in service registry.
3. If valid destination, update approved upstream allowlist through change control.
4. If destination is unexpected, treat as potential security event and contain source.
5. Re-run health and integration checks after policy update.

## Incident 8: Connector contract validation failures

**Trigger:** MCP tool calls fail with contract validation errors.
**Default severity:** `SEV-2`

1. Capture tool name, payload, and contract violation message.
2. Confirm request payload matches declared `inputSchema` for the tool.
3. Confirm connector response shape still matches declared `outputSchema`.
4. Roll back connector/tool contract change if regression was introduced.
5. Add/update tests for contract boundary before re-release.

## Incident 9: Deterministic startup gate failure in CI/deploy

**Trigger:** `runtime_precheck.py --strict ...` gate fails in CI/deploy.
**Default severity:** `SEV-2`

1. Review generated runtime precheck JSON report artifact from workflow.
2. Address failing blocker/action findings (config, dependencies, or startup prerequisites).
3. Re-run precheck locally with matching flags:
   `python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process`
4. Re-run pipeline after remediation and attach updated report evidence.

## Incident 10: Installer signature verification failure

**Trigger:** Windows release signing workflow reports invalid/missing Authenticode signatures.
**Default severity:** `SEV-1` for release blockers, `SEV-2` for pre-release smoke failures

1. Review `reports/installer_signature_report.json` from signing workflow artifacts.
2. Confirm certificate validity window and thumbprint against release policy.
3. Re-run signature verification locally:
   `powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts`
4. If signature missing/invalid, re-run signing workflow after correcting certificate secret material.
5. Block release distribution until signature status is `Valid` for all installer artifacts.

## Validation checklist after any incident

1. `GET /health` is healthy.
2. Core auth flow works for expected roles.
3. Gateway request path returns expected policy behavior.
4. Error rates and latency return to baseline.
5. Incident report and follow-up actions are recorded.
