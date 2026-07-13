# Phase 0 Rollback

Phase 0 authority and inventory work does not migrate or delete user data.

1. Revert Phase 0 evidence and inventory artifacts as one reviewable change.
2. Restore archived TODO/HANDOFF only if the owner revokes the active plan.
3. Do not delete archived history.
4. Do not alter databases, credentials, installer data, or service volumes.

The Phase 0 Podman containers use only disposable generated credentials and data.
After evidence capture they are removed and the `datalogicengine` machine is
stopped. To remove the runtime experiment entirely, verify the exact machine name
and then run `podman machine rm datalogicengine`; uninstall Podman through Windows
Installed Apps. Do not remove a later production machine or persistent volume
under this Phase 0 procedure.
