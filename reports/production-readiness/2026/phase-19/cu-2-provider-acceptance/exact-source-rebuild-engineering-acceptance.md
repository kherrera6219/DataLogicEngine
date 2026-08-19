# CU-2 exact-source rebuild engineering acceptance

## Decision

**Portable engineering result: PASS. Production/public release: NO-GO.**

The product owner directed the work to proceed through every independently safe
step despite the retained OpenAI quota blocker. This record closes the reviewed
clean-source binding and unsigned portable packaging rows only. It does not
close signing, elevated installed lifecycle, provider corpus/human review,
accessibility, recovery, independent review, pilot, or soak acceptance.

## Exact subject

| Field | Result |
|---|---|
| Product | DataLogicEngine 4.4.0 |
| Source commit | `c765ba03257e58e69a4cd4b80f92390c71346801` |
| Source state before build | Clean; `main` ahead of `origin/main` by the source checkpoint only |
| Artifact | `DataLogicEngine Setup 4.4.0.exe` |
| Size | 358,848,516 bytes |
| SHA-256 | `650034eeec76cbfc582ce81551f40d14e527aeea2707682bdf040d808062a591` |
| Build time | `2026-08-19T03:11:31.8924870Z` |
| Authenticode | `NotSigned`; no signer certificate |
| Release trust policy | `production_authorized=false` |

The installer, block map, and checksum are local build products and remain
outside source control. Evidence and documentation are committed; the binary is
not distributed by this checkpoint.

## Validation

| Gate | Result |
|---|---|
| Version parity and packaged backend build | Pass |
| Next.js production export | Pass; 31 static pages |
| Electron TypeScript build | Pass |
| Electron/NSIS build | Pass |
| Installer integrity | Pass; zero errors and zero warnings; checksum and block map present |
| NSIS governance | Pass |
| Release payload | Pass; 6,096 backend files and zero issues |
| Required packaging resources | Pass; backend executable, release trust/channel policies, and one Rego policy present |
| Strict portable launch | Pass |
| Package-owned backend readiness | Pass in 30,701 ms; listener owner verified as a descendant of the launched package |
| Shutdown cleanup | Pass; zero port-5000 listeners and no packaged backend process remain |
| Elevated installer lifecycle | Not run; no install/uninstall claim |

The build emitted the existing optional-module and static-export warnings. No
required build or validation gate failed.

## Provider and release boundary

Google `gemini-3.7-flash` has two passing bounded source-level availability
receipts. OpenAI `gpt-5.6-sol` reached the live API with the required High
reasoning contract but returned `quota_exhausted` twice. No credential or
response body is stored in those receipts.

The exact-source artifact remains unsigned and has not completed installed
provider, retained-data, service-role, Phase 9-13, accessibility/NVDA,
protected-volume recovery, independent-review, pilot, or 24/72-hour soak
acceptance. No result from an older artifact hash transfers to this one.

## Evidence files

- `reports/installer_integrity_report.json`
- `reports/packaging_resources_report.json`
- `reports/packaging_smoke_report.json`
- `reports/production-readiness/2026/phase-19/cu-2-provider-acceptance/exact-source-rebuild-payload.json`
- `reports/production-readiness/2026/phase-19/cu-2-provider-acceptance/provider-refresh-live-acceptance.json`
- `reports/production-readiness/2026/phase-19/cu-2-provider-acceptance/google-live-retest.json`
- `reports/production-readiness/2026/phase-19/cu-2-provider-acceptance/openai-live-retry.json`

## Next action

Restore OpenAI quota and rerun the bounded High-reasoning availability check.
After both provider rows pass, obtain owner-authorized production signing
material and rebuild/sign/timestamp from the then-current exact commit before
starting elevated CP19-M installed acceptance.
