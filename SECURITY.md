# Security Policy

**Document Control**

| Field | Value |
|-------|-------|
| Owner | Security Engineering |
| Last Updated | March 2026 |
| Status | Active |
| Review Cadence | Every 30 days |
| Classification | Public |

---

## Table of Contents

1. [Supported Versions](#supported-versions)
2. [Reporting a Vulnerability](#reporting-a-vulnerability)
3. [Vulnerability Response Process](#vulnerability-response-process)
4. [Disclosure Policy](#disclosure-policy)
5. [Security Architecture Overview](#security-architecture-overview)
6. [Security Best Practices](#security-best-practices)
7. [Secure Coding Standards](#secure-coding-standards)
8. [Security Testing](#security-testing)
9. [Compliance and Regulatory Alignment](#compliance-and-regulatory-alignment)
10. [Incident Response](#incident-response)
11. [Security Update SLAs](#security-update-slas)
12. [Additional Resources](#additional-resources)
13. [Security Recognition](#security-recognition)
14. [Contact](#contact)

---

## Supported Versions

Security patches are provided for the following versions. Deployments on unsupported versions should be upgraded immediately.

| Version | Supported | End of Support |
|---------|-----------|----------------|
| 4.1.x (current) | Yes | Active |
| 4.0.x | Yes | TBD |
| < 4.0 | No | End of Life |

> **Note:** The version table was previously inaccurate (referencing 1.x versions). The current production version is the 4.x series. All prior versions are unsupported.

---

## Reporting a Vulnerability

> **Do not report security vulnerabilities through public GitHub issues, pull requests, or discussions.**

Public disclosure of unpatched vulnerabilities puts all users at risk. Please use private reporting channels only.

### Primary Reporting Channel

**Email:** [security@datalogicengine.com](mailto:security@datalogicengine.com)

You will receive an acknowledgement within **48 hours**. If you do not receive a response, follow up via email to confirm receipt.

### GitHub Private Security Advisory

You may also report vulnerabilities via GitHub's private security advisory feature:

1. Navigate to the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Complete the advisory form.

### What to Include in Your Report

To allow for rapid triage and investigation, include as much of the following as possible:

| Field | Description |
|-------|-------------|
| **Vulnerability type** | e.g., SQL injection, XSS, SSRF, broken authentication |
| **Affected component** | Module, file path, API endpoint, or feature area |
| **Affected version(s)** | Specific version or commit hash |
| **Reproduction steps** | Step-by-step instructions to reproduce |
| **Proof of concept** | Code or payload (if safe to share) |
| **Impact assessment** | What an attacker could achieve, and how |
| **Suggested fix** | Optional, but appreciated |

---

## Vulnerability Response Process

Upon receiving a security report, the Security Engineering team will:

1. **Acknowledge receipt** within 48 hours with a tracking reference.
2. **Assess and triage** the report within 7 business days, including:
   - Confirming reproducibility
   - Determining affected versions and scope
   - Assigning a severity rating (Critical / High / Medium / Low)
3. **Develop and test a fix** within the SLA for the assigned severity (see [Security Update SLAs](#security-update-slas)).
4. **Coordinate disclosure** with the reporter prior to public release.
5. **Release a patch** and publish a GitHub Security Advisory.
6. **Credit the reporter** (unless anonymity is requested).

---

## Disclosure Policy

We follow a **coordinated disclosure** model. We ask that reporters:

- Provide us reasonable time to investigate and remediate before public disclosure.
- Avoid accessing, modifying, or exfiltrating data beyond what is necessary to demonstrate the vulnerability.
- Limit testing to accounts and data you own or have explicit written permission to test.
- Do not perform actions that could degrade service availability (e.g., denial-of-service testing in production).

In return, we commit to:

- Respond and communicate transparently throughout the remediation process.
- Not pursue legal action against researchers acting in good faith within these guidelines.
- Publicly credit contributors in our [Security Recognition](#security-recognition) section.

---

## Security Architecture Overview

DataLogicEngine implements a multi-layer enterprise security architecture. The following controls are currently implemented and production-ready.

### Authentication and Identity

| Control | Description |
|---------|-------------|
| **MFA (TOTP)** | Time-based one-time password authentication with encrypted backup codes |
| **SSO / OIDC** | Azure AD / Microsoft Entra ID integration for enterprise identity federation |
| **Session Hardening** | Redis-backed session storage with rotation, HTTPONLY and SECURE cookie flags |
| **Account Protection** | Progressive lockout after failed attempts; configurable password expiry |
| **JWT Tokens** | Configurable expiration; refresh token rotation enforced |
| **Desktop No-Login Mode** | Local Electron mode with OS-protected secret storage (`safeStorage`) |

### Authorization

| Control | Description |
|---------|-------------|
| **Granular RBAC** | Permission-based access control (e.g., `user:manage_roles`, `data:export`, `knowledge:write`) |
| **API Key Scoping** | Encrypted API keys with per-tenant isolation |
| **Tenant Isolation** | Row-Level Security (RLS) enforced at the PostgreSQL database level |
| **Decorator Enforcement** | `@require_permission(Permission.X)` enforced on all protected routes |

### Data Protection

| Control | Description |
|---------|-------------|
| **Field-Level Encryption** | AES-256 encryption for sensitive PII fields (emails, metadata) via `EncryptionManager` |
| **KEK/DEK Pattern** | Secure key wrapping for encrypted database fields |
| **Transit Security** | TLS 1.3 enforced; HSTS headers applied |
| **Vault Integration** | Production secrets resolved from vault-backed sources; plaintext `.env` disallowed in production |

### Active Defense (2026)

| Control | Description |
|---------|-------------|
| **Dual-LLM Pipeline** | A secondary "Supervisor" LLM performs semantic intent analysis before execution, detecting jailbreaks, prompt injections, and adversarial DAN-mode prompts via `ActiveDefenseService` |
| **Honeypot Router** | High-threat sessions are routed to a sandboxed decoy environment for forensics capture without production data exposure (`HoneypotRouter`) |
| **Fail-Closed Design** | If the Supervisor LLM is unavailable, requests are blocked by default rather than passed through |
| **AGI Planner Hardening** | Strict `MAX_DEPTH` (3) and `MAX_TOTAL_GOALS` (50) limits prevent recursive planner DoS; all goals pass through `AIGuardrailService` |

### Network and API Security

| Control | Description |
|---------|-------------|
| **SSRF Protection** | API gateway enforces allowlist for upstream forwarding and enterprise health probes |
| **Rate Limiting** | Per-IP and per-user rate limiting via `Flask-Limiter` |
| **CSRF Protection** | CSRF tokens on all state-changing operations via `Flask-WTF` |
| **Security Headers** | HSTS, Content-Security-Policy, X-Frame-Options, X-Content-Type-Options enforced |

### Audit and Compliance

| Control | Description |
|---------|-------------|
| **Immutable Audit Trail** | Hash-chained audit events — EU AI Act and SOC 2 aligned |
| **SIEM Integration** | Real-time export to Syslog for SIEM ingestion |
| **Distributed Tracing** | End-to-end correlation IDs across all service calls |
| **Trace Export Signing** | Signed and encrypted trace export envelopes for evidence packaging |
| **Support Bundle Sanitization** | Diagnostic bundles sanitized before export to remove credentials and PII |

### Knowledge Algorithm (KA) Security

| Layer | Control |
|-------|---------|
| **L1 Input Validation** | KA-004 sanitizes all incoming queries before processing |
| **L3 Bias Detection** | KA-010 scans agent outputs for bias and harmful content |
| **L3 Adversarial Reasoning** | KA-034 tests for logical contradictions and manipulation attempts |
| **L7 Guardrail Integration** | All recursive planning passes through `AIGuardrailService` |
| **Fail-Safe Execution** | KA invocations use try/except with structured logging — failures degrade gracefully without system crash |

---

## Security Best Practices

### For System Administrators

**Environment Variables and Secrets**

- Never commit `.env` files or credentials to version control.
- Use vault-backed secret resolution in all production deployments (`PRODUCTION_VAULT_SECRETS_REQUIRED=true`).
- Rotate `SESSION_SECRET` and API keys on a regular schedule (quarterly minimum).
- Use OS-protected storage for desktop installations (`safeStorage` via Electron).

**Database Security**

- Enable SSL/TLS for all database connections in production.
- Restrict PostgreSQL access to the application service account only.
- Enable Row-Level Security (RLS) via the provided bootstrap scripts.
- Maintain encrypted database backups with tested restore procedures.

**Network Security**

- Enforce HTTPS in all production environments; disable HTTP.
- Place the application behind a reverse proxy (nginx, Azure Application Gateway) with TLS termination.
- Restrict inbound ports to 443 (HTTPS) and the monitoring port only.

**Authentication**

- Enable Azure AD / Entra ID SSO for all enterprise deployments.
- Enforce MFA for all administrative accounts.
- Configure session timeout after inactivity (recommended: 30 minutes).
- Monitor for brute-force indicators and account lockout events in audit logs.

### For Developers

Refer to [Secure Coding Standards](#secure-coding-standards) below. All contributions must pass the security checklist defined in [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Secure Coding Standards

### Input Validation

All user-facing inputs must be validated using Pydantic or Marshmallow schemas:

```python
from marshmallow import Schema, fields, validate

class NodeSchema(Schema):
    label = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    node_type = fields.Str(
        required=True,
        validate=validate.OneOf(['knowledge', 'sector', 'regulatory'])
    )
```

### SQL Injection Prevention

Always use parameterized queries. Direct string interpolation into SQL is prohibited and will be rejected in code review:

```python
from sqlalchemy import text

# Correct — parameterized query
query = text("SELECT * FROM nodes WHERE id = :node_id AND tenant_id = :tenant_id")
result = db.session.execute(query, {"node_id": node_id, "tenant_id": tenant_id})

# Prohibited — never do this
query = f"SELECT * FROM nodes WHERE id = {node_id}"  # VULNERABLE TO SQL INJECTION
```

### XSS Prevention

React's JSX automatically escapes values. Do not use `dangerouslySetInnerHTML` with unsanitized user input:

```tsx
// Correct — React escapes user input automatically
<div>{userInput}</div>

// Prohibited — XSS vector
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### Route Authentication and Authorization

All API routes must be protected with the appropriate permission decorator:

```python
from backend.security import require_permission, Permission

@app.route('/api/nodes')
@require_permission(Permission.KNOWLEDGE_READ)
def list_nodes():
    """List knowledge graph nodes for the authenticated tenant."""
    ...
```

### Dependency Security

```bash
# Python dependency vulnerability check
pip install pip-audit
pip-audit

# Node.js dependency vulnerability check
npm audit
npm audit fix
```

### Code Review Security Checklist

Before approving any PR, reviewers must verify:

- [ ] No hardcoded secrets, credentials, or API keys
- [ ] Input validation applied on all user-facing parameters
- [ ] Authentication and authorization enforced on all new routes
- [ ] No direct SQL string interpolation
- [ ] No use of `dangerouslySetInnerHTML` with unsanitized data
- [ ] Tenant isolation (`tenant_id` filtering) maintained in all queries
- [ ] Secure session management — no session token leakage
- [ ] Error handling does not expose stack traces or sensitive data to clients
- [ ] HTTPS enforced; no HTTP fallback
- [ ] Security headers present

---

## Security Testing

### Automated Security Tests

```bash
# Run dedicated security test suite
python -m pytest tests/security/ -v

# Knowledge Algorithm bulk verification (117 KAs)
python -m pytest backend/tests/test_ka_bulk.py -v

# API fuzz testing (enterprise hardening)
python -m pytest backend/tests/test_fuzzing.py -v

# API gateway coverage tests
python -m pytest backend/tests/test_gateway_api_coverage.py -v

# Static analysis — Python (Bandit)
bandit -r backend/ core/ -ll

# Dependency vulnerability scan — Python
pip-audit

# Dependency vulnerability scan — Node.js
npm audit
```

### CI-Enforced Security Gates

The following security checks run automatically on every PR and must pass before merge:

| Check | Tool | Workflow |
|-------|------|----------|
| Static code analysis | Bandit | `.github/workflows/security.yml` |
| Python dependency scan | pip-audit | `.github/workflows/ci.yml` |
| Node.js dependency scan | npm audit | `.github/workflows/ci.yml` |
| CodeQL SAST | GitHub CodeQL | `.github/workflows/security.yml` |
| OWASP dependency check | OWASP DC | `.github/workflows/security.yml` |
| Artifact signing | Sigstore | `.github/workflows/release-installer-signing.yml` |

### Pre-Deployment Manual Verification

Before any production deployment, verify:

1. All API endpoints require appropriate authentication.
2. Authorization checks correctly enforce permission boundaries.
3. Input validation blocks injection payloads.
4. Error responses do not expose stack traces, internal paths, or sensitive data.
5. HTTPS is enforced end-to-end.
6. Security headers are present and correctly configured.
7. MFA is functional for administrative accounts.

---

## Compliance and Regulatory Alignment

DataLogicEngine implements controls aligned with the following frameworks:

| Standard | Alignment |
|----------|-----------|
| **SOC 2 Type II** | Audit logging, access controls, availability monitoring |
| **GDPR** | Data subject rights, encryption at rest and in transit, audit trail |
| **HIPAA** | Configurable — enable via `HIPAA_MODE=true` in `.env` |
| **ISO 27001** | Information security management controls |
| **EU AI Act** | Immutable audit trail, explainability controls, bias detection (KA-010) |

For compliance reporting, see [`docs/SECURITY.md`](docs/SECURITY.md) and the compliance route handlers in `routes/compliance_routes.py`.

---

## Incident Response

In the event of a confirmed security incident:

### Immediate Actions (0–1 hours)

1. **Isolate** affected systems from production traffic.
2. **Preserve** logs, memory dumps, and forensic evidence before remediation.
3. **Notify** the security team at [security@datalogicengine.com](mailto:security@datalogicengine.com).

### Assessment Phase (1–24 hours)

4. **Assess** the scope, affected accounts, and data exposure.
5. **Contain** lateral movement by revoking compromised credentials and tokens.
6. **Audit** hash-chained audit log for indicators of compromise.

### Remediation Phase

7. **Remediate** the root vulnerability.
8. **Restore** services from verified clean backups if necessary.
9. **Verify** remediation through security testing.

### Post-Incident

10. **Document** a full incident report.
11. **Conduct** a post-mortem review within 5 business days.
12. **Update** detection rules, monitoring, and runbooks based on findings.

For detailed procedures, see [`docs/OPERATIONAL_RUNBOOKS.md`](docs/OPERATIONAL_RUNBOOKS.md).

---

## Security Update SLAs

| Severity | Response SLA | Patch Release SLA |
|----------|-------------|-------------------|
| **Critical (CVSS 9.0–10.0)** | 24 hours | 48 hours |
| **High (CVSS 7.0–8.9)** | 48 hours | 7 days |
| **Medium (CVSS 4.0–6.9)** | 7 days | 30 days |
| **Low (CVSS 0.1–3.9)** | 30 days | Next regular release |

Subscribe to security advisories by watching this repository and enabling **Security alerts** in your GitHub notification settings.

---

## Additional Resources

| Resource | URL |
|----------|-----|
| OWASP Top 10 | [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/) |
| CWE Top 25 | [https://cwe.mitre.org/top25/](https://cwe.mitre.org/top25/) |
| NIST Cybersecurity Framework | [https://www.nist.gov/cyberframework](https://www.nist.gov/cyberframework) |
| Microsoft Secure Development Lifecycle | [https://www.microsoft.com/en-us/securityengineering/sdl](https://www.microsoft.com/en-us/securityengineering/sdl) |
| Flask Security Best Practices | [https://flask.palletsprojects.com/en/latest/security/](https://flask.palletsprojects.com/en/latest/security/) |

---

## Security Recognition

We recognize and thank the security researchers who have responsibly disclosed vulnerabilities in DataLogicEngine. Researchers are listed here with their permission.

*No external disclosures on record at this time.*

---

## Contact

| Purpose | Contact |
|---------|---------|
| Vulnerability reports | [security@datalogicengine.com](mailto:security@datalogicengine.com) |
| General security questions | [security@datalogicengine.com](mailto:security@datalogicengine.com) |
| Code of conduct violations | [conduct@datalogicengine.com](mailto:conduct@datalogicengine.com) |

---

*This document is reviewed every 30 days. Last reviewed: March 2026.*
