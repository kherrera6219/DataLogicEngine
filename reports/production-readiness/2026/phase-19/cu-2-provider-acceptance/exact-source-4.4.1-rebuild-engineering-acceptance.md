# Exact-source 4.4.1 rebuild engineering acceptance

## Decision

The unsigned Windows engineering artifact built from source commit
`ab7b1b181d65d0fc10c1a88706258710b2b34807` passes exact-source integrity,
release-payload, NSIS-governance, and strict package-owned portable-readiness
checks. This closes only the CU-2 4.4.1 rebuild and portable engineering row.
Fresh-installed Google chat, OpenAI quota, production signing, and every
retained CP19-M manual, external, lifecycle, accessibility, recovery, pilot,
and soak gate remain open. Production/public release remains **NO-GO**.

## Artifact binding

| Field | Value |
|---|---|
| Product version | `4.4.1` |
| Windows file version | `4.4.1.0` |
| Source commit | `ab7b1b181d65d0fc10c1a88706258710b2b34807` |
| Artifact | `DataLogicEngine Setup 4.4.1.exe` |
| Size | `358849159` bytes |
| SHA-256 | `a92b836145bb23eccc2f89c33a005a6ec66683fae28e13824cd988ec18b05156` |
| Signature | `NotSigned` |
| Build completed | `2026-08-20` |

## Validation

| Check | Result |
|---|---|
| Focused runtime/DSQP/FROST/governed/gateway/version/migration tests | `89 passed` |
| Full Windows source suite | `3295 passed, 18 skipped, 0 failures, 0 setup errors` |
| Installer integrity | `pass`, 0 errors, 0 warnings |
| NSIS governance | `pass` |
| Release payload | `pass`, 6,096 backend files, 0 issues |
| Strict portable launch | `pass` |
| Package-owned backend readiness | `ready` in 28,447 ms; listener owner verified as a launched-package descendant |
| Shutdown | no retained packaged process or port-5000 listener |
| Installed mode | not run |

Machine-readable evidence is in `reports/installer_integrity_report.json`,
`reports/nsis_governance_report.json`, `reports/release_payload_report.json`,
and `reports/packaging_smoke_report.json`.

## Next artifact-bound action

Install this exact hash and prove an ordinary Google chat advances past Layer 4,
invokes the configured provider exactly once, returns a governed response, and
creates validation telemetry. Do not transfer provider or installed evidence
from an older installer hash.
