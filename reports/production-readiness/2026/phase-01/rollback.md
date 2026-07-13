# Phase 1 Rollback

Phase 1 changes authentication, listener, public-error, IPC, path, and
credential-storage contracts. Roll back the phase as one commit; do not weaken a
single failing route to anonymous access, wildcard CORS, non-loopback bind,
plaintext secret storage, generic IPC, or raw exception output.

There is no schema migration, but new writes after Phase 1 can use
DPAPI-prefixed provider and internal-service credential values. Pre-Phase-1
code cannot consume those values safely.

Rollback procedure:

1. Stop Electron and the backend; preserve redacted logs and the encrypted
   runtime directory.
2. Record the current commit and copy the database/settings/secret files to a
   user-protected incident location. Do not place them in a normal backup or
   support bundle.
3. Revert the complete Phase 1 commit.
4. Re-enter provider/internal-service credentials through the rolled-back UI;
   never convert a DPAPI value to plaintext by hand.
5. Expect desktop sessions to be invalidated if the install secret rotated.
6. Re-run anonymous-mutation, public-error, listener, and credential-leak tests
   before restarting normal work.
7. Restore Phase 1 immediately if a rollback would require public diagnostics,
   external-key owner access, arbitrary renderer paths, or non-loopback exposure.
