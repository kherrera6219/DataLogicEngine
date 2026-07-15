# Security Policy

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ROOT-003 |
| Title | Vulnerability reporting and disclosure policy |
| Document version | v2.7.0 |
| Product version | 4.3.0 |
| Status | active |
| Audience | Security researchers, users, maintainers, and release reviewers |
| Owner | Security Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Security policy, supported-version authority, and release-risk records |
| Confidentiality | Public |
| Last reviewed | 2026-07-14 |
| Next-review trigger | Supported-version, reporting, threat, or disclosure-process change |
| Requirements and evidence | `docs/SECURITY.md`, `docs/THREAT_MODEL.md`, and security workflow evidence |

## Purpose

Define public vulnerability reporting guidance and summarize DataLogicEngine security posture at a high level.

For detailed internal security architecture, see `docs/SECURITY.md`.

---

## Supported versions

Security patches are provided for actively maintained release lines only.

| Version | Supported | Notes |
|---|---|---|
| Current 4.x line | Yes | Active development/release line. |
| Older lines | No, unless separately announced | Upgrade to the current maintained line. |

---

## Reporting a vulnerability

Do not report security vulnerabilities through public GitHub issues, pull requests, or discussions.

Use private reporting channels only.

Primary reporting channel:

```text
security@datalogicengine.com
```

You may also use GitHub private security advisory reporting if enabled for the repository.

Include as much of the following as possible:

| Field | Description |
|---|---|
| Vulnerability type | SQL injection, XSS, SSRF, broken auth, data exposure, etc. |
| Affected component | File path, endpoint, module, installer, workflow, or feature. |
| Affected version/commit | Version, tag, branch, or commit SHA. |
| Reproduction steps | Minimal steps to reproduce safely. |
| Proof of concept | Only safe, non-destructive examples. |
| Impact | What could be accessed, changed, or disrupted. |
| Suggested remediation | Optional. |

---

## Safe testing rules

Security researchers should:

1. test only accounts, systems, and data they own or have permission to test;
2. avoid destructive testing;
3. avoid denial-of-service testing against production systems;
4. avoid persistence, lateral movement, or data exfiltration;
5. stop testing and report immediately if sensitive data is encountered;
6. keep vulnerability details private until coordinated disclosure is complete.

---

## Vulnerability response process

After receiving a report, Security Engineering will:

1. acknowledge receipt;
2. triage severity and affected scope;
3. reproduce safely where possible;
4. develop and test a fix;
5. coordinate disclosure with the reporter;
6. release a patch or mitigation;
7. credit the reporter if requested and appropriate.

Severity and response targets are handled according to current release and incident-response procedures.

---

## Security architecture summary

DataLogicEngine uses a layered security model:

1. local-first Windows/Electron desktop trust boundary;
2. Flask API security envelope;
3. session, API, and desktop-local authentication controls;
4. CSRF, CORS, trusted-host, and rate/resource controls;
5. DMRF injection-defense checks;
6. TruthGate policy controls;
7. MCP connector scope and contract validation;
8. trace/export integrity controls;
9. privacy export/delete controls;
10. release and supply-chain governance checks.

Detailed controls are documented in:

1. `docs/SECURITY.md`
2. `docs/PRIVACY_AI_NOTICE.md`
3. `docs/SSL_CONFIGURATION.md`
4. `docs/CIS_BENCHMARKS.md`
5. `docs/SLSA_LEVEL_3_ATTESTATION.md`
6. `docs/RELEASE_CHECKLIST.md`
7. `docs/PRODUCTION_READINESS.md`

---

## Security claim policy

This public security policy intentionally avoids unsupported certification or benchmark claims.

Do not infer that this repository is certified for SOC 2, ISO 27001, ISO/IEC 42001, FedRAMP, SLSA Level 3, CIS Benchmark conformance, or any other formal standard unless a separate signed/validated attestation is provided.

Current documentation may include mappings, roadmaps, and evidence-guided controls, but those are not equivalent to certification.

---

## Known release caveats

Current caveats may include, depending on release mode:

1. trusted public Windows code-signing certificate provisioning;
2. signed installer artifact validation;
3. provider-backed staging validation;
4. production connector validation against real external systems;
5. manual accessibility evidence;
6. final release checklist approval.

See `docs/PRODUCTION_READINESS.md` and `docs/RELEASE_CHECKLIST.md` for current release posture.

---

## Additional resources

1. `docs/SECURITY.md`
2. `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`
3. `docs/PRIVACY_AI_NOTICE.md`
4. `docs/RELEASE_CHECKLIST.md`
5. `docs/DOCUMENTATION_STANDARDS.md`

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Replaced older claim-heavy public security summary with evidence-based public security policy.
3. Removed stale Active Defense Supervisor-LLM and blanket production-ready control claims from the public policy.
4. Added safe testing, security claim policy, and release caveats.
