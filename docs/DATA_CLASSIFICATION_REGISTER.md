# DataLogicEngine Data Classification Register

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Privacy + Security Engineering |
| Code authority | `backend/storage/data_at_rest.py` and `backend/storage/retention.py` |

## Classification register

| Data class | Sensitivity | Principal locations | Required protection | Retention basis |
|---|---|---|---|---|
| Provider credentials | Restricted | PostgreSQL, DPAPI vault | DPAPI plus protected volume | Installation lifetime |
| Client credentials | Restricted | PostgreSQL | Field encryption plus protected volume | Revocation/security policy |
| Prompts and chats | Confidential | PostgreSQL, exports | Protected volume; encrypted export when selected | Owner deletion/history policy |
| External-client requests/results | Confidential | PostgreSQL, MinIO | Protected volume and object access policy | Gateway policy |
| Traces and evidence | Confidential | PostgreSQL, MinIO | Protected volume and object access policy | Trace/evidence policy |
| Gateway audit and usage | Confidential | PostgreSQL, MinIO, minimized logs | Protected volume and integrity chain | Disclosed audit/usage policy |
| Ingested documents | Confidential | PostgreSQL, ChromaDB, Neo4j | Protected volume and authenticated loopback services | Ingestion/source policy |
| Embeddings | Confidential | ChromaDB | Protected volume and authenticated loopback service | Source policy |
| Graph data | Confidential | PostgreSQL, Neo4j | Protected volume and authenticated loopback service | Graph/source policy |
| Simulations | Confidential | PostgreSQL, MinIO | Protected volume and object access policy | Owner deletion |
| Exports | Confidential | Owner-selected path | Owner-selected encryption and short-lived staging | Export policy |
| Logs | Internal | Runtime logs | Protected volume, restricted ACL, content minimization | Rotation policy |
| Backups | Restricted | Owner-selected path | AES-256-GCM, signed manifest, owner recovery secret | Backup retention/expiry |
| Support bundles | Confidential | Owner-selected path | Redaction and owner-selected encryption | Support policy |
| Retained JSON/SQLite | Confidential | Runtime databases | Protected volume, restricted ACL, versioned format | Retained-data policy |
| Temporary staging | Confidential | Runtime staging | Protected volume, restricted ACL, immediate cleanup | Operation lifetime |

## Retention and deletion rules

The canonical retention registry defines 17 operational classes. Cross-store
user deletion covers PostgreSQL, Redis, Neo4j, ChromaDB, MinIO, local JSON, and
logs. A non-PII keyed tombstone records per-store completion; any store failure
returns a partial-failure result and prevents a success claim. Immutable remnants
are permitted only when an explicit disclosed security or regulatory basis is
recorded.

Uninstall offers only explicit `keep`, `export_then_delete`, or `delete`
dispositions. Export-then-delete requires a verified coordinated backup. Secure
deletion is not promised for SSDs, virtual disks, snapshots, or retained backup
copies; retention expiry and cryptographic erasure are used where applicable.
