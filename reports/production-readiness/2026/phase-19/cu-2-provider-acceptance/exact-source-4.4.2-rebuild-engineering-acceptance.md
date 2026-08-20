# Exact-source 4.4.2 rebuild engineering acceptance

## Decision

The unsigned Windows engineering artifact built from source commit
`103f52e5f9b51f937ac2da8adc17523ec98affdb` passes exact-source integrity,
release-payload, NSIS-governance, and strict package-owned portable-readiness
checks. This closes only the CU-2 4.4.2 rebuild and portable engineering row.
Fresh-installed Google chat, OpenAI quota, production signing, and every
retained CP19-M manual, external, lifecycle, accessibility, recovery, pilot,
and soak gate remain open. Production/public release remains **NO-GO**.

## Artifact binding

| Field | Value |
|---|---|
| Product version | `4.4.2` |
| Windows file version | `4.4.2.0` |
| Source commit | `103f52e5f9b51f937ac2da8adc17523ec98affdb` |
| Artifact | `DataLogicEngine Setup 4.4.2.exe` |
| Size | `358849388` bytes |
| SHA-256 | `ece59ad3e1e36afabd9856b29839254c626638cbcb2d4f00d7efe51c24031f8a` |
| Signature | `NotSigned` |
| Build completed | `2026-08-20` |

## Validation

| Check | Result |
|---|---|
| Focused runtime/KA/governed/version/migration tests | `49 passed` |
| Full Windows source suite | `3297 passed, 18 skipped, 0 failures, 0 setup errors` |
| Frontend lint and type checking | `pass` |
| Product/version parity | `pass`, all 18 checks |
| Installer integrity | `pass`, 0 errors, 0 warnings |
| NSIS governance | `pass` |
| Release payload | `pass`, 6,096 backend files, 0 issues |
| Strict portable launch | `pass` |
| Package-owned backend readiness | `ready` in 38,848 ms; listener owner verified as a launched-package descendant |
| Shutdown | no retained packaged process or port-5000 listener |
| Installed mode | not run |

Machine-readable evidence is in `reports/installer_integrity_report.json`,
`reports/nsis_governance_report.json`, `reports/release_payload_report.json`,
`reports/packaging_smoke_report.json`, and
`reports/production-readiness/2026/phase-14/product-version-parity.json`.

## Next artifact-bound action

Install this exact hash and prove an ordinary Google chat invokes the configured
provider exactly once, releases through Layer 10, returns the governed response,
and exposes the persisted validation telemetry. Do not transfer provider or
installed evidence from an older installer hash.
