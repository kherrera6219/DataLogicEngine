# Phase 3 Risk Register

| ID | Risk | Severity | Disposition |
|---|---|---|---|
| P3-R001 | A floating or substituted service artifact runs as the app data plane | Critical | Closed for implementation: immutable lock, local-image verification, identity labels, and production authorization gate |
| P3-R002 | Default/plaintext credentials or production `.env` authority expose internal services | Critical | Closed for implementation: per-install random credentials in DPAPI/ACL vault and Podman secrets |
| P3-R003 | A foreign container/listener is adopted or reported healthy | Critical | Closed: installation labels, expected identity/digest, exact loopback publication, and protocol probes are mandatory |
| P3-R004 | PostgreSQL/Redis/Neo4j/Chroma/S3 failure silently falls back to SQLite, memory, or filesystem | Critical | Closed for managed production policy; required construction, initialization, probes, and artifact writes fail closed |
| P3-R005 | SeaweedFS is mistaken for an approved production replacement | Critical | Open release blocker: qualification-only profile, ADR-0004 Proposed, production lock false, architecture remains MinIO-specific |
| P3-R006 | Redis/Neo4j/object-store/runtime redistribution lacks independent authority | Critical | Open release blocker assigned to legal/distribution register and Phase 14 |
| P3-R007 | Clean installer does not deliver the exact locked runtime/profile | Critical | Deferred to rebuilt signed installer and Phase 15 clean-machine qualification; not passed in Phase 3 |
| P3-R008 | Cross-store backup/restore, corruption, disk-full, or partial recovery loses data | Critical | Open and assigned to Phase 4 plus final failure qualification |
| P3-R009 | Installed Storage UI differs from source-tested truthful state/actions | High | Source/unit/build validation passed; installed-shell proof deferred to rebuilt candidate and Phase 15 |
| P3-R010 | Lab Podman version differs from the locked distributable | High | Explicit blocker: lab client 5.8.3/server 5.8.5 versus locked 5.8.2; exact artifact qualification remains open |
| P3-R011 | Chroma/object-store collection, lifecycle, retention, pagination, and cross-store deletion contracts are incomplete | High | Open work assigned to Phase 4 data contracts/recovery and Phase 9 retrieval completion |
| P3-R012 | Coordinated backup endpoint suggests a partial backup is safe | Critical | Closed for Phase 3: managed Podman backup refuses with `coordinated_data_plane_backup_requires_phase_4` until Phase 4 implements it |
