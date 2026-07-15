# Phase 14 retained installed and authority gates

Date: 2026-07-14

These rows are intentionally not marked complete. They require the clean rebuilt
release candidate, an approved production publisher/distribution decision, or
independent evidence that does not exist at the source checkpoint.

| Gate | Current evidence | Required closure evidence | Owner phase |
|---|---|---|---|
| Canonical installer | Source requires DataLogicEngine Setup 4.3.0.exe; only stale 0.1.1/Latest local output exists | Clean tagged 4.3.0 backend/Electron build and artifact parity | Phase 15 |
| Repeatability | Normalized content inventory comparator implemented | Two isolated same-input builds with explained/approved nondeterminism only | Phase 15 |
| Lifecycle | NSIS policy and packaging smoke foundations exist | Clean/repair/upgrade/rollback and all uninstall data choices on supported Windows | Phase 15 |
| Windows matrix | Source preflight/ownership/ACL checks exist | Non-default path, non-ASCII user, long path, standard user and elevation results | Phase 15 |
| Publisher trust | Signature/publisher/timestamp/revocation verifiers exist | Approved publisher subject and managed/hardware signing boundary; all app binaries valid | Owner + Phase 15 |
| Signed updates | Updates are disabled and policy-gated | Adversarial online/offline update matrix including downgrade/replay/interruption rollback | Phase 15 |
| Final SBOM/provenance | Source generators and workflow attest/verify gates exist | Final installer/service/JRE SBOMs, signatures, attestations and verification logs | Phase 15 |
| Vulnerability/license/AV | npm audit and source gates pass | Final shipped-content vulnerability, license, AV and binary inventory review | Phase 15 |
| Distribution/legal | Structured register passes; 10 actions remain open | Written approvals for product/terms/privacy/providers/dependencies/regions/channel/publisher | Owner |
| Third-party notices | Readiness record identifies required inputs | Reviewed notice bundle exactly matching final shipped components | Owner + Phase 15 |
| ChromaDB alert 389 | Reachability mitigation retained; no patched upstream release | Reviewed patched replacement/upgrade and adversarial qualification | External upstream + owner |
| Object store | SeaweedFS qualification candidate only | Full Replacement Control, independent review and final owner approval | Owner + Phase 15 |
| Legacy reachability | Old installer bundle path excluded | Full disposition and signed-runtime import/route/config/bundle coverage | Phase 15 |
