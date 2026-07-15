# Phase 15 release-candidate engineering checkpoint

## Decision

Phase 15 reached its release-candidate **engineering checkpoint** on 2026-07-14.
It did not pass the signed installed-product exit gate. Phase 16 documentation
replacement may proceed while CP15-A through CP15-H remain explicit release
blockers. Production/public distribution remains **NO-GO**.

## Frozen source and build authority

- Candidate source commit: `f2e4174f363f4af26e2af5428abb75ebd51e0b1d`.
- Product: DataLogicEngine 4.3.0; Windows file version 4.3.0.0.
- Exact local build environment: CPython 3.11.14, PyInstaller 6.18.0, Electron
  43.1.1, and the complete 315-package SHA-256 Python release lock.
- Candidate and production workflow modes are separate. Candidate mode creates
  unsigned qualification artifacts. Production mode requires the authorized
  release channel, ownership, legal/distribution, trust, signing, and signature
  gates.
- The packaged release channel is `candidate`, its data-plane profile is
  `qualification`, and `production_authorized` is false.

## Candidate results

The first build is retained as negative baseline evidence, not as a release
candidate. It came from a drifted developer environment and included tests,
caches, application source, and stale compiled Electron tests. Its backend had
10,331 files; its portable tree had 10,416 files and 1,330,613,366 bytes; its
installer was 380,856,055 bytes.

The clean local candidate passed exact-lock installation, `pip check`, version
parity, workflow-pin verification, dependency-lock verification, installer
integrity, and release-payload verification:

| Artifact/check | Result |
|---|---|
| Installer | 299,129,416 bytes |
| Installer SHA-256 | `5a76e0004e17ccee3e0721ec3f9fe0ee109ccc03d74c5ceb19273e99b3ae4620` |
| Frozen backend | 6,151 files; 513,329,279 bytes |
| Portable tree | 6,229 files; 886,614,933 bytes |
| Required packaged runtime assets | Present |
| Forbidden source/test/cache/stale Electron-test findings | 0 |
| Installer checksum/blockmap/integrity | Pass |
| Authenticode/publisher gate | Fail as expected: unsigned qualification artifact |

## Independent clean builds and repeatability

Two independent `windows-latest` GitHub builds completed successfully from the
same frozen commit:

- [Run 29393458241](https://github.com/kherrera6219/DataLogicEngine/actions/runs/29393458241):
  299,350,829 bytes,
  SHA-256 `21bdd3d51c153a30a2c67b03ed4f4c6db3be26f99a0ec3486b91f0f9ed68f2fe`.
- [Run 29393459452](https://github.com/kherrera6219/DataLogicEngine/actions/runs/29393459452):
  299,350,973 bytes,
  SHA-256 `94514b1bcfe7c6e499d1e2d545a20eac15de9faa0a538ff6e86f7c4fc4c6e2a2`.

Both builds passed source authority, exact dependency installation, payload,
integrity, SBOM, manifest, and artifact-upload steps, and each produced the same
file counts: 6,155 backend files and 6,233 portable files. The repeatability
comparison still fails because eight backend files differ byte-for-byte,
including `base_library.zip`, six installed-package `RECORD` files, and the
PyInstaller executable. The portable Electron executable and `app.asar` also
differ, so the outer NSIS installers differ. CP14-B/Phase 15 reproducibility is
therefore retained; equal file counts are not reported as byte reproducibility.

## Packaged runtime probe

The unpacked candidate launched the Electron shell and reached the frozen
backend. The backend then refused readiness at
`at_rest_protection_not_ready`/`startup_failed:paths_and_acl` because the current
workstation could not prove protected-volume readiness. This is a truthful
fail-closed result, not a packaging pass and not a clean-machine lifecycle test.
The current machine also could not run the administrative BitLocker status probe
without elevation. The signed/protected clean-machine matrix remains open.

## Focused validation

- 28 release-focused Python tests passed in the final checkpoint run.
- Ruff passed for the changed Python release files.
- Frontend typecheck and Electron build passed.
- Seven focused Electron tests passed across three files.
- Workflow YAML parsed and all 71 external action references were commit-pinned.
- All 18 product-version checks and dependency-lock authority passed.
- The local canonical backend, portable application, NSIS installer, checksum,
  blockmap, content inventory, and payload report were rebuilt after cleanup.

## Retained release blockers

The complete table is in `deferred-gates.md`. Material blockers include the
approved publisher and signed artifact, reproducible payload bytes, clean
install/repair/upgrade/rollback/uninstall, protected-volume and supported Windows
matrix, real five-service/provider workflows, complete failure/recovery matrix,
24-hour stress and 72-hour idle/normal-use soak, packaged accessibility/manual
NVDA, same-host/private gateway qualification, two-machine human pilot,
independent reviews, legal/distribution authority, object-store Replacement
Control, and open critical Dependabot alert 389 (`CVE-2026-45829`).

SeaweedFS remains candidate-only under Proposed ADR-0004. MinIO remains the
product-specific production architecture until Replacement Control passes and
the owner records final selection.
