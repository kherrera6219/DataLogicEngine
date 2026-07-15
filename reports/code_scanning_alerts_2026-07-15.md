# Code Scanning Alert Remediation Report

Snapshot and source remediation date: 2026-07-15

Repository: `kherrera6219/DataLogicEngine`

## Live finding inventory

The live GitHub query returned 57 open CodeQL findings: 51 medium
`py/stack-trace-exposure` findings, four high `py/path-injection` findings, one
high `py/clear-text-storage-sensitive-data` finding, and one high
`py/weak-sensitive-data-hashing` finding.

## Medium finding root cause and correction

All 51 medium findings reached the same public-error helper. The helper treated a
safe phrase inside an exception as authority to return the entire exception.
That allowed unrelated database, provider, file-path, credential, or internal
diagnostic text surrounding the phrase to enter a public response.

`normalize_public_error_message()` now returns only a code-owned canonical
message for an allowed phrase. It never returns the supplied exception text.
Focused regressions prove that a message containing `permission denied` or a
custom provider phrase cannot expose a secret, internal path, or upstream URL.
The pushed CodeQL rerun marked all 51 findings fixed. They were not dismissed.

## High finding review and disposition

| Alert | CodeQL classification | Control evidence | Disposition |
|---|---|---|---|
| #653 | Backup destination path | Electron main consumes a single-use picker capability and signs the owner-selected destination; the coordinator creates a new encrypted, authenticated recovery archive | Dismissed as false positive |
| #654 | Weak sensitive-data hash | The value is a generated 256-bit machine credential; SHA-256 is its nonreversible lookup index, not a human-password KDF; human passwords use the separate password-hashing implementation | Dismissed as false positive |
| #655 | Ingestion source path | Electron main consumes a single-use picker capability and signs the request; non-desktop mode canonicalizes and confines the source under `DATALOGIC_INGESTION_ROOT` | Dismissed as false positive |
| #656 | MCP allowed-root path | Admin-only registration requires absolute existing directories, canonicalizes them, fingerprints the definition, and keeps execution disabled until explicit scope consent | Dismissed as false positive |
| #658 | Support-bundle JSON storage | `write_json()` recursively applies `redact_value()` before serialization; a regression proves nested token material is absent from stored JSON | Dismissed as false positive |
| #659 | MCP executable path | Admin-only registration requires an absolute existing file, denies shells and package runners, fingerprints the definition, and requires consent plus process containment | Dismissed as false positive |

Alert #657 was already fixed in the live GitHub state; #659 was the active
instance at the same MCP executable sink. Each dismissal includes the relevant
control evidence in GitHub. The live open-high query returns zero findings.

## Adjacent deployment correction

The replacement Deploy and CI runs exposed separate frontend-image failures
after their original jobs passed. `next.config.ts` reads the repository-wide
product version authority during the frontend build, but neither image stage
received that file. `Dockerfile.cloud` now copies the authority into its
root-context build. The standalone `frontend/Dockerfile`, CI job, and Compose
definition now use repository context and copy the same authority before
`npm run build`. Regressions lock both copy orders and both context contracts.

## Validation

- Focused error-normalization, support-bundle, and Dockerfile regressions: 11 passed.
- Focused MCP policy and route regressions: 35 passed.
- Repository-wide Ruff: passed.
- Public-error contract scan: 425 Python files, zero findings.
- Secret-storage verifier and Bandit high-confidence delta gate: passed.
- Dependency-lock, workflow-pin, frontend lint, and frontend typecheck gates: passed.
- Documentation authority: 30/30 canonical; product 5/5, assurance 12/12, external review 3/3, and 8 focused tests passed.
- Cloud and standalone frontend-builder Docker targets: passed, including Next.js production builds and TypeScript validation.
- Docker Compose rendering: passed; unset local credential warnings are expected without an operator environment file.
- Full isolated backend suite: 2,181 passed and 18 skipped.
- Replacement GitHub workflows: passed.

## Remote confirmation

Commit `6c1f2e8f` passed every required replacement workflow:

| Workflow | Run | Result |
|---|---|---|
| Security Scan | [29401695782](https://github.com/kherrera6219/DataLogicEngine/actions/runs/29401695782) | Passed, including dependency, Bandit, secret, SBOM, Cosign, and Python/JavaScript CodeQL jobs |
| CI/CD Pipeline | [29401695732](https://github.com/kherrera6219/DataLogicEngine/actions/runs/29401695732) | Passed, including backend, governance, frontend, Windows packaging/portable smoke, and backend/frontend Docker images |
| Deploy | [29401695777](https://github.com/kherrera6219/DataLogicEngine/actions/runs/29401695777) | Passed, including build/test and the combined cloud Docker image |

The live GitHub code-scanning query returns zero open findings. Dependabot alert
389 remains open and critical as the separately retained ChromaDB blocker.

Dependabot alert 389 for the no-fixed-release ChromaDB advisory is separate and
remains a production/public-release blocker.
