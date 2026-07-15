# Phase 14 live inventory

Date: 2026-07-14 (America/Los_Angeles)

Status: active engineering inventory; production/public release remains **NO-GO**.

## Version and dependency authority

1. Product versions conflict: root Python metadata reports `0.1.0`, the
   frontend/installer reports `0.1.1`, legacy configuration reports `1.0.0`,
   and the crash-release fallback and latest existing product changelog entry
   report `1.2.0`.
2. The installer filename is `DataLogicEngine Setup Latest.exe`, so artifact
   identity does not prove its embedded version.
3. `requirements.txt` is the documented/install/CI authority, but
   `pyproject.toml` is a partial dependency subset and `uv.lock` follows that
   subset. The three files therefore do not yet describe one reviewed graph.
4. `frontend/package-lock.json` exists and is lockfile v3, but release gates do
   not yet prove manifest/lock parity or ban lock drift.
5. The internal data-plane candidate lock pins service images by digest, but all
   production approvals remain false. SeaweedFS remains a qualification-only
   candidate under Replacement Control.

## Build and installer

1. The installer command rebuilds the PyInstaller backend before Electron, which
   closes the known stale-backend failure, but it does not require a clean tagged
   checkout or emit one immutable release manifest for all inputs/outputs.
2. Build output cleanup exists, but stale tracked root installer artifacts can
   still be mistaken for the current build outside the packaging command.
3. Portable and installer smoke scripts exist. Clean install, repair, supported
   upgrade, rollback, data-choice uninstall, non-default path, non-ASCII user,
   long path, standard-user runtime, and controlled elevation are not one
   complete installed matrix.
4. The current NSIS uninstall path retains application data by default and does
   not yet implement the required explicit keep/export-delete/delete choices.

## Signing and update trust

1. `verifyUpdateCodeSignature: false` is present in Electron Builder and is a
   production blocker.
2. Auto-update is disabled by default, but a generic feed can be enabled by
   environment configuration before downgrade, replay, wrong-publisher,
   tamper, interrupted-update, staged-rollout, and rollback qualification exists.
3. Authenticode scripts validate certificate health, SHA-256 signing,
   timestamping, revocation, and installer signatures, but trusted publisher
   credentials and clean-machine signed evidence are not available in source.

## Supply chain and distribution

1. Python/frontend SBOM jobs exist, but coverage does not yet include internal
   service assets, JRE, final installed contents, or one release manifest.
2. SBOM keyless signing can soft-pass when signing fails, and attestation
   verification is not a release gate.
3. Third-party Actions use mutable version tags rather than reviewed commit
   SHAs in multiple workflows.
4. The signing workflow materializes an exportable PFX on a normal hosted runner;
   the final signing service/hardware boundary and publisher identity are open.
5. Legal/distribution approvals, third-party redistribution review, signing
   identity succession, and final MSIX/external-location/offline EXE decision
   remain release-blocking Phase 0 decisions.

## Legacy retirement

SQLite, filesystem object storage, in-memory coordination/graph fallbacks,
duplicate legacy API prefixes, alternate app factories, and old installer paths
still require a production-build reachability gate and explicit migrate/remove/
disable disposition evidence.

## First implementation order

1. Install `config/product-versions.json` as the single product/contract/SDK
   version authority and fail builds on parity drift.
2. Reconcile the Python dependency manifests and strengthen npm lock parity.
3. Make artifact identity versioned, enable update-signature verification, and
   keep updates disabled until adversarial qualification passes.
4. Produce deterministic release manifest/SBOM/provenance gates and remove
   supply-chain soft passes.
5. Expand installer/legacy/legal evidence while retaining machine- and owner-
   dependent acceptance as explicit release blockers.
