# DataLogicEngine installation and lifecycle guide

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-USER-002 |
| Title | Installation and lifecycle guide |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | qualification_only |
| Audience | Supported users, evaluators, desktop administrators, and release reviewers |
| Owner | Platform Operations |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | NSIS packaging controls, Windows runtime implementation, release trust policy, and installed qualification plan |
| Confidentiality | Public |
| Last reviewed | 2026-07-14 |
| Next-review trigger | Installer, signing, prerequisite, lifecycle, data-location, update, or supported-Windows change |
| Requirements and evidence | Product requirements, release manifest, installer verification, Phase 15 evidence, and lifecycle acceptance |

## Current distribution status

DataLogicEngine 4.3.0 is not approved for production or public installation.
The current engineering candidate is unsigned and is for controlled qualification
only. It passed payload and integrity checks, but its packaged backend correctly
stopped at `at_rest_protection_not_ready` on the development workstation. Two
clean candidate builds also produced different hashes. Do not treat an unsigned,
stale, `Latest`, or locally rebuilt artifact as the production installer.

The production procedure below becomes authoritative only when the release
record names the exact signed installer, SHA-256, publisher, timestamp, source
commit, supported Windows matrix, and accepted lifecycle evidence.

## Supported target

The approved target is Windows 11 x64 on a user-controlled desktop or Windows
VM. The installed application uses Electron, a loopback backend, and app-owned
app-owned PostgreSQL, Redis, Neo4j, ChromaDB, and S3-compatible object-store
services. Public cloud/SaaS,
macOS, Linux, mobile, and public-internet gateway deployments are unsupported.

The final release must document required disk, memory, CPU, virtualization,
rootless Podman/WSL2, protected-volume, elevation, and network prerequisites from
the signed installed qualification. Those hardware and delivery values are not
yet ratified and must not be guessed from development machines.

## Before installation

1. Obtain the installer only from the release location named in the approved
   release-readiness record.
2. Confirm the filename is `DataLogicEngine Setup 4.3.0.exe`.
3. Confirm the published SHA-256 matches the installer.
4. Open Windows file properties and verify a valid signature from the approved
   publisher, a trusted chain, a valid timestamp, and no revocation failure.
5. Confirm the Windows build, available resources, protected data volume, and
   virtualization prerequisites are in the signed release support matrix.
6. Back up any existing DataLogicEngine data before repair, upgrade, rollback,
   or uninstall.
7. Close other DataLogicEngine processes. Do not remove a live runtime lock or
   stop a foreign process merely because it occupies a preferred port.

If any identity, signature, hash, prerequisite, or backup check fails, stop and
follow the troubleshooting guide. Do not bypass readiness or trust controls.

## Clean installation

1. Run `DataLogicEngine Setup 4.3.0.exe` as the Windows user who will own the
   installation.
2. Review the publisher and version displayed by Windows before continuing.
3. Select only an approved protected local data location when prompted.
4. Allow only the documented app-owned service and firewall changes. The normal
   desktop profile remains loopback-only.
5. Complete installation and launch DataLogicEngine from the installed shortcut.
6. Wait for readiness. A live backend is not necessarily ready; the desktop must
   show a safe blocker if required services, identities, migrations, storage
   protection, or policies do not pass.
7. Open Settings and Diagnostics and confirm product 4.3.0, runtime identity,
   required service state, external telemetry state, and update state.
8. Configure one supported provider only after reviewing the privacy/AI notice.
   A stored key is not `available` until its bounded live test passes.

These steps require completion of the signed CP15-A lifecycle matrix before they
may be described as production-validated.

## First-use acceptance

After a clean installation, verify:

1. Dashboard opens without bypassing a readiness failure.
2. Settings shows truthful provider and storage states.
3. A governed chat request returns a stable run/trace ID or an explicit blocked,
   failed, cancelled, unavailable, or offline outcome.
4. Runs/Trace Explorer displays only executed stages and reports absent metrics
   as `not measured`.
5. Diagnostics can preview a content-free support bundle without uploading it.
6. Privacy controls identify local data, provider egress, exports, and supported
   deletion actions.
7. Restart, reboot, sleep/resume, and provider-offline behavior match the release
   acceptance record.

## Repair

Use repair only with the exact signed installer version named by the release
record. Create and verify an encrypted coordinated backup first. Repair must
preserve installation identity and retained data unless the UI explicitly states
otherwise, restore only approved binaries/configuration, rerun readiness and
migrations, and leave unrelated applications and ports untouched. Record the
repair log and rerun the first-use acceptance steps.

Repair behavior remains an open installed qualification gate for 4.3.0.

## Upgrade

1. Read the release notes and supported upgrade matrix.
2. Create an encrypted coordinated backup and verify its manifest.
3. Confirm the new installer signature, version, and hash.
4. Close the application and run the approved installer.
5. Allow the startup coordinator to apply versioned per-store migrations before
   readiness; never use automatic schema creation as a production shortcut.
6. Verify retained sessions, traces, provider settings, knowledge, graph/vector/
   object consistency, client keys/jobs, connector consent, backup, and deletion.
7. Retain the pre-upgrade backup until the acceptance window closes.

The 0.1.1 retained-data-to-4.3.0 path and clean signed upgrade remain open gates.

## Rollback

Rollback is permitted only when the release matrix names a supported target and
the retained data/schema version is compatible. Stop the app, preserve failure
evidence, verify the prior signed installer and backup, restore into an isolated
root, verify integrity and schema compatibility, then atomically activate the
approved root. Never point an older binary at a newer unsupported populated
store or manually copy partial database directories.

Rollback and interrupted-update recovery remain open installed gates.

## Uninstall and data choice

Before uninstalling, export any approved records and create a verified backup if
retention is required. Use Windows Installed Apps or the signed installer's
documented uninstall entry. The final release must present an explicit choice:

- retain app-owned data for a later reinstall or recovery; or
- delete app-owned active data through the coordinated deletion path.

Deletion must reconcile PostgreSQL, Redis, Neo4j, ChromaDB, object storage,
memory/local records, and logs and must report a partial failure. Exported files,
backups, VM snapshots, and immutable media may remain outside the uninstall and
must be handled separately. Secure erasure cannot be guaranteed for every SSD,
snapshot, or retained backup.

The exact silent uninstall syntax, exit codes, data-choice behavior, remnant scan,
and reinstall result remain CP15-A qualification gates.

## Updates

Automatic update is disabled. Environment variables cannot override the release
trust policy. It may be enabled only after production authorization proves signed
metadata, publisher identity, downgrade/replay rejection, staged activation,
offline behavior, and interrupted-update rollback. Until then, use only the
owner-approved signed installer procedure.

## Installation failures

Do not weaken a failing gate. Record the product version, installer hash/signature,
Windows build, lifecycle action, time, safe error code, and whether data changed.
Then use `docs/TROUBLESHOOTING_SUPPORT_GUIDE.md`. Security or signature concerns
must follow `SECURITY.md`, not a public issue.

## Development builds

Python, Node.js, source checkouts, unsigned builds, Docker-compatible checks, and
the development launch scripts belong to `docs/DEVELOPER_GUIDE.md`. They are not
end-user installation requirements and are not production release evidence.
