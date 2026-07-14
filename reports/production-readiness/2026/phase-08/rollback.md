# Phase 8 Rollback Contract

Date: 2026-07-13

If the Phase 8 gateway contract must be disabled or rolled back before release:

1. Disable new external client admission and keep the desktop owner boundary
   available for local diagnosis where safe.
2. Revoke affected client keys and cancel their queued/running jobs through the
   lifecycle API. Do not expose or reconstruct copy-once secrets.
3. Preserve PostgreSQL key, idempotency, virtual-model, async-run, audit, usage,
   and trace rows plus referenced encrypted S3 result objects.
4. Do not downgrade populated migrations `e4f5a6b7c8d9` through `b7c8d9e0f1a2`
   destructively. An older binary must understand the schema or refuse startup.
5. Keep private mode disabled. Remove any lab-only certificate/firewall state
   through the private gateway runbook rather than opening a fallback listener.
6. Do not restore broad read/write permissions, process-local rate limiting,
   ungoverned compatibility routes, early provider-token release, or filesystem
   result fallback.
7. Re-run Phase 5-8 governed, provider, gateway, storage, migration, SDK,
   frontend, documentation, and compatibility gates before re-enabling clients.

This rollback contract does not authorize production release or change the
SeaweedFS candidate-only, ChromaDB alert, or installed evidence gates.
