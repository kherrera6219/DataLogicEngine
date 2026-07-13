# Phase 3 Rollback Notes

## Qualification profile

The disposable qualification profile can be removed only through
`PodmanDataPlaneManager.remove_qualification_profile()`. Removal is restricted
to the qualification profile and covers its five containers, named volumes,
secrets, private network, and labels. The final live gate proved every resource
was removed successfully.

The credential vault is outside the disposable Podman resources so repeated
qualification runs retain the same installation identity and credentials. It
contains no production authorization.

## Code rollback boundary

Reverting the Phase 3 commit restores the legacy development adapters and UI,
but it must not be used as a production fallback. A rollback does not authorize
SQLite, filesystem object storage, cloud database fields, floating Compose
images, or known/default credentials for production.

No production user data was migrated in this phase. The live services used a
qualification-only installation identity and were deleted after verification.

## Object-store candidate rollback

The candidate qualification separately proved S3-to-local export/rollback with
key, content, metadata, and SHA-256 parity. This is engineering evidence only;
production migration and rollback remain prohibited until ADR-0004 is accepted
and Phase 4 recovery contracts pass.
