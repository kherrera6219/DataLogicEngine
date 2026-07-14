# Phase 7 Rollback Contract

Date: 2026-07-13

If the Phase 7 provider contract must be rolled back before release:

1. Stop provider-backed requests and preserve redacted traces, usage-ledger rows,
   and offline-queue metadata.
2. Do not restore deleted SDK/direct provider execution paths or unsupported
   provider fallbacks; that would recreate parallel ungoverned paths.
3. Disable the affected provider capability and return a typed unavailable
   boundary while correcting the backend-owned adapter.
4. Preserve migration `d3e4f5a6b7c8` data during application rollback. A later
   binary must either understand the schema or refuse startup; do not downgrade a
   populated database destructively.
5. Delete or expire unsafe queue items through the owner API rather than editing
   ciphertext manually.
6. Re-run the Phase 7 focused and complete validation sets before re-enabling
   provider-backed work.

This engineering rollback contract does not authorize production release or
change the SeaweedFS candidate-only, ChromaDB alert, or installed evidence gates.
