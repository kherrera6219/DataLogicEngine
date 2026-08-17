# Provider-refresh replacement rebuild acceptance

## Verdict

The local replacement engineering artifact passes static package validation and
portable package-owned readiness against the retained data plane. It is not a
production or public-release candidate: it is unsigned, built from an
uncommitted local working tree based on commit `b3132966`, and has not passed
the elevated installed lifecycle or owner-authorized live-provider tests.

## Exact artifact

| Field | Result |
|---|---|
| Artifact | `DataLogicEngine Setup 4.4.0.exe` |
| Size | 358,859,589 bytes |
| SHA-256 | `5ec7af72638bde793dbb60fb48745055d0b61c2f11e334dde0a8df5060415bab` |
| Source binding | local uncommitted tree based on `b3132966fd9c9f3d92a21036e06e636c1e96c97c` |
| Authenticode | `NotSigned` |
| Checksum / block map | pass / present |
| Production/public release | **NO-GO** |

## Validation

- Version parity and schema parity pass for product `4.4.0` and Alembic head
  `b2c3d4e5f6a7`.
- NSIS governance, packaged-resource, installer-integrity, and release-payload
  checks pass. The backend payload contains 6,096 files and zero verifier
  issues.
- The exact portable payload reached package-owned `/ready` in 52,549 ms. The
  listener belonged to the launched package process tree.
- The first diagnostic rebuild correctly failed closed because the migration
  gate had not explicitly authorized the new PostgreSQL revision. The gate was
  corrected to distinguish explicitly enumerated transactional/lossless paths
  from destructive paths, which continue to require a verified backup.
- The retained PostgreSQL store advanced from `0a1b2c3d4e5f` to
  `b2c3d4e5f6a7`; every managed store reported ready. Read-only verification
  showed saved provider rows at Google `gemini-3.7-flash` and OpenAI
  `gpt-5.6-sol`. No provider key was read or printed.
- The smoke-created service containers were stopped after verification; no app
  process or owned listener was intentionally left running.

## Coverage truth

There is no supported 80% whole-application coverage claim. The fresh split
measurement is:

| Surface | Result |
|---|---:|
| Python `backend/` + `core/` | 67.01% (41,231 / 61,530) |
| Python `backend/` only | 76.78% (35,712 / 46,511) |
| Python `backend/security/` | 79.26% (1,624 / 2,049) |
| Frontend statements | 76.29% (2,108 / 2,763) |
| Frontend lines | 78.53% (2,009 / 2,558) |
| Frontend functions | 71.37% |
| Frontend branches | 65.71% |

The measurement runs passed 3,115 backend tests with 18 skipped and 435
frontend tests. Python and V8 coverage are not blended, and neither suite
currently enforces a hard coverage `fail-under`.

## Evidence

- `backend-coverage.json`
- `frontend-coverage/coverage-summary.json`
- `installer-integrity.json`
- `release-payload-verification.json`
- `release-content-inventory.json`
- `packaging-smoke-report.json`
- `provider-refresh-rebuild-acceptance.json`

## Open acceptance boundary

Next, run the bounded owner-authorized Google and OpenAI connectivity tests on
this replacement source, then bind a clean committed and signed artifact before
elevated per-machine install/upgrade/repair/uninstall, retained-data,
accessibility, recovery, independent-review, pilot, and soak acceptance.
