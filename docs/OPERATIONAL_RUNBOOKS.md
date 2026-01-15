# Operational Runbooks: Incident Response
## DataLogicEngine (UKG) Enterprise Operations

This document provides step-by-step procedures for responding to security and operational incidents within the UKG system.

---

### Incident 1: Detected Prompt Injection Attempt
**Trigger:** `KA-61 Adversarial Input Shield` logs a high-severity injection attempt.

1.  **Isolate:** The system automatically blocks the request.
2.  **Audit:** Retrieve the session logs via the Admin Dashboard.
3.  **Identify:** Extract the `user_id`, `tenant_id`, and source IP.
4.  **Action:** Temporarily suspend the user account if the attempt was repeated (>3 times).
5.  **Refine:** Update the `KA-61` blocklist or regex patterns if the injection bypassed initial filters.

---

### Incident 2: High Entropy/Hallucination Detection
**Trigger:** `TruthCore` reports a confidence score below 85% for a critical query.

1.  **Retry:** Execute the query with a higher reasoning tier (e.g., Tier 5).
2.  **Verify:** Manually inspect the "Claims vs Evidence" mapping in the Trace Explorer.
3.  **Mitigation:** If evidence is lacking, return a "No verified knowledge found" response instead of a generative guess.
4.  **Root Cause:** Identify if the knowledge gap is in the vector database or if the coordinate mapping was too broad.

---

### Incident 3: Data Leakage Detection (PII)
**Trigger:** `KA-59 Privacy Filter` detects PII in an LLM outgoing response.

1.  **Block:** Immediately stop the stream or block the JSON response.
2.  **Scrub:** Sanitize the PII using `Presidio` or local replacement logic.
3.  **Alert:** Notify the Tenant Privacy Officer (DPO) via the Compliance API.
4.  **Log:** Record the event in the Hash-Chained Audit Log for regulatory reporting (GDPR/HIPAA).

---

### Incident 4: Infrastructure Failover (LLM Provider Down)
**Trigger:** Circuit breaker opens for OpenAI/Azure.

1.  **Automatic:** System fails over to the secondary provider (e.g., Anthropic).
2.  **Manual Check:** Verify the latency and token usage on the secondary provider.
3.  **Communication:** Update the system status on the dashboard (/health).
4.  **Recovery:** Once the primary provider status is "Healthy" for 5 consecutive pings, reset the circuit breaker.

---

### Incident 5: Unauthorized Access (RBAC Violation)
**Trigger:** Middleware logs a 403 Forbidden for a sensitive endpoint.

1.  **Verify:** Check if the user has the required permission (`security:read`, etc.).
2.  **Re-Auth:** Require the user to re-verify via MFA.
3.  **Log:** Record the attempt in the security audit logs for threat modeling.
4.  **Protect:** If the request originated from a rotated API key, revoke the key immediately.
