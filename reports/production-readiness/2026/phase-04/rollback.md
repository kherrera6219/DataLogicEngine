# Phase 4 Rollback

1. Stop the application and materialization worker before changing a populated
   runtime root.
2. Preserve the current coordinated `.dlebackup` archive and recovery secret.
3. For a failed restore activation, use the prior root retained by the atomic
   swap; do not merge individual store directories.
4. For an incompatible migration, refuse startup and restore the complete prior
   recovery set. Run Alembic downgrade only where that exact revision rollback
   has been tested and a verified coordinated backup exists.
5. Pending materialization events remain PostgreSQL-authoritative and can be
   replayed after the prior root is restored.
6. Do not downgrade against a newer data version, flush Redis, delete the prior
   root, or copy a single store into a mixed-version installation.
7. Reverting source code alone is insufficient when the data version changed;
   source, migration head, per-store versions, and recovery root must agree.
