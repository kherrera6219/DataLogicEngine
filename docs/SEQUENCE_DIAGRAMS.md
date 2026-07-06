# Sequence Diagrams — DataLogicEngine

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Architecture |
| Audience | Software engineers, architects, QA, API integrators |
| Review cadence | Every 60 days |
| Notation | Mermaid UML sequence diagrams |

## Purpose

Document key runtime sequences in the current DataLogicEngine architecture.

This version aligns sequence diagrams with the local-first desktop trust model, canonical API behavior, DMRF, Truth Engine, 17-axis routing, DSQP, provider/tool execution, trace/export, privacy, and release governance.

---

## SD-01: Desktop local-auth sequence

```mermaid
sequenceDiagram
    participant Electron as Electron Shell
    participant Runtime as Frontend Runtime Policy
    participant API as Flask API
    participant Auth as DesktopLocalAuth
    participant DPAPI as DPAPI / Local Secret Store
    participant Session as Session/Auth Context

    Electron->>Runtime: Start local desktop session
    Runtime->>API: Request local auth challenge over loopback
    API->>Auth: Create nonce challenge
    Auth->>DPAPI: Resolve install secret where available
    DPAPI-->>Auth: Secret material / protected value
    Auth-->>API: Nonce + timestamp challenge
    API-->>Runtime: Challenge response
    Runtime->>Electron: Sign challenge with local secret
    Electron-->>Runtime: HMAC signature
    Runtime->>API: Submit nonce + timestamp + HMAC
    API->>Auth: Verify timestamp skew and constant-time HMAC
    alt Valid local desktop context
        Auth-->>API: Accepted
        API->>Session: Create local session/context
        API-->>Runtime: 200 OK
    else Invalid or non-local context
        Auth-->>API: Reject
        API-->>Runtime: 401/403 JSON response
    end
```

---

## SD-02: Web/cloud API auth failure sequence

```mermaid
sequenceDiagram
    participant Client as API Client
    participant API as Flask API
    participant Sec as Security Envelope
    participant Route as Canonical /api/v1 Route

    Client->>API: Request /api/v1/* without valid auth
    API->>Sec: Apply CSRF/CORS/trusted-host/rate-limit checks
    Sec->>Route: Evaluate auth decorator
    alt Auth missing or invalid
        Route-->>API: JSON 401/403
        API-->>Client: JSON error, no browser redirect
    else Auth valid
        Route-->>API: Continue route handling
        API-->>Client: JSON response
    end
```

---

## SD-03: Governed AI request sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend UI
    participant API as Flask API
    participant DMRF as DMRF Orchestrator
    participant Inject as InjectionDefense
    participant Gate as TruthGate
    participant Tier as TierClassifier
    participant Axis as 17-Axis Router
    participant DSQP as DSQP
    participant Core as TruthCore
    participant Evidence as Evidence/Convergence
    participant Memory as Memory/Trace Stores

    User->>UI: Submit prompt/action
    UI->>API: POST canonical API request
    API->>API: Auth, CSRF, CORS, trusted-host, rate-limit checks
    API->>DMRF: Start governed lifecycle
    DMRF->>Inject: Analyze prompt/context
    alt Injection blocked
        Inject-->>DMRF: Block decision
        DMRF-->>API: Structured block
        API-->>UI: Block response + trace metadata
    else Allowed
        Inject-->>DMRF: Allowed/warn
        DMRF->>Gate: Evaluate TruthGate context
        alt Gate blocks
            Gate-->>DMRF: Block
            DMRF-->>API: Structured block
            API-->>UI: Block response
        else Gate allows
            Gate-->>DMRF: Allow/warn
            DMRF->>Tier: Classify tier
            DMRF->>Axis: Resolve 17-axis route
            DMRF->>DSQP: Build personas if needed
            DMRF->>Core: Execute TruthCore plan
            Core->>Evidence: Score evidence/convergence
            Evidence->>Memory: Persist memory/audit/trace
            Memory-->>Evidence: Stored
            Evidence-->>Core: Final result
            Core-->>DMRF: Governed response
            DMRF-->>API: Response envelope
            API-->>UI: Response + trace affordance
        end
    end
```

---

## SD-04: Provider execution sequence

```mermaid
sequenceDiagram
    participant Core as TruthCore
    participant Gateway as LLM Gateway
    participant Secrets as Secret Resolver
    participant Provider as Configured AI Provider
    participant Metrics as Usage/Metrics

    Core->>Gateway: Request provider execution
    Gateway->>Secrets: Resolve provider key/config
    alt Missing provider config
        Secrets-->>Gateway: Unavailable
        Gateway-->>Core: Structured provider error
    else Config available
        Secrets-->>Gateway: Provider config
        Gateway->>Provider: Send selected prompt/context
        alt Provider success
            Provider-->>Gateway: Model response
            Gateway->>Metrics: Record latency/usage
            Gateway-->>Core: Provider result
        else Provider failure
            Provider-->>Gateway: Error/timeout
            Gateway->>Metrics: Record failure
            Gateway-->>Core: Structured provider failure
        end
    end
```

---

## SD-05: MCP tool execution sequence

```mermaid
sequenceDiagram
    participant Core as TruthCore/API
    participant MCP as MCP Server
    participant Scope as Scope Enforcement
    participant Contract as Contract Validation
    participant Tool as External Tool/API
    participant Trace as Trace/Metrics

    Core->>MCP: Request tool execution
    MCP->>Scope: Check connector/tool scopes
    alt Scope denied
        Scope-->>MCP: Deny
        MCP->>Trace: Audit denial
        MCP-->>Core: Policy denial
    else Scope allowed
        Scope-->>MCP: Allowed
        MCP->>Contract: Validate request contract
        alt Request invalid
            Contract-->>MCP: Reject
            MCP-->>Core: Contract error
        else Request valid
            MCP->>Tool: Execute external call
            Tool-->>MCP: Tool result
            MCP->>Contract: Validate response contract
            MCP->>Trace: Record trace/metrics
            MCP-->>Core: Validated tool result
        end
    end
```

---

## SD-06: Trace review and export sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Trace Explorer
    participant API as Trace API
    participant Store as Trace/Memory Store
    participant Integrity as Export Integrity
    participant Download as Export Bundle

    User->>UI: Open run/trace
    UI->>API: GET trace details
    API->>Store: Fetch run, stages, evidence, claims, policy/personas
    Store-->>API: Trace data
    API-->>UI: Trace view model
    User->>UI: Request export
    UI->>API: POST export request
    API->>Integrity: Build section hashes and manifest
    alt HMAC/encryption enabled
        Integrity->>Integrity: Sign and/or encrypt export
    else Plain manifest
        Integrity->>Integrity: Attach hashes only
    end
    Integrity-->>API: Export artifact metadata
    API-->>Download: Create bundle
    Download-->>UI: Download ready
```

---

## SD-07: Privacy export/delete sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Privacy UI
    participant API as Privacy API
    participant Auth as Auth/Single-Owner Check
    participant Stores as Data Stores
    participant Audit as Audit Log

    User->>UI: Request export or delete
    UI->>API: Submit privacy action
    API->>Auth: Verify owner/principal/session
    alt Export
        API->>Stores: Collect eligible user data
        Stores-->>API: Data package
        API->>Audit: Record export event
        API-->>UI: Download/export response
    else Delete
        API->>Stores: Resolve eligible deletion/anonymization scope
        Stores-->>API: Applied changes
        API->>Audit: Record deletion/anonymization event
        API-->>UI: Confirmation
    end
```

---

## SD-08: Local data service health sequence

```mermaid
sequenceDiagram
    participant Operator as User/Operator
    participant Script as Windows Local Stack Script
    participant Services as SQL/Redis/Neo4j/Chroma/Object Store
    participant API as Flask API
    participant Health as Health/Readiness API

    Operator->>Script: Start local stack
    Script->>Services: Start/check services
    Services-->>Script: Service states
    Script->>API: Start/connect backend
    API->>Health: Run health/readiness checks
    Health->>Services: Probe storage/services
    Services-->>Health: Health results
    Health-->>API: Ready or degraded
    API-->>Operator: Local stack status
```

---

## SD-09: Release validation sequence

```mermaid
sequenceDiagram
    participant Dev as Developer/Release Owner
    participant CI as GitHub Actions / CI
    participant Tests as Test Suites
    participant Gov as Governance Scripts
    participant Backend as PyInstaller Backend
    participant Pkg as Windows Packaging
    participant Integrity as Installer Integrity
    participant Sign as Signing Verification
    participant Checklist as Release Checklist

    Dev->>CI: Push release candidate
    CI->>Tests: Run backend/frontend/security/parity tests
    Tests-->>CI: Results
    CI->>Gov: Run docs/env/lockfile/release checks
    Gov-->>CI: Governance results
    alt Desktop release
        CI->>Backend: Build backend executable bundle
        Backend-->>CI: Backend package evidence
        CI->>Pkg: Build Electron/NSIS installer + run NSIS checks
        Pkg-->>CI: Packaging evidence
        CI->>Integrity: Verify checksum/blockmap/root installer artifacts
        Integrity-->>CI: Integrity report
        CI->>Pkg: Run portable and installer-mode smoke where scoped
        Pkg-->>CI: Smoke reports
    end
    alt Signed production release
        CI->>Sign: Verify trusted signature/artifact evidence
        Sign-->>CI: Signature result
    end
    CI->>Checklist: Attach/verify release evidence
    Checklist-->>Dev: Approve, block, or approve with caveat
```

---

## SD-10: Documentation governance sequence

```mermaid
sequenceDiagram
    participant Author as Doc/Code Author
    participant Docs as Active Docs
    participant Matrix as Coverage Matrix
    participant Version as Versioning Policy
    participant CI as Docs Validation

    Author->>Docs: Update source-of-truth document
    Docs->>Version: Update metadata/version/date
    Docs->>Matrix: Update coverage if doc added/renamed/retired
    Author->>CI: Run documentation validation
    CI->>CI: verify_docs_references and generate_docs
    alt Validation passes
        CI-->>Author: Ready for review
    else Validation fails
        CI-->>Author: Fix links/metadata/references
    end
```

## Change notes for v2.7.0

1. Updated privacy-action auth wording for single-owner/principal verification.
2. Expanded the release validation sequence to include backend bundle build, installer integrity, and installer-mode smoke.
3. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older MFA/SID/Active Defense/Knowledge Engine/QuadPersona sequences with current local-auth, DMRF, Truth Engine, provider, MCP, trace/export, privacy, local data, release, and docs-governance sequences.
3. Aligned sequence terminology with `ARCHITECTURE.md`, `WORKFLOW.md`, `DATA_FLOW_DIAGRAMS.md`, `PROCESS_MAP.md`, and `DECISION_LOGIC.md`.
