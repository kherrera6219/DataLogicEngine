# CP19-L clean rebuild and installed-candidate checkpoint

## Decision

CP19-L passed on 2026-08-10. The source, dependency, security, documentation,
frontend, SDK, packaging, and no-capability-reduction gates authorized a clean
candidate rebuild. The rebuilt unsigned 4.3.0 candidate was installed per-machine
and launched from `C:\Program Files\DataLogicEngine Desktop`.

This is an installed engineering checkpoint, not CP19-M completion and not a
production/public-release authorization. Production remains **NO-GO** until the
exact signed artifact and every retained installed, manual, external, provider,
pilot, and soak gate pass.

## Candidate identity

| Item | Result |
|---|---|
| Installer | `DataLogicEngine Setup 4.3.0.exe` |
| Size | 283,890,413 bytes |
| SHA-256 | `1b7bb3202f1ac320d266f1203e12956c152040c42ba015f405ca33c2425a018e` |
| Installation | Per-machine install completed with exit code 0 |
| Installed executable | `C:\Program Files\DataLogicEngine Desktop\DataLogicEngine Desktop.exe` |
| Runtime result | `/ready` returned HTTP 200 with database `ok`, runtime `ready`, and no blockers; the Electron window opened |
| Trust result | Unsigned candidate; signing/update/distribution policy remains fail-closed |

## Retained app-owned data plane

The application did not create or substitute a new user database. It adopted the
existing 0.1.1 SQLite authority once into the required 4.3.0 PostgreSQL service,
retained an immutable recovery copy and verified adoption receipt, synchronized
PostgreSQL sequences, and reused the retained encryption-key authority.

The app-owned Podman machine `datalogicengine` supervises loopback-only
PostgreSQL, Redis, Neo4j, ChromaDB, and SeaweedFS services. The verified adoption
receipt records:

| Surface | Retained result |
|---|---:|
| Users | 3 |
| Audit logs | 21,992 |
| Provider records | 3 |
| Provider usage records | 52 |
| AI audit events | 16 |
| AI preferences | 1 |
| Notification preferences | 1 |
| Total listed relational rows | 22,068 |
| Neo4j graph | 20 nodes / 18 relationships |
| Object store | 8 objects / 32,596 bytes |

The legacy `ukg-neo4j` Docker container was stopped only after the graph adoption
receipt verified; its volumes were not deleted. Completed adoption remains valid
when the immutable recovery copy matches even if the live legacy SQLite WAL later
changes the source-file digest.

## Validation summary

- full backend: 3,098 passed, 19 skipped;
- frontend: 430 tests plus lint, type checking, production build, and Electron
  TypeScript checks;
- SDKs: 36 Python and 7 TypeScript tests;
- dependency/security: governed locks, `pip-audit`, `npm audit`, Ruff, Bandit,
  public-error contracts, Electron security, and environment/workflow parity;
- release: payload, installer integrity, governance, ownership, runtime precheck,
  schema parity, documentation truth, and legacy-retirement checks;
- installed smoke: readiness, authentication, diagnostics, and representative
  governed KA execution from the frozen backend.
- installed follow-up: health polling no longer exhausts the general API rate
  budget, and dashboard overview/activity/trends use the canonical `started_at`
  model fields; 30 focused regressions pass.
- final rebuilt-install follow-up: the post-launch log window contained no
  actual 429, analytics error, traceback, or fatal event; all five retained
  app-owned services were running and the verified adoption receipt remained
  unchanged.

## Post-candidate source boundary

Linux-safe document-closure hashing, bounded Electron-builder rename retries,
secret-scan false-positive identifier cleanup, Algorithms registry/API/sidebar
remediation, focused regressions, and controlled review-document routing were
completed after the payload above was frozen. Per owner direction, no second
full rebuild was performed at this checkpoint. These source changes are not
claims about the installed hash above and require a new exact-source rebuild
before installed acceptance continues.

## Retained CP19-M and release gates

- exact signed/timestamped publisher artifact and production trust authority;
- protected-volume clean install, repair/upgrade/rollback/uninstall, coordinated
  backup/restore, remnant review, and independent recovery/security/license review;
- installed OpenAI/Google provider and corpus runs, blinded-human acceptance, and
  owner/second-reviewer approvals;
- installed Phase 9 retrieval/Knowledge/Graph, Phase 10 simulation/provider/
  artifact/UI, Phase 11 MCP containment/lifecycle/stores/Electron, Phase 12 real
  workflow/store effects plus packaged visual/scaling/high-contrast and NVDA, and
  Phase 13 correlation/failure-injection/redaction/no-egress/support acceptance;
- 24-hour stress, 72-hour idle/normal-use soak, clean-machine pilot, same-host/
  private gateway, and independent professional acceptance.
