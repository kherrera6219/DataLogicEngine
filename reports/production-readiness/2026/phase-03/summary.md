# Phase 3 Evidence Summary

## Status

| Field | Value |
|---|---|
| Phase | 3 - Full internal service delivery and supervision |
| Engineering checkpoint | 2026-07-13 |
| Replacement Control closure | 2026-07-24 |
| Checkpoint result | SeaweedFS selected for rebuilt installed qualification |
| Production authorization | `false` |
| Release posture | Production/public release remains **NO-GO** |

## Closure results

1. One installation-specific, rootless Podman profile owns PostgreSQL, Redis,
   Neo4j, ChromaDB, and the app-owned S3-compatible object-store capability.
2. ADR-0010 supersedes the historical Proposed ADR-0004 and selects SeaweedFS
   4.40-dle.1 for rebuilt installed qualification.
3. The exact selected image rebuilds SeaweedFS 4.40 source revision
   `875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa` with the upstream-fixed
   gRPC-Go 1.82.1 for `GHSA-hrxh-6v49-42gf`.
4. The app-owned image, OCI archive, Podman 6.0.1 Windows packages, source
   revision, build recipe, license inventory, and exact vulnerability report
   are locked by hashes and immutable identities.
5. The Windows lab used the exact Podman 6.0.1 client with the locked rootless
   5.8.5 WSL machine server baseline.
6. The selected image passed S3 contract, concurrency, restart/kill durability,
   backup and clean-root restore, corrupt/incomplete snapshot rejection,
   occupied-port fail-closed behavior, disposable disk-full recovery,
   local-to-S3 migration, and S3-to-local rollback.
7. Container and credential controls passed: loopback-only port, non-root
   process, read-only root filesystem, zero effective capabilities,
   no-new-privileges, resource limits, protected runtime secret, anonymous and
   invalid-credential denial, and least-privilege denial.
8. Trivy 0.70.0 reports zero High or Critical findings for the exact image.
   The unscored `GO-2026-5932` OpenPGP maintenance notice remains visible and
   unsuppressed.
9. The Apache-2.0 engineering redistribution inventory is complete and the
   owner selection is recorded. Production provisioning remains disabled.
10. GitHub Dependabot alert 389 is confirmed fixed after removal of the
    vulnerable ChromaDB Python SDK.

## Validation summary

- Replacement Control report: `passed_for_release_qualification`.
- All 12 engineering Replacement Control gates: **passed**.
- Disposable qualification resource cleanup: **passed**.
- High/Critical exact-image findings: **0**.
- Production selected for release qualification: **true**.
- Production approved/authorized: **false**.

## Deferred release acceptance

The following are intentionally retained and not converted into source/lab
PASS results:

- signed installer delivery, repair, upgrade, uninstall, and relaunch on clean
  supported Windows machines;
- installed protected-volume/BitLocker or approved equivalent behavior;
- independent security and license acceptance;
- packaged coordinated backup/restore, recovery, and data-plane lifecycle;
- final signed-artifact SBOM/notices/malware/signature verification; and
- CP15 lifecycle, Windows, provider, gateway, accessibility, pilot, and soak
  acceptance.

These gates control production approval. Their pending state does not reverse
the capability architecture or SeaweedFS implementation selection, and it does
not authorize a filesystem fallback.
