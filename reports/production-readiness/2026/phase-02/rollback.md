# Phase 2 Rollback

Phase 2 changes process construction, runtime ownership, application-owned
extensions, startup/shutdown behavior, readiness, and Electron lifecycle
coordination. Roll back the phase as one commit; do not mix the old import-time
global application with the new runtime-owned stores or supervisor.

There is no new production schema migration. A local development migration may
have been applied during validation, but production still requires explicit
Alembic migration and PostgreSQL.

Rollback procedure:

1. Stop Electron and the backend through the lifecycle endpoint where available.
2. Run `scripts/windows/stop_local_stack.ps1 -WithDataServices` and verify no
   DataLogicEngine application listener remains.
3. Preserve the runtime-root installation identity, lock record, protected keys,
   database files, and redacted logs for incident analysis.
4. Revert the complete Phase 2 commit.
5. Do not delete `installation.json`, protected credentials, or data volumes to
   make the older runtime start; use a separate test root if rollback validation
   is necessary.
6. Re-run the Phase 1 trust/security gates before any restart.
7. Treat a rollback that reintroduces import-time threads, production SQLite,
   unverified port adoption, or a shell that opens before readiness as NO-GO.
