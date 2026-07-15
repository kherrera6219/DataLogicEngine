# Third-party notices readiness

Date: 2026-07-14

Status: **not approved for production distribution**.

Phase 14 now records exact Python, Node/Electron, Podman, PostgreSQL, Redis,
Neo4j, ChromaDB, and SeaweedFS candidate versions/digests/licenses in the
dependency authority, service SBOM, and release manifest. That inventory is an
engineering input; it is not the final legal notice bundle or a redistribution
approval.

Before distribution, the release owner must:

1. generate backend, frontend, internal-service, JRE, and installer SBOMs from
   the exact clean release candidate;
2. reconcile package metadata with authoritative license texts and notices;
3. resolve missing, ambiguous, custom, copyleft, font, icon, model/provider, and
   sample-data terms;
4. complete the ten release-blocking Phase 0 legal/distribution actions;
5. obtain owner-directed legal/export review for intended regions and use;
6. approve and archive one notice bundle with the release manifest, hashes,
   signatures, attestations, scan results, and release approval.

No workflow or document may infer commercial redistribution authority from a
package-manager license field. Redistribution remains fail-closed until
verify_release_ownership.py --require-release-ready passes and the final notice
bundle is reviewed.
