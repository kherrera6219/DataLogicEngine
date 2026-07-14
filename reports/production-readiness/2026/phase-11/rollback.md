# Phase 11 Rollback and Safe Disablement

Date: 2026-07-14

1. Keep `DLE_MCP_CONNECTORS_QUALIFIED=false` to prevent production connector
   startup while retaining inspectable durable records.
2. Revoke active consent and stop every connector before application rollback.
3. Confirm all Job Object process trees have exited; investigate any orphan before
   continuing.
4. Back up PostgreSQL and required object buckets before migration downgrade.
5. Downgrade migration `e0f1a2b3c4d5` only after confirming no retained consent,
   lifecycle, execution, or result-reference evidence is required.
6. Remove `mcp-results` objects only after proving no surviving database reference
   and preserving required audit evidence.
7. Clear content-free Redis MCP live keys only after durable lifecycle state has
   been confirmed in PostgreSQL.
8. Do not restore repository JSON auto-start, fake defaults, fake sampling, or
   permissive caller-owned scope behavior. A rollback disables MCP rather than
   reintroducing unsafe behavior.

Rollback validation requires the same supported installed baseline used for the
forward migration and remains part of the deferred installed gate.
