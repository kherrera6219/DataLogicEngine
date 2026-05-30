# Local-First Security Model Map

## Purpose

This diagram maps DataLogicEngine's local-first Windows security model to the actual code paths that implement desktop identity, loopback authentication, DPAPI protection, encryption/key rotation, export integrity, frontend runtime policy, and desktop session behavior.

The goal is to show that local-first security is not only a written standard. The repository contains concrete implementation modules for desktop auth, DPAPI, encryption, signed requests, runtime policy, export authenticity, and frontend auto-login behavior.

## Primary Code Paths

- `backend/security/desktop_local_auth.py`
- `backend/security/dpapi_store.py`
- `backend/security/encryption_manager.py`
- `backend/security/export_integrity.py`
- `backend/security/integrity.py`
- `frontend/contexts/AuthContext.tsx`
- `frontend/lib/runtime/policy.ts`
- `frontend/components/AppInitializer.tsx`
- `frontend/electron/main.ts`
- `frontend/electron/preload.ts`
- `app.py`

## Mermaid Architecture Diagram

```mermaid
flowchart TD
    User[Windows User]
    WindowsLogin[Windows Login Session]
    Electron[Electron Desktop Runtime]
    Frontend[Next.js Frontend]
    AuthContext[AuthContext\nDesktop Auto-Login Decision]
    RuntimePolicy[Runtime Policy\nlocal / hybrid / cloud\nLoopback + Electron Detection]
    AppInit[AppInitializer\nLoading + Workspace Bootstrap]

    User --> WindowsLogin
    WindowsLogin --> Electron
    Electron --> Frontend
    Frontend --> RuntimePolicy
    Frontend --> AuthContext
    AuthContext --> AppInit

    subgraph LOOPBACK[Desktop Loopback Authentication]
        Challenge[Issue One-Time Challenge Nonce]
        InstallSecret[Per-Install Secret\nDESKTOP_INSTALL_SECRET or local secret file]
        NonceTTL[Nonce TTL\n30-300 seconds]
        HMACChallenge[HMAC-SHA256 Challenge Signature]
        RequestSig[Per-Request HMAC Signature\nmethod + path + timestamp]
        SkewCheck[Timestamp Skew Check]
        Compare[Constant-Time Signature Compare]
    end

    AuthContext --> Challenge
    Challenge --> NonceTTL
    Challenge --> InstallSecret
    InstallSecret --> HMACChallenge
    InstallSecret --> RequestSig
    RequestSig --> SkewCheck
    SkewCheck --> Compare
    Compare --> BackendAuth[Backend Desktop Auth Accepted]

    subgraph DPAPI[Windows DPAPI Protection]
        DPAPIStore[backend/security/dpapi_store.py]
        Entropy[App Entropy\nUKG_DPAPI_ENTROPY or default pepper]
        Protect[CryptProtectData\nCurrent Windows Context]
        Unprotect[CryptUnprotectData\nCurrent Windows Context]
        Base64[Base64 Envelope]
    end

    WindowsLogin --> DPAPIStore
    DPAPIStore --> Entropy
    Entropy --> Protect
    Entropy --> Unprotect
    Protect --> Base64
    Base64 --> Unprotect

    subgraph ENC[Application Encryption Manager]
        EncMgr[EncryptionManager]
        KEK[Key Encryption Key\nPBKDF2-HMAC-SHA256\n600000 iterations]
        Salt[Per-Install Salt\nkek.salt]
        DEK[Data Encryption Keys\nVersioned Registry]
        Rotation[Automatic DEK Rotation\n90-day default]
        FieldEnc[Field-Level Encryption]
        AuditEnc[Encryption Audit Events\ndata_encrypted / data_decrypted / rotation]
    end

    DPAPIStore --> EncMgr
    EncMgr --> KEK
    Salt --> KEK
    KEK --> DEK
    DEK --> Rotation
    DEK --> FieldEnc
    EncMgr --> AuditEnc

    subgraph EXPORT[Trace Export Authenticity]
        Bundle[Trace / Audit Export Bundle]
        SectionHashes[Per-Section SHA-256 Hashes]
        BundleHash[Bundle SHA-256 Hash]
        HMACExport[Optional HMAC-SHA256 Signature]
        FernetExport[Optional Fernet Payload Encryption]
        Manifest[Export Manifest\nversion + hashes + signature + encryption flags]
    end

    BackendAuth --> Bundle
    Bundle --> SectionHashes
    Bundle --> BundleHash
    BundleHash --> Manifest
    HMACExport --> Manifest
    FernetExport --> Manifest

    subgraph APISEC[Backend Security Envelope]
        App[app.py]
        SessionHardening[Session Cookie Hardening\nHttpOnly + SameSite + Secure]
        TrustedHosts[Trusted Host Validation]
        HTTPS[HTTPS Redirect Outside Desktop Mode]
        CORS[CORS Allowlist]
        CSRF[CSRF Origin / Token Checks]
        RateLimit[Rate Limiting]
        Middleware[Security Middleware\nInput Sanitization + Request Limits + Timeouts]
    end

    BackendAuth --> App
    App --> SessionHardening
    App --> TrustedHosts
    App --> HTTPS
    App --> CORS
    App --> CSRF
    App --> RateLimit
    App --> Middleware

    Middleware --> ProtectedWorkspace[Protected Local Workspace / API Session]
    FieldEnc --> ProtectedWorkspace
    Manifest --> ProtectedWorkspace
```

## Desktop Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    participant User as Windows User
    participant FE as Electron / Frontend
    participant Policy as Runtime Policy
    participant API as Flask Backend
    participant Auth as desktop_local_auth.py
    participant Secret as Install Secret

    User->>FE: Launch DataLogicEngine desktop app
    FE->>Policy: shouldUseDesktopSessionFlow()
    Policy-->>FE: true when Electron/local/hybrid runtime permits desktop auth
    FE->>API: Request desktop auth challenge
    API->>Auth: issue_desktop_auth_challenge(session)
    Auth-->>API: nonce + ttl
    API-->>FE: challenge nonce
    FE->>Secret: Use per-install secret
    FE->>Auth: Build HMAC signature for nonce
    FE->>API: Submit nonce + signature
    API->>Auth: verify_desktop_auth_challenge()
    Auth->>Auth: consume nonce regardless of success/failure
    Auth->>Auth: check expiry + nonce match + HMAC compare_digest
    Auth-->>API: accepted or rejected
    API-->>FE: desktop session / auto-login result
```

## Local-First Security Responsibilities

| Responsibility | Implementation | Notes |
|---|---|---|
| Runtime mode selection | `frontend/lib/runtime/policy.ts` | Determines `local`, `hybrid`, or `cloud`; cloud disables desktop auth. |
| Electron/desktop detection | `frontend/lib/runtime/policy.ts` | Uses `window.electronAPI` or Electron user agent. |
| Desktop auto-login path | `frontend/contexts/AuthContext.tsx` | Calls `desktopAutoLogin()` when desktop session flow is allowed and no user is already authenticated. |
| Startup loading/bootstrapping | `frontend/components/AppInitializer.tsx` | Provides controlled loading state while auth/session initialization runs. |
| Per-install secret | `backend/security/desktop_local_auth.py` | Reads env secret or creates `instance/desktop_install_secret.txt`; attempts `0600` permissions. |
| One-time challenge | `backend/security/desktop_local_auth.py` | Stores nonce and expiry in session; invalidates nonce regardless of outcome to reduce replay risk. |
| Per-request desktop signing | `backend/security/desktop_local_auth.py` | HMAC over method, path/query, and timestamp; validates skew and signature. |
| DPAPI storage | `backend/security/dpapi_store.py` | Uses Windows `win32crypt.CryptProtectData` / `CryptUnprotectData` with app entropy. |
| Key hierarchy | `backend/security/encryption_manager.py` | KEK/DEK pattern, PBKDF2-HMAC-SHA256, versioned DEK registry. |
| Key rotation | `backend/security/encryption_manager.py` | 90-day default rotation; archived old keys retained for decryption. |
| Field-level encryption | `backend/security/encryption_manager.py` | `FieldEncryption` helper encrypts/decrypts selected model fields. |
| Export authenticity | `backend/security/export_integrity.py` | Builds manifest with bundle hash, section hashes, optional HMAC signature, optional Fernet encryption. |
| Backend envelope | `app.py` | Session hardening, trusted hosts, HTTPS redirect, CORS allowlist, CSRF checks, rate limits, middleware. |

## DPAPI Model

The DPAPI helper is Windows-specific and intentionally tied to the local Windows context:

```text
plaintext
  ↓
CryptProtectData + app entropy
  ↓
base64 encoded protected payload
  ↓
CryptUnprotectData + same Windows context + same app entropy
  ↓
plaintext
```

This supports the local-first design principle that the Windows user account is the application identity boundary.

## Encryption Manager Model

The encryption manager uses a hierarchical model:

```text
ENCRYPTION_KEK_SECRET + salt
        ↓ PBKDF2-HMAC-SHA256, 600000 iterations
KEK
        ↓ encrypts
Versioned DEKs
        ↓ encrypt data fields
Encrypted payloads with v{version}: prefix
```

Important behavior:

- A salt file is created under the configured key directory.
- DEKs are stored encrypted by the KEK.
- Each encrypted value includes a key version prefix.
- Rotation archives old DEKs while preserving decryption support.
- Encrypt/decrypt operations can emit audit events when an audit logger is supplied.

## Export Integrity Model

Trace exports are protected as envelopes:

```text
Trace bundle
  ↓
section hashes + bundle hash
  ↓
manifest
  ↓
optional HMAC-SHA256 signature
  ↓
optional Fernet-encrypted payload
  ↓
export document
```

This supports judge/auditor review because exported trace bundles can carry integrity metadata instead of being raw JSON dumps.

## Security Boundary Notes

### Local/desktop mode

- Desktop auth is allowed only when runtime policy permits it.
- Loopback and Electron runtime checks are part of the frontend policy.
- Backend desktop auth relies on nonce challenge and HMAC signatures.
- DPAPI protection is bound to the local Windows environment.

### Cloud mode

- Desktop auth is denied by runtime policy when mode is `cloud`.
- Backend controls such as trusted hosts, HTTPS redirect, CORS allowlist, CSRF checks, sessions, and rate limits remain relevant.

### Hybrid mode

- Hybrid can permit desktop auth while still using selected external services.
- This should be reviewed carefully during deployment because hybrid mode crosses local and external trust boundaries.

## Judge Review Path

A technical judge should inspect these files in order:

1. `frontend/lib/runtime/policy.ts` — verifies runtime mode, loopback host detection, Electron detection, and desktop request authorization rules.
2. `frontend/contexts/AuthContext.tsx` — verifies desktop auto-login behavior and web/desktop route handling.
3. `backend/security/desktop_local_auth.py` — verifies install secret, nonce challenge, HMAC challenge signatures, per-request signatures, timestamp skew checks, and nonce invalidation.
4. `backend/security/dpapi_store.py` — verifies Windows DPAPI usage and app entropy.
5. `backend/security/encryption_manager.py` — verifies KEK/DEK hierarchy, PBKDF2, versioned encrypted payloads, rotation, and field-level encryption.
6. `backend/security/export_integrity.py` — verifies trace export hashing, manifest construction, optional HMAC signing, and optional encryption.
7. `app.py` — verifies backend session, CORS, CSRF, trusted host, HTTPS, rate limiting, and middleware envelope.
8. `frontend/electron/main.ts` and `frontend/electron/preload.ts` — verifies desktop runtime and IPC exposure boundaries.

## Implementation Caveat

The local-first security standard references AES-256-GCM as the target data-encryption standard. The current `EncryptionManager` implementation uses Fernet and records the algorithm as `Fernet-AES-128-CBC`; DPAPI uses Windows platform crypto through `win32crypt`. This diagram maps the implementation as it exists in code. If the target is strict AES-256-GCM everywhere, the code should either be upgraded or the standard should explicitly distinguish current implementation from target future state.

## Interpretation

The local-first security model is one of DataLogicEngine's strongest differentiators. Most AI applications assume cloud identity, cloud storage, and cloud key management. DataLogicEngine includes a path for a local Windows user to run the application with desktop session flow, per-install secrets, signed loopback requests, DPAPI-protected local secrets, encrypted application data, and integrity-protected exports.

This gives the platform a credible local-first enterprise security story while still allowing web/cloud/hybrid deployments when configured.
