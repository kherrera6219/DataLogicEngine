# Process Maps — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Engineers, product managers, QA, technical reviewers |
| Review cadence | Every 60 days |
| Notation | BPMN-inspired process maps rendered in Mermaid |

## Purpose

Describe the major business and technical processes in the current DataLogicEngine architecture.

This version aligns process flows with local-first desktop operation, Flask/API security envelope, DMRF, Truth Engine, 17-axis routing, DSQP, MCP, trace/export, privacy, testing, and release governance.

---

## PM-01: Runtime start and authentication

```mermaid
flowchart TD
    START([Start application]) --> FACTORY[Create isolated Flask application]
    FACTORY --> CONFIG[Validate configuration]
    CONFIG --> PATHS[Resolve runtime root and ACL]
    PATHS --> LOCK{Installation identity and runtime lock valid?}
    LOCK -- No --> REFUSE[Safe refusal or repair action]
    LOCK -- Yes --> SUP[Start one service supervisor]
    SUP --> VERIFY[Verify service identity/version/credentials]
    VERIFY --> MIGRATE[Migrations and store compatibility]
    MIGRATE --> STORES[Initialize app-owned stores and workers]
    STORES --> READY{Core ready?}
    READY -- No --> DEGRADED[Keep shell closed; show safe blocker]
    READY -- Yes --> MODE{Runtime mode?}

    MODE -- Desktop --> ELECTRON[Electron receives /ready]
    ELECTRON --> DAUTH[Desktop local-auth challenge]
    DAUTH --> DOK{Nonce/HMAC/timestamp valid?}
    DOK -- No --> DENY[Reject local auth]
    DOK -- Yes --> DASH[Open dashboard]

    MODE -- Web/internal --> WEB[Open browser UI]
    WEB --> LOGIN[Login/session flow]
    LOGIN --> AUTHOK{Authenticated?}
    AUTHOK -- No --> DENYWEB[401/403 or login challenge]
    AUTHOK -- Yes --> DASH
```

---

## PM-02: Governed AI request lifecycle

```mermaid
flowchart TD
    USER[User submits prompt/action] --> API[API request]
    API --> SEC[Security envelope]
    SEC --> INJ[DMRF InjectionDefense]
    INJ --> INJDEC{Allowed?}
    INJDEC -- No --> BLOCK[Structured block + audit/trace]
    INJDEC -- Yes --> TG[TruthGate]
    TG --> TGDEC{Allow / warn / block?}
    TGDEC -- Block --> BLOCK
    TGDEC -- Allow/Warn --> TIER[TierClassifier]
    TIER --> AXIS[17-axis route]
    AXIS --> DSQP[DSQP persona construction]
    DSQP --> PLAN[TruthCore plan]
    PLAN --> EXEC{External execution needed?}
    EXEC -- Provider --> LLM[LLM Gateway]
    EXEC -- Tool --> MCP[MCP connector]
    EXEC -- No --> LOCAL[Local deterministic processing]
    LLM --> EVID[Evidence + convergence]
    MCP --> EVID
    LOCAL --> EVID
    EVID --> FINAL{Converged?}
    FINAL -- No --> PLAN
    FINAL -- Yes --> TRACE[Persist memory/audit/trace]
    TRACE --> RESP[Return response]
```

---

## PM-03: Provider configuration and execution

```mermaid
flowchart TD
    CONFIG[User/admin configures provider] --> SAVE[Save provider settings]
    SAVE --> TEST[Test provider connection]
    TEST --> OK{Valid?}
    OK -- No --> ERR[Show failure reason]
    OK -- Yes --> ENABLE[Provider available for workflows]
    ENABLE --> REQUEST[Workflow requests model execution]
    REQUEST --> SECRET[Resolve provider secret]
    SECRET --> CALL[Call configured provider]
    CALL --> RESULT{Success?}
    RESULT -- No --> FAIL[Structured provider failure]
    RESULT -- Yes --> USAGE[Record latency/usage/error metadata]
    USAGE --> RETURN[Return to TruthCore]
```

---

## PM-04: MCP connector workflow

```mermaid
flowchart TD
    ADMIN[Admin configures connector] --> REG[Register connector]
    REG --> SCOPE[Define scopes/permissions]
    SCOPE --> TEST[Test connector]
    TEST --> READY{Ready?}
    READY -- No --> FIX[Fix config/credentials]
    READY -- Yes --> USE[Workflow requests tool]
    USE --> CHECK[Scope + contract validation]
    CHECK --> ALLOW{Allowed?}
    ALLOW -- No --> DENY[Deny + audit]
    ALLOW -- Yes --> CALL[Execute connector call]
    CALL --> VALIDATE[Validate response contract]
    VALIDATE --> TRACE[Record trace/metrics]
    TRACE --> RETURN[Return tool result]
```

---

## PM-05: Trace review and export

```mermaid
flowchart TD
    RUN[Workflow completes] --> TRACE[Persist run trace]
    TRACE --> REVIEW[User opens Trace Explorer]
    REVIEW --> SECTIONS[Inspect stages/evidence/claims/policy/personas]
    SECTIONS --> EXPORT{Export requested?}
    EXPORT -- No --> DONE[Review complete]
    EXPORT -- Yes --> HASH[Generate section and bundle hashes]
    HASH --> MANIFEST[Generate export manifest]
    MANIFEST --> SIGN{HMAC enabled?}
    SIGN -- Yes --> HMAC[Attach signature]
    SIGN -- No --> NOSIGN[Unsigned manifest]
    HMAC --> DOWNLOAD[Download export bundle]
    NOSIGN --> DOWNLOAD
```

---

## PM-06: Privacy export/delete process

```mermaid
flowchart TD
    USER[Owner requests privacy action] --> AUTH[Auth and single-owner check]
    AUTH --> ACTION{Export or delete?}
    ACTION -- Export --> COLLECT[Collect eligible user data]
    COLLECT --> PACKAGE[Package export]
    PACKAGE --> MANIFEST[Generate manifest/hash]
    MANIFEST --> DOWNLOAD[Download]
    ACTION -- Delete --> SCOPE[Resolve deletion scope]
    SCOPE --> RETENTION{Retention/audit constraint?}
    RETENTION -- Yes --> PARTIAL[Delete/anonymize eligible fields]
    RETENTION -- No --> DELETE[Delete eligible data]
    PARTIAL --> AUDIT[Audit event]
    DELETE --> AUDIT
    AUDIT --> CONFIRM[Confirmation]
```

---

## PM-07: Local data service lifecycle

```mermaid
flowchart TD
    START[Start local stack] --> PRECHECK[Runtime precheck]
    PRECHECK --> OWNER{Configured port and identity app-owned?}
    OWNER -- Foreign --> REFUSE[Refuse reuse and return repair action]
    OWNER -- Owned/free --> SERVICES[Supervisor starts services in dependency order]
    SERVICES --> HEALTH[Identity and service-specific probes]
    HEALTH --> OK{Every required service ready?}
    OK -- No --> BLOCK[Publish not-ready and safe per-service reason]
    OK -- Yes --> APP[Publish /ready and capabilities]
    APP --> EVENT{Stop, backup, update, sleep, or logoff?}
    EVENT --> DRAIN[Reject new mutations and drain admitted work]
    DRAIN --> CLEAN[Checkpoint/stop with bounded cleanup]
    CLEAN --> RELEASE[Release runtime lock and reconcile on resume/restart]
```

---

## PM-08: Incident/support process

```mermaid
flowchart TD
    ISSUE[User/operator reports issue] --> TRIAGE[Triage severity]
    TRIAGE --> COLLECT[Collect logs/metrics/support bundle]
    COLLECT --> SANITIZE[Sanitize secrets/PII]
    SANITIZE --> CLASSIFY{Security/privacy impact?}
    CLASSIFY -- Yes --> SECURITY[Follow security/privacy response]
    CLASSIFY -- No --> OPS[Operational remediation]
    SECURITY --> FIX[Fix/mitigate]
    OPS --> FIX
    FIX --> VALIDATE[Run validation checks]
    VALIDATE --> CLOSE[Document outcome]
```

---

## PM-09: Release process

```mermaid
flowchart TD
    CHANGE[Release candidate change set] --> TESTS[Run backend/frontend/security/parity tests]
    TESTS --> GOV[Run governance checks]
    GOV --> PACKAGE{Desktop release?}
    PACKAGE -- Yes --> BUILD[Rebuild PyInstaller backend + Electron/NSIS package]
    BUILD --> INTEGRITY[Verify installer integrity]
    INTEGRITY --> SMOKE[Run portable and installer-mode smoke]
    PACKAGE -- No --> READY[Readiness review]
    SMOKE --> SIGN{Public signed release?}
    SIGN -- Yes --> VERIFY[Verify trusted signature/artifacts]
    SIGN -- No --> READY
    VERIFY --> READY
    READY --> DECISION{Evidence complete?}
    DECISION -- No --> BLOCK[Block or waive with caveat]
    DECISION -- Yes --> RELEASE[Approve release]
```

---

## PM-10: Vulnerability response

```mermaid
flowchart TD
    REPORT[Vulnerability report] --> ACK[Acknowledge/report intake]
    ACK --> TRIAGE[Security triage]
    TRIAGE --> SEV{Severity?}
    SEV -- Critical/High --> HOTFIX[Hotfix path]
    SEV -- Medium/Low --> BACKLOG[Planned remediation]
    HOTFIX --> PATCH[Patch + tests]
    BACKLOG --> PATCH
    PATCH --> VERIFY[Security/regression validation]
    VERIFY --> RELEASE[Release or document fix]
    RELEASE --> DISCLOSE[Coordinate disclosure where applicable]
```

## Change notes for v2.8.0

1. Replaced the legacy runtime maps with the implemented factory, installation
   lock, phased startup, truthful readiness, identity-aware supervision,
   admission drain, and Windows lifecycle flow.

## Change notes for v2.7.0

1. Updated the release process map to include backend rebuild, Electron/NSIS packaging, installer integrity verification, and installer-mode smoke before signing review.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older Active Defense, SID auto-login, Knowledge Engine, and QuadPersona process flows with current DMRF/Truth Engine/DSQP/local-first process flows.
3. Added trace/export, privacy, local data lifecycle, incident, release, and vulnerability processes.
