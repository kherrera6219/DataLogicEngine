# SeaweedFS 4.40-dle.1 Engineering License and Redistribution Review

| Field | Evidence |
|---|---|
| Review date | 2026-07-24 |
| Scope | Engineering license inventory for the selected object-store implementation |
| Upstream project | SeaweedFS |
| Upstream release | 4.40 |
| Upstream source revision | `875cd1f67ea25e8965a4f5ba1e6aaf501ba6b6fa` |
| DataLogicEngine build revision | `4.40-dle.1` |
| Declared license | Apache License 2.0 |
| Exact upstream license SHA-256 | `d789d433cc11da163273d1e39be2e8fa67642f9a58ef220d3f258fa9c14ef613` |
| Exact upstream license bytes | `11,337` |
| Upstream `NOTICE` file | None in the exact release tree |
| Build recipe | `deploy/seaweedfs/Dockerfile` |
| Result | Engineering redistribution inventory passed; independent legal acceptance remains a release gate |

## Distribution obligations carried forward

The release package and third-party index must:

1. include the Apache License 2.0 text;
2. retain applicable copyright, patent, trademark, and attribution notices;
3. identify the DataLogicEngine dependency change from
   `google.golang.org/grpc` 1.81.1 to 1.82.1;
4. state that DataLogicEngine distributes a modified build and that the
   SeaweedFS name and marks are not an endorsement;
5. retain the exact upstream source revision, build recipe, image identity,
   vulnerability report, and packaged archive hash in release evidence; and
6. repeat this inventory and the independent acceptance step for every
   SeaweedFS or base-image update.

No separate upstream `NOTICE` file exists in the exact 4.40 source tree. The
vendored Rust and Go components remain subject to their own notices and are
covered by the generated image SBOM and release third-party inventory.

## Security-motivated modification

The official SeaweedFS 4.40 image embeds `google.golang.org/grpc` 1.81.1.
`GHSA-hrxh-6v49-42gf`, published 2026-07-21, is fixed in 1.82.1. The
DataLogicEngine image rebuilds the exact 4.40 source revision with 1.82.1 and
labels the change. The exact rebuilt image was scanned separately; it has zero
High or Critical findings. The remaining `GO-2026-5932` result is an
unscored Go database notice about the unmaintained `openpgp` package and is
retained in the scan report rather than suppressed.

## Boundary

This record is an engineering inventory, not legal advice or independent legal
approval. Production provisioning remains disabled until the later signed,
installed release gates, including independent license acceptance, pass.
