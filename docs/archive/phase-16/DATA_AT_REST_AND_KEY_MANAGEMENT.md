# DataLogicEngine Data-at-Rest and Key-Management Standard

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Last updated | 2026-07-13 |
| Status | Active engineering standard; supported-Windows qualification pending |
| Owner | Security Engineering |
| Policy version | `2026.07.13-v1` |

## Approved protection model

The approved design combines:

1. BitLocker or Windows device encryption on every active, temporary, retained,
   export, diagnostic, and service-data volume used by the production profile.
2. Restrictive current-user/System ACLs on the installation runtime root.
3. DPAPI current-user wrapping for installation, provider, and internal-service
   secrets, with plaintext/default credential paths refused in production.
4. AES-256-GCM portable backup encryption with a user-controlled recovery
   secret and a signed, hashed manifest.

ACLs and non-obvious paths are access controls, not encryption. Production
startup verifies the active volume and runtime-root ACL and fails closed when
either requirement is not proven.

## Key separation and recovery

| Purpose | Authority | Storage rule |
|---|---|---|
| Active service/provider secrets | Windows DPAPI, current user | Stored only in protected vaults; never included in backups or logs |
| Backup encryption and manifest authentication | Owner recovery secret, scrypt-derived keys | Secret is entered locally, is not persisted in the archive, and must be retained by the owner |
| Restored internal-service credentials | New installation identity | Generated for the isolated restored root; old machine-bound secrets are not copied |
| Field encryption | Backend encryption manager with DPAPI-protected local material | Rotation must preserve decryptability until verified migration completes |

Losing the portable recovery secret makes the archive unrecoverable. A backup is
not considered valid until encryption, manifest authentication, component hashes,
and archive readback all pass.

## Temporary data, exports, and deletion

Backup/restore staging is isolated and removed after completion or failure.
Plaintext `.env`, credential, secret, unencrypted backup, and temporary residue
patterns are checked. Owner-selected exports and support bundles remain outside
the runtime root and inherit the owner's selected destination protection.

Secure deletion cannot be guaranteed on every SSD, virtual disk, snapshot, or
backed-up volume. The product must state this residual risk and use retention
expiry or destruction of encryption material where technically applicable.

## Qualification status

The Phase 4 engineering drill proved encrypted portable backup and isolated
clean-root restore. The current development machine did not prove protected
volume status or the supported installed-root ACL, so CP4-F and production
authorization remain open until the rebuilt signed installer runs the Windows
matrix, including copied-root, offline-disk, alternate-user, lost-key,
rotated-key, crash-cleanup, and partial-encryption scenarios.
