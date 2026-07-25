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

The selected implementation qualification separately proved app-owned
S3-compatible object-store export, clean restore, local-to-S3 migration, and
S3-to-local rollback with key, content, metadata, and SHA-256 parity. Corrupt
manifest, corrupt blob, and missing-blob backups were rejected before restore
writes. ADR-0010 accepts SeaweedFS `4.40-dle.1` for rebuilt installed
qualification and supersedes the historical Proposed ADR-0004.

This remains engineering evidence only. Production migration and rollback stay
prohibited while `production_approved=false`; the rebuilt signed application
must pass clean-machine delivery, protected-volume, coordinated backup/restore,
independent security/license, and final owner release gates first.
