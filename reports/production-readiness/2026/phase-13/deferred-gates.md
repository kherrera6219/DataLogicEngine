# Phase 13 deferred installed acceptance gates

Date: 2026-07-14 (America/Los_Angeles)

Status: release-blocking; production/public release remains **NO-GO**.

The source engineering checkpoint does not satisfy the installed Phase 13 exit
gate. Complete these after the application is rebuilt and installed:

1. Reconstruct one real run across Electron, Flask, orchestrator/workers,
   provider/tool boundaries, PostgreSQL, Redis, Neo4j, Chroma, the selected S3-
   compatible object-store candidate, simulation, ingestion, and MCP using safe
   correlation/run evidence.
2. Execute the complete failure-injection matrix for auth, policy, configuration,
   migration, service loss, provider/tool failure, timeout, cancellation,
   persistence, corruption, disk exhaustion, resource pressure, and shutdown.
   Every outcome must match the approved safe state and evidence contract.
3. Run canary secrets/PII/content through installed logs, metrics, local crash
   evidence, Electron/renderer output, audit/export, and owner-created support
   bundles. Verify no forbidden value or unexpected egress.
4. Exercise the installed Diagnostics page, preview/confirmation/export flow,
   retention, archive/sidecar verification, optional CLI encryption, and recovery
   guidance with the real runtime root and services.
5. Resolve or explicitly schedule the four real import cycles recorded in
   `python-import-cycles.json`; do not restore the former fabricated pass.
6. Continue deliberate conversion of the 1,104-site broad-catch legacy queue.
   Core logic must use typed handling; broad catches may remain only at reviewed
   process/task boundaries that preserve safe terminal state.
7. Run the full installed 24-hour `stress24` and 72-hour `idle72` profiles while
   monitoring memory, handles, threads, children, connections, queues, logs,
   caches, object growth, failures, correlation, and outbound calls. Short runs
   can never satisfy CP13-E.
8. Obtain owner/operations/security review of evidence-backed framework/control
   wording and verify no UI, PDF, API, or exported record implies independent
   certification.
