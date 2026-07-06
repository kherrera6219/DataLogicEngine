# CIS Benchmarks: Security Coverage

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.0 |
| Last updated | 2026-07-06 |
| Status | Active / Evidence-Guided Mapping |
| Owner | Security Engineering + Platform Operations |
| Review cadence | Every 60 days |

## Purpose

Map DataLogicEngine security-hardening practices to CIS-style benchmark areas without overstating certification or benchmark conformance.

This document is not a CIS certification or attestation. It is a practical hardening coverage map for the current architecture: local-first Windows desktop, Windows VM, controlled web/cloud deployment, Flask API, Electron frontend, local data services, CI/release governance, and operational validation.

## Deployment scope

| Deployment mode | CIS relevance |
|---|---|
| Local-first Windows desktop | Windows workstation hardening, filesystem permissions, local secrets, installer/signature controls, endpoint security. |
| Windows VM | Windows Server/VM hardening, local app-owned services, restricted network exposure. |
| Web/cloud deployment | Linux/container/reverse-proxy/Kubernetes/cloud benchmarks where applicable. |
| Developer workstation | Baseline hygiene only; not production evidence. |

---

## CIS-style control coverage

### 1. Operating system hardening

| Area | DataLogicEngine guidance | Evidence / source |
|---|---|---|
| Least privilege | Run app and services without unnecessary administrator rights where possible. | `docs/WINDOWS_11_LOCAL_RUNBOOK.md`, deployment docs |
| Filesystem permissions | Restrict local logs, install secrets, data directories, and ProgramData paths. | desktop runtime, installer scripts, Windows runbook |
| Patch management | Keep Windows, Python, Node.js, npm, and browser/Electron runtime current. | release checklist, engineer onboarding |
| Local secrets | Use DPAPI helper where available and avoid plaintext secret logging. | `backend/security/dpapi_store.py`, `docs/SECURITY.md` |
| Endpoint protection | Treat antivirus/file locks as operational factors for local stores. | Windows runbook troubleshooting |

### 2. Web/API hardening

| Area | DataLogicEngine guidance | Evidence / source |
|---|---|---|
| HTTPS/TLS | Required for web/cloud production, not required for loopback-only desktop traffic. | `docs/SSL_CONFIGURATION.md` |
| Secure cookies | Required for production web/cloud sessions. | `app.py`, `docs/API.md`, `docs/SECURITY.md` |
| CSRF/CORS/trusted hosts | Enforced/configured for web/cloud contexts. | `app.py`, security docs |
| Rate/resource limits | Request limits and rate-limit controls are part of security envelope. | `app.py`, `tests/security/` |
| Security headers | Security header behavior covered by tests and app configuration. | `tests/security/`, `docs/SECURITY.md` |

### 3. Local data-service hardening

| Area | DataLogicEngine guidance | Evidence / source |
|---|---|---|
| PostgreSQL/SQLite | Use app-owned/local paths; schema parity validation; no unsafe auto-create in production. | `docs/DATABASE_SCHEMA.md`, `scripts/validate_schema_parity.py` |
| Redis | Restrict to local/trusted network contexts; do not expose publicly. | deployment/runbook guidance |
| Neo4j | Restrict local/VM exposure and validate service state. | Windows runbook, data docs |
| ChromaDB | Local persistent path; validate directory permissions. | `backend/storage/vector_store.py` |
| Object store | Reject traversal/unsafe paths and protect exported artifacts. | `backend/storage/object_store.py`, `backend/security/export_integrity.py` |

### 4. Container/Kubernetes hardening

Kubernetes/container CIS controls are relevant only when DataLogicEngine is deployed to containerized or orchestrated production environments.

| Area | Status |
|---|---|
| Kubernetes CIS benchmark | Target-state / deployment-specific, not default local-first evidence. |
| Pod security and admission controls | Claim only when deployment manifests and cluster evidence prove them. |
| Container image provenance/signing | Track through release/supply-chain roadmap. |
| Runtime policy enforcement | Deployment-specific. |

Do not claim Kubernetes CIS conformance for local-first desktop or Windows VM deployments unless a Kubernetes deployment is actually in scope and evidence exists.

### 5. Supply-chain hardening

| Area | DataLogicEngine guidance | Evidence / source |
|---|---|---|
| CI gates | Backend, frontend, governance, contract/parity/security, packaging checks. | `.github/workflows/ci.yml`, `docs/TESTING.md` |
| Lockfile governance | Lockfile verification before release. | `scripts/verify_lockfiles.py` |
| Environment parity | Validate expected environment and dependency state. | `scripts/verify_environment_parity.py` |
| Installer integrity | Verify installer artifacts and signature where applicable. | `scripts/verify_installer_integrity.py`, `scripts/windows/verify_installer_signature.ps1` |
| SLSA roadmap | Current-state/target-state supply-chain map. | `docs/SLSA_LEVEL_3_ATTESTATION.md` |

---

## Verification commands

```powershell
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/validate_schema_parity.py
python scripts/verify_release_governance.py
python scripts/verify_docs_references.py
```

For Windows desktop release candidates:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

---

## Claims that require evidence

Do not claim the following without deployment evidence:

1. CIS Kubernetes Benchmark conformance;
2. CIS Linux Benchmark conformance;
3. CIS Windows Benchmark conformance;
4. Pod Security Admission enforcement;
5. Kubernetes admission-controller policy enforcement;
6. Redis TLS/ACL hardening in every deployment;
7. weekly automated CIS scanner coverage;
8. scanner integrations that are not present in current workflow evidence.

## Change notes for v2.7.0

1. Added installer integrity and installer-mode install/uninstall smoke commands to the Windows desktop release-candidate verification path.
2. Kept CIS language evidence-guided and non-attestation.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed the document from benchmark conformance claims to an evidence-guided hardening map.
3. Distinguished local-first Windows, Windows VM, web/cloud, and Kubernetes/container scopes.
4. Added validation commands and explicit claim caveats.
5. Removed unsupported weekly scanner and blanket Kubernetes/Linux conformance claims.
