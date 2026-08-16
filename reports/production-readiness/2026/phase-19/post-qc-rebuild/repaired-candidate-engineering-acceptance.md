# Post-QC repaired candidate engineering acceptance

## Verdict

The repaired 4.4.0 package passes the automatable, non-elevated post-QC
engineering checks performed on this workstation. The exact package starts its
owned backend, reaches `/ready`, preserves the retained installation identity,
advances that identity from 4.3.0 to 4.4.0 only after managed migrations pass,
and renders the tested desktop workflows.

This is **not** CP19-M closure or production/public release approval. The
artifact is unsigned, the elevated per-machine lifecycle is not conclusively
accepted, and the retained manual, provider, accessibility, independent-review,
pilot, and soak gates remain open. Release posture remains **NO-GO**.

## Exact candidate identity

| Item | Result |
|---|---|
| Build source commit | `e893d42436c8f250de7a2781dc7f621ae4ddab1f` |
| Runtime compatibility fix | `16faaeb4` |
| Readiness-smoke hardening | `56bc4aa7` |
| Product version | `4.4.0` |
| Installer | `DataLogicEngine Setup 4.4.0.exe` |
| Size | 358,857,127 bytes |
| Build timestamp (UTC) | `2026-08-16T05:52:02.9721321Z` |
| SHA-256 | `54dfb496bc2c45a5d02656bdf3d9a02a571868889dc7a76b59ce4fc1ed44fc97` |
| Signature | `NotSigned` |

Installer integrity, checksum, block map, NSIS governance, and packaged-resource
verification pass. The packaging resource report confirms the frozen backend,
release trust policy, release channel, and shipped Rego resource are present.

## Defect found and corrected during acceptance

The first post-QC artifact, built from `2d166456`, remained alive in Electron
but never opened `/ready`. The frozen backend failed closed with
`installation_version_mismatch` because the retained 4.3.0 engineering identity
was not an allowed source for the 4.4.0 migration path. The artifact and failure
are recorded in `first-rebuild-runtime-blocker.md` and must not be used.

Commit `16faaeb4` added 4.3.0 to the authoritative upgrade sources and added a
regression proving version advancement occurs only after the managed migration
gate succeeds. The focused product-version, runtime-lifecycle, and migration
set passed 34 tests. The rebuilt artifact above then passed the same retained
identity transition: the installation identifier remained unchanged and its
version advanced from 4.3.0 to 4.4.0.

The existing portable smoke was also found to be process-only: it could pass
while the backend repeatedly crashed. Commit `56bc4aa7` adds an explicit
`-RequireBackendReady` mode, rejects a pre-existing listener, polls `/ready`,
and verifies that the listening backend is a descendant of the exact launched
package process. The focused Phase 7 tooling tests pass.

## Runtime and desktop evidence

| Check | Result |
|---|---|
| Readiness-required portable smoke | **Pass** |
| Package-owned `/ready` latency | 46,402 ms |
| Readiness response | HTTP 200; `status=ready`; zero blockers |
| Health response | HTTP 200; `service=datalogicengine`; `status=ok` |
| Process ownership | Port 5000 listener verified as a launched-package descendant |
| Shutdown hygiene | Zero packaged processes and zero port-5000 listeners after test |
| Repaired-launch crash markers | Zero version mismatches, tracebacks, fatals, or HTTP 429/rate-limit events |

The packaged desktop was also inspected directly using the Windows application,
not a browser substitute:

- Dashboard rendered and reported the application API available.
- Trace Explorer rendered its execution table and empty-state correctly.
- Diagnostics refreshed successfully, reported runtime phase `ready`, external
  telemetry disabled, user content excluded from support bundles, and Chroma,
  MinIO, Neo4j, PostgreSQL, and Redis ready.
- Diagnostics reported `Api_gateway` and `Workers` stopped. Their required vs.
  optional installed-role classification remains part of CP19-M; this evidence
  does not convert those states into an acceptance waiver.
- Algorithm Registry loaded manifest `2026.08.11-AL10.2` and rendered canonical
  KA cards and plan/run controls. No effectful KA run was initiated during this
  visual inspection.

One known Windows startup warning, `Signal-based timeout not available on this
platform`, is written to backend stderr and therefore wrapped by Electron as a
top-level `ERROR` even though the backend proceeds to readiness. It is retained
as observability cleanup; it was not a runtime failure in this acceptance run.

## Validation inherited from the exact source line

The post-QC source qualification preceding the artifact passed 3,108 backend
tests with 18 skipped, 435 frontend tests, frontend lint/typecheck/Next/Electron
builds, 36 Python SDK tests, eight TypeScript SDK tests, documentation truth
10/10, 350 live routes with zero unclassified or unauthenticated mutations,
zero route collisions, and zero orphan/blocked bytecode results.

## Retained CP19-M and release blockers

The following remain open and fail closed:

1. Conclusive elevated per-machine install, Program Files launch, repair,
   upgrade, retained-data, uninstall, and cleanup evidence for this exact hash.
2. Valid publisher signature, trusted timestamp, revocation/chain checks, SBOM,
   provenance, attestations, and approved distribution authority.
3. Installed Phase 9-13 matrices, protected-volume/key recovery,
   backup/restore/delete parity, failure/recovery, and performance evidence.
4. Real OpenAI/Google provider and corpus acceptance, gateway/private-host
   interoperability, and blinded-human evaluation.
5. Packaged keyboard, scaling, high-contrast, screen-reader/NVDA, and complete
   enabled-control acceptance.
6. Independent security/accessibility/professional review, clean-machine pilot,
   and 24/72-hour soaks.

CP16-G, CP17-E, CP15-A through CP15-H, Phase 8 signing, distribution, and
production GO remain unbound and open.
