# Phase 11 Residual Risk Register

Date: 2026-07-14

| Risk | Severity | State | Control / next evidence |
|---|---|---|---|
| Installed connector can reach files or network beyond declared capability | High | Open | Production start gate remains false; installed ACL/firewall qualification required |
| Child/grandchild survives crash, app exit, or reboot transition | High | Open | Job Object and hostile source tests exist; packaged crash/reboot qualification required |
| Large result object is written but PostgreSQL reference commit fails | Medium | Open | No false-ready record is returned; installed orphan scan/reconciliation must be qualified |
| Redis live publication fails after PostgreSQL commit | Medium | Controlled/open | PostgreSQL remains authority and Redis content-free; reconstruction/outage recovery needs installed proof |
| Credential can be exposed through installed identity or diagnostics | High | Open | DPAPI/redaction source controls exist; installed identity, ACL, log, and support-bundle tests required |
| SeaweedFS differs from required S3 capability or Windows operations | High | Open | Candidate only under Replacement Control; no architecture selection before all qualification passes |
| GitHub security alert 389 remains unresolved | Critical | Open | Release remains NO-GO until separately remediated and verified |

No open risk in this register is waived by the engineering checkpoint.
