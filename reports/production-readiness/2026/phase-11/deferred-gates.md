# Phase 11 Deferred Installed Gates

Date: 2026-07-14
Status: release-blocking until executed on the rebuilt application

1. Prove exact file-root access and denial outside the approved roots under the
   installed Windows identity and ACLs.
2. Prove outbound network allow/deny behavior with the installed firewall policy.
3. Prove DPAPI decryptability only under the intended installed identity and
   prove renderer, logs, diagnostics, and support artifacts cannot reveal values.
4. Run add, consent, discover, call, timeout, cancel, stop, restart, revoke,
   remove, app-exit, crash, and reboot flows in packaged Electron.
5. Prove memory/output/time limits and Windows Job Object child/grandchild cleanup
   against hostile installed connector binaries.
6. Prove PostgreSQL/Redis/object-store outage and recovery behavior, lifecycle
   reconstruction, large-result hash/reference integrity, and orphan-object
   reconciliation on populated data.
7. Prove migration upgrade and rollback from the supported installed baseline.
8. Confirm the final object store through Replacement Control. SeaweedFS remains
   candidate-only until parity, durability, backup/restore, security, licensing,
   migration/rollback, and Windows deployment qualification pass.
9. Resolve GitHub security alert 389 and all broader release gates retained by
   the production completion plan.

`DLE_MCP_CONNECTORS_QUALIFIED` must remain false in production until these MCP
installed gates are accepted and recorded.
