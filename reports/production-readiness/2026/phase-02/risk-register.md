# Phase 2 Risk Register

| ID | Risk | Severity | Disposition |
|---|---|---|---|
| P2-R001 | Importing the Flask application creates shared runtime resources | Critical | Closed: dormant compatibility proxy plus 59-module static gate and subprocess import test |
| P2-R002 | Two app instances share configuration, stores, metrics, WebSocket, or SQL state | Critical | Closed: two-instance isolation tests prove independent app-owned state and no import-started threads/ports |
| P2-R003 | Port occupancy is misreported as an app-owned healthy service | Critical | Closed: supervisor and launcher require owned identity; foreign listeners become `blocked` or an actionable refusal |
| P2-R004 | Required production services fail but SQLite/memory/filesystem fallback appears ready | Critical | Closed for runtime policy: production SQLite and auto-schema are refused; required-service failure blocks readiness |
| P2-R005 | Concurrent launches, another Windows user, or incompatible version competes for one data root | Critical | Closed: per-user installation identity, OS lock, owner/version checks, and stale-lock recovery fail closed |
| P2-R006 | Sleep/logoff/shutdown or Electron close leaves the backend accepting mutations | High | Closed: signed lifecycle events enter drain/stop state; Electron uses bounded graceful shutdown and forced cleanup |
| P2-R007 | Full five-service production data plane is not delivered by the installer | Critical | Open release blocker assigned to Phase 3; MinIO/Chroma remain explicitly not installed and production readiness stays false |
| P2-R008 | Foreign DevOnz containers occupy the standard local data ports on this workstation | Medium | Environment conflict safely detected; Phase 3 must assign installation-specific ports/names and prove clean-machine provisioning |
| P2-R009 | Deprecated `from app import app` callers can still trigger the compatibility application | Medium | Accepted migration shim; all process entry points use `create_app()` and import alone is side-effect free; remove remaining consumers in later consolidation |
| P2-R010 | Worker/provider-specific cancellation and durable queue reconciliation depend on concrete Phase 3/7 adapters | High | Runtime admission, exclusive-operation, lifecycle callback, and bounded cleanup contracts are complete; adapter-specific qualification remains release-blocking in owning phases |
