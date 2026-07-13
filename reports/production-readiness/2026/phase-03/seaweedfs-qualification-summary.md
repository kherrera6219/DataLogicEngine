# SeaweedFS Replacement Qualification Summary

## Decision

SeaweedFS remains a qualification candidate and is **not** the approved
production object store. The MinIO product-specific target architecture remains
unchanged under Replacement Control.

## Live Windows lab result

The 2026-07-13 run used the immutable SeaweedFS 4.29 image on the dedicated
rootless DataLogicEngine Podman Machine. The candidate became ready and all
uniquely named containers, volumes, networks, and secrets were removed after the
run.

### Passed

- immutable index and Linux amd64 digest verification;
- SeaweedFS binary/version and declared Apache-2.0 image metadata;
- loopback-only S3 publication on `127.0.0.1`;
- non-root UID/GID 1000 process, read-only root filesystem, no effective
  capabilities, no-new-privileges, memory/PID/CPU budgets, and runtime-secret
  credential delivery;
- anonymous, invalid-credential, and unauthorized bucket-creation denial;
- put/get/head/prefix-list/delete, content type, metadata, SHA-256 integrity,
  multipart upload, and presigned GET;
- 32-object, eight-worker concurrent write/read/hash smoke in 0.276 seconds;
- graceful restart and forced-termination durability with exact read-back hash;
- portable backup of 34 objects / 2,359,345 bytes and verified clean-data-root
  restore;
- local-to-candidate migration and candidate-to-local rollback with object,
  metadata, and hash parity;
- credential absence from container inspection and captured logs;
- complete cleanup of disposable qualification resources.

### Failed or incomplete

- the installed Windows Podman client is 5.8.3 and the machine server is 5.8.5,
  while the distributable candidate lock records official Podman 5.8.2;
- version/identity observability now uses the immutable image, binary, and
  supervisor identity evidence because the mini-server log stream does not emit
  a standalone version record;
- independent SeaweedFS license/redistribution/notices/support review is pending;
- independent security, TLS, data-at-rest, BitLocker/store-encryption, and
  vulnerability review is pending;
- corruption, disk-full, port-conflict, backup-failure, restore-failure, and
  comparative recovery tests are pending;
- a clean-machine signed installer/supervisor/relaunch qualification is pending;
- required audit, simulation, and deliverable object writes now fail closed in
  the managed profile, and Boto3 is a direct pinned dependency;
- supervisor and source-tested Storage UI integration are complete, but the
  rebuilt installed-shell qualification remains pending;
- final ADR acceptance and final owner production approval are pending.

## Evidence

- `seaweedfs-replacement-qualification-windows.json`
- `object-store-caller-contract-inventory.md`
- `cp3-a-version-license-audit.md`
- `service-candidates.json`
- `docs/adr/ADR-0004-seaweedfs-replacement-qualification.md`

The JSON report intentionally returns a blocked result while any required gate
is failed or pending. No architecture rename or production provisioning is
authorized by this lab result.

## Five-service integration result

`internal-data-plane-qualification.json` separately records a passing live run
of the complete PostgreSQL/Redis/Neo4j/Chroma/SeaweedFS qualification profile,
including restart durability, truthful identities, and full cleanup. That run
is an engineering checkpoint and retains `production_authorized: false`.
