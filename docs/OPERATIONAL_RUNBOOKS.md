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
2. Last updated: 2026-02-08
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

## Validation checklist after any incident

1. `GET /health` is healthy.
2. Core auth flow works for expected roles.
3. Gateway request path returns expected policy behavior.
4. Error rates and latency return to baseline.
5. Incident report and follow-up actions are recorded.

