# Phase 14 engineering checkpoint

Date: 2026-07-14 (America/Los_Angeles)

Result: **engineering checkpoint complete; production/public release remains NO-GO**.

Phase 14 now has one product-version authority, one Python dependency authority,
versioned Windows artifacts, immutable workflow inputs, fail-closed release trust,
complete source-side SBOM/manifest machinery, and explicit legacy/legal gates.
The final trusted installer, installed lifecycle, publisher identity, signed
updates, legal authority, two-build reproducibility proof, and final
service/installer evidence can only close against the rebuilt release candidate.

## Implemented

1. config/product-versions.json is the authority for product 4.3.0,
   Windows file version 4.3.0.0, public API v1, governed/gateway contracts,
   schema, SDKs, provider manifest, and the supported 0.1.1 upgrade source.
   Python, Electron, UI, support, migration, packaging, and release consumers
   fail when they drift.
2. requirements.txt is the reviewed direct-pin input and
   requirements.lock is the generated 315-package SHA-256 release lock.
   pyproject.toml delegates runtime dependency authority and the contradictory
   partial uv.lock was removed. The Node lock is exact and Electron is locked
   to 43.1.1.
3. Backend builds generate Windows version resources. Electron emits only
   DataLogicEngine Setup 4.3.0.exe; the stale Latest alias is rejected.
   Release jobs require clean/tag/version parity, current backend-before-frontend
   order, integrity/SBOM/content inventory/manifest generation, signing,
   signature verification, attestations, and attestation verification.
4. All external GitHub Actions references are pinned to reviewed 40-character
   commits. Vulnerability, SBOM, signing, and attestation failures no longer
   soft-pass.
5. Backend, frontend, internal-service, and final-installer CycloneDX evidence
   generators are present. The release manifest binds source, runtime,
   dependencies, service assets, artifacts, hashes, signatures, and blockers.
6. config/release-trust-policy.json keeps production signing, distribution,
   and updates disabled until their approval and qualification gates pass.
   Electron always verifies update code signatures; runtime configuration cannot
   bypass the signed-update qualification policy.
7. Windows signature verification covers the canonical installer plus executable
   and scripted payloads, approved publisher subjects, timestamps, hashes, and
   optional revocation. The scripts run under Windows PowerShell 5.1 as well as
   modern PowerShell.
8. Legacy WiX/standalone installer scripts are source-quarantined and excluded
   from all Electron/NSIS release payloads. The filesystem object store remains
   bootstrap/development/repair-only. SeaweedFS remains candidate-only and cannot
   enter a production release.
9. Distribution/legal structure is machine-checked and release-blocking. Ten
   Phase 0 authority/legal decisions and the approved third-party notice bundle
   remain open rather than being implied complete.

## Checkpoint disposition

| Checkpoint | Engineering result | Retained release evidence |
|---|---|---|
| CP14-A Version unity | **Source pass**: 18 consumers report the 4.3.0 authority | Rebuilt installer/binaries and installed About/support output |
| CP14-B Clean deterministic build | **Source controls pass**: clean/tag/lock/stale-output/content-manifest gates implemented | Two clean same-input builds and normalized inventory comparison |
| CP14-C Installer lifecycle | **Open** | Clean install, repair, 0.1.1 upgrade, rollback, keep/export-delete/delete uninstall, path/user/elevation matrix |
| CP14-D Signature trust | **Verifier pass; trust open** | Approved publisher/signing boundary and valid timestamp/revocation evidence for every release executable |
| CP14-E Supply chain | **Source pipeline pass** | Final installer/service/JRE SBOMs, verified attestations, AV/license results, alert 389 disposition |
| CP14-F Update trust | **Fail-closed source pass** | Tamper, unsigned, wrong-publisher, replay, downgrade, interrupted rollback, staged and offline update qualification |
| CP14-G Distribution authority | **Open and release-blocking** | Ten legal/authority actions, approved notices, publisher succession, regions and artifact/channel decision |
| CP14-H Legacy retirement | **Installer-source pass; broader reachability partial** | Full feature-disposition and signed-runtime import/route/config/bundle coverage |

Phase 14 therefore reaches an engineering checkpoint, not its production exit
gate. Phase 15 owns the complete installed release-candidate qualification while
these retained rows remain release-blocking.

## Validation

| Check | Result |
|---|---|
| Phase 14 Python unit/regression tests | 27 passed |
| Ruff over changed Python source/tests | Passed |
| Product-version parity | 18/18 passed |
| Python/Node lock governance | 315 hashed Python packages; exact Node lock; passed |
| Workflow pin governance | 71 references; zero errors |
| Legacy retirement governance | Passed |
| NSIS governance | Passed under Windows PowerShell 5.1 |
| Phase 14 signing scripts | Parsed under Windows PowerShell 5.1 |
| Binary signature inventory | 158 files inventoried; expected fail until rebuilt/signed |
| Release trust policy | Engineering structure passed; signing/update/distribution blocked |
| Distribution authority structure | Passed; release-ready false with 10 open actions |
| Release manifest | Engineering-only; 11 truthful blockers including the fallback Python runtime mismatch |
| Frontend unit tests | 86 files / 422 tests passed |
| Frontend lint | Passed with one existing unused-test-parameter warning |
| Frontend typecheck, Electron TypeScript build, and Next production build | Passed |
| npm audit | Zero vulnerabilities |
| Documentation references | 0 errors; 41 historical style warnings |

The project virtual-environment launcher later hit Windows Store
CreateProcessAsUserW 1312. The focused Phase 14 suite was rerun with the
bundled Python executable and the project's installed pure-Python test packages;
27 tests passed. Earlier Phase 14 runs in the project environment passed before
the launcher fault.

## Evidence

- product-version-parity.json
- dependency-lock-verification.json
- workflow-pins.json
- release-manifest.json
- release-trust-policy.json
- binary-signature-inventory.json
- sbom-services.cdx.json
- distribution-authority.json
- legacy-retirement.json
- installer-stale-artifact-gate.json
- backend-version-info.txt
- deferred-gates.md
- third-party-notices-readiness.md
