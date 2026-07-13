# Phase 1 Risk Register

| ID | Risk | Severity | Disposition |
|---|---|---|---|
| P1-R001 | Anonymous mutations reach validation or execution | Critical | Closed: exhaustive 179-rule runtime denial matrix passes |
| P1-R002 | Public responses expose exception or secret text | Critical | Closed: 353-file static gate, response sentinels, and GitHub CodeQL alert query are clear |
| P1-R003 | Route/surface classification overexposes owner/internal behavior | High | Closed: live HTTP plus GraphQL/IPC/MCP/file/network inventory has zero unclassified entries |
| P1-R004 | Renderer supplies arbitrary filesystem paths | Critical | Closed: single-use expiring picker tokens plus main-process purpose signature |
| P1-R005 | Credential plaintext, weak ACL, or backup/log mirror | Critical | Closed: safeStorage/DPAPI, current-user/System ACL, redaction, KEK fail-closed behavior, and backup exclusion tests pass |
| P1-R006 | Private listener or Host/Origin confusion | Critical | Closed: all entry points use loopback policy; unsafe bind, Host, Origin, and proxy Host inputs fail closed |
| P1-R007 | Importing the global Flask app performs runtime initialization | Medium | Accepted for Phase 1; deterministic app factory/startup ownership is Phase 2 |
| P1-R008 | Neo4j driver teardown logs after pytest capture closes | Low | Accepted test-lifecycle noise; no test or runtime control failure; retain for Phase 2 cleanup |
| P1-R009 | Same-user malicious process can inspect live process memory/UI | High | Explicit residual threat; DPAPI/ACL protects at rest, while signing/update/OS-hardening work continues in Phases 14-16 |
| P1-R010 | Phase 1 backup archive is not a portable encrypted recovery package | High | Explicitly deferred to coordinated encrypted backup/restore qualification in Phase 4; secrets are excluded now |
