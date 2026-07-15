# Phase 12 Rollback Notes

Date: 2026-07-14

- UI semantics and Session Library naming are source-only changes; rollback is a
  normal source revert with no data migration.
- ADR-0009 preserves `/projects` compatibility routes, so existing bookmarks and
  stored chat sessions are not migrated.
- Offline queue metadata adds `snapshot_at` only; existing queue files remain
  compatible and request payload encryption is unchanged.
- The MCP containment change does not alter connector definitions or consent
  records. Rollback removes breakaway-descendant hardening and is not recommended.
- No installed application or production-like data root was mutated by this
  engineering checkpoint.
