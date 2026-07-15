# Phase 15 retained release gates

Phase 15 closed the release-candidate engineering work that can be proved from
the frozen source and unsigned qualification artifacts. It did not close the
signed installed-product exit gate. A source/dev pass, unsigned portable launch,
or qualification-only service run cannot substitute for the exact signed RC.

| Checkpoint | Current evidence | Evidence still required to close |
|---|---|---|
| CP15-A - Lifecycle matrix | Candidate freeze, integrity, payload, and launch-to-backend evidence | Signed clean install, first run, close/reopen, reboot/crash, repair, 0.1.1 upgrade, migration rollback, interrupted update, keep/delete-data uninstall/reinstall, clean restore, rollback, concurrent launch, second-user, power-state, and operation-collision matrix |
| CP15-B - Functional matrix | Packaged backend reached startup gates; source contracts exist | Installed PostgreSQL, Redis, Neo4j, ChromaDB, and MinIO workflows; both supported providers; provider-disabled mode; MCP; simulation; native/SSE/async/SDK requests; durable store effects; no fallback |
| CP15-C - Failure matrix | Protected-storage and unsigned-publisher boundaries fail closed | Every service/provider/gateway/content/configuration/resource/security fault with public-safe error, correlation evidence, recovery action, and post-recovery parity |
| CP15-D - Performance/soak | Build performance and short source-level resource observations | Ratified reference hardware budgets, installed concurrency/load profile, crash-during-write recovery, 24-hour stress, 72-hour idle/normal-use soak, and bounded resource growth |
| CP15-E - Security/privacy | Payload leakage gate passes; candidate channel and unsigned state are explicit | Final CodeQL/dependency/secret/license/malware state, packaged Electron/network/egress inspection, all-output privacy proof, ASVS/SSDF evidence, threat review, and focused penetration test |
| CP15-F - Accessibility/docs | Source accessibility automation and current runbooks exist | Packaged visual/scaling/high-contrast checks, complete keyboard and manual NVDA acceptance, and clean-machine install/first-run/backup/restore/troubleshooting/uninstall document walkthrough |
| CP15-G - Human pilot | Pilot requirements are defined | Named owner-approved users, two clean non-development Windows machines, multiple normal-use days, every primary job, defect dispositions, and signed acceptance record |
| CP15-H - Gateway interoperability | Source contracts, SDKs, controls, and tests exist | Exact signed-RC same-host/private Windows native, SSE, async/cancel, SDK, compatibility, TLS/firewall/certificate, restart/recovery, and desktop-control-plane acceptance |

Cross-cutting blockers also retained:

- CP14-B two-build byte reproducibility: file sets match but normalized hashes do
  not; `github-candidate-reproducibility.json` remains failed.
- CP14-D approved publisher, certificate custody, signing, timestamp, revocation,
  and every final app-owned binary signature.
- CP14-E final signed SBOM/provenance/attestation/AV/license evidence.
- CP14-G legal/distribution approvals and third-party notices.
- Critical Dependabot alert 389, final object-store decision, independent
  architecture/security/license/recovery/accessibility/AI reviews, and every
  retained installed gate from Phases 3-14.
