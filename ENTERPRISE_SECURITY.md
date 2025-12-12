# Enterprise Security Hardening Documentation

## Overview

This document describes the enterprise-grade security implementations added to DataLogicEngine to meet **SOC 2 Type 2** and **ISO 27001** compliance requirements.

**Last Updated:** 2025-12-12
**Security Level:** Enterprise
**Compliance Frameworks:** SOC 2 Type 2, ISO 27001, GDPR, CCPA, HIPAA

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Encryption & Key Management](#encryption--key-management)
3. [Access Control (RBAC)](#access-control-rbac)
4. [Data Classification](#data-classification)
5. [Security Monitoring](#security-monitoring)
6. [Compliance Management](#compliance-management)
7. [Vulnerability Management](#vulnerability-management)
8. [Incident Response](#incident-response)
9. [Configuration Guide](#configuration-guide)
10. [Audit & Logging](#audit--logging)

---

## Security Architecture

### Multi-Layered Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  • Input Validation  • Rate Limiting  • CORS  • CSP         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Layer                        │
│  • JWT Tokens  • MFA  • Session Management                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Authorization Layer                         │
│  • RBAC  • Permission Checks  • Resource Access Control     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Protection Layer                     │
│  • Field Encryption  • Data Classification  • PII Detection │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Layer                          │
│  • Security Events  • Threat Detection  • Audit Logging     │
└─────────────────────────────────────────────────────────────┘
```

### Security Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Encryption Manager | `backend/security/encryption_manager.py` | KEK/DEK encryption, key rotation |
| RBAC System | `backend/security/rbac.py` | Role-based access control |
| Data Classifier | `backend/security/data_classification.py` | PII detection, data labeling |
| Security Monitor | `backend/security/security_monitoring.py` | Threat detection, alerting |
| Compliance Manager | `backend/security/compliance_manager.py` | SOC 2, ISO 27001 compliance |
| Vulnerability Scanner | `backend/security/vulnerability_scanner.py` | Dependency scanning, SBOM |

---

## Encryption & Key Management

### KEK/DEK Pattern

We implement a **Key Encryption Key (KEK) / Data Encryption Key (DEK)** pattern for enterprise-grade encryption:

```python
from backend.security.encryption_manager import get_encryption_manager

# Get encryption manager instance
encryption = get_encryption_manager()

# Encrypt sensitive data
encrypted_ssn = encryption.encrypt(user_ssn, field_name="ssn")

# Decrypt when needed
decrypted_ssn = encryption.decrypt(encrypted_ssn, field_name="ssn")
```

### Key Features

- **Automatic Key Rotation:** DEK rotates every 90 days by default
- **Version Tracking:** Encrypted data includes version prefix for backward compatibility
- **Cloud KMS Ready:** Supports AWS KMS, Azure Key Vault, GCP KMS integration
- **Audit Logging:** All encryption operations logged

### Key Rotation

```python
# Check key status
status = encryption.get_key_status()
print(f"Days until rotation: {status['days_until_rotation']}")

# Force immediate rotation
result = encryption.force_rotation()
```

### Environment Variables

```bash
# Required: KEK secret (32+ character random string)
ENCRYPTION_KEK_SECRET=<your-secret-here>

# Generate with:
python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

### Data Storage

- **KEK Salt:** `data/security/keys/kek.salt`
- **DEK Registry:** `data/security/keys/dek_registry.json`
- **Encrypted Format:** `v{version}:{base64_encrypted_data}`

---

## Access Control (RBAC)

### Role Hierarchy

```
Super Admin (All Permissions)
    ├── Admin (Management Capabilities)
    ├── Security Officer (Security & Compliance)
    ├── Auditor (Read-Only Audit Access)
    ├── Data Scientist (Research & Simulation)
    ├── Developer (Development & API)
    ├── Analyst (Read & Analysis)
    ├── User (Basic Access)
    └── Guest (Minimal Access)
```

### Default Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **super_admin** | Full system access | All permissions |
| **admin** | Administrative access | User management, system config, data operations |
| **security_officer** | Security & compliance | Security admin, compliance, audit access |
| **auditor** | Read-only compliance | Audit logs, compliance reports, security status |
| **data_scientist** | Research access | UKG, simulations, MCP, data export |
| **developer** | Development access | API, UKG, simulations, MCP |
| **analyst** | Analysis access | Read access, simulation execution, exports |
| **user** | Standard user | Basic read access |
| **guest** | Minimal access | UKG read-only |

### Permission Categories

1. **User Management:** `user:read`, `user:write`, `user:delete`, `user:manage_roles`
2. **Knowledge Graph:** `ukg:read`, `ukg:write`, `ukg:delete`, `ukg:admin`
3. **Simulations:** `simulation:read`, `simulation:write`, `simulation:execute`, `simulation:delete`
4. **Security:** `security:read`, `security:write`, `security:admin`
5. **Compliance:** `compliance:read`, `compliance:write`, `compliance:admin`
6. **Audit:** `audit:read`, `audit:export`, `audit:delete`
7. **System:** `system:config:read`, `system:config:write`, `system:admin`
8. **Data:** `data:export`, `data:import`, `data:delete`, `data:backup`, `data:restore`
9. **API:** `api:key:create`, `api:key:revoke`, `api:rate_limit:exempt`

### Usage in Routes

```python
from backend.security.rbac import require_permission, Permission

@app.route('/admin/users')
@login_required
@require_permission(Permission.USER_WRITE)
def manage_users():
    # Only users with USER_WRITE permission can access
    return render_template('admin/users.html')

@app.route('/data/export')
@login_required
@require_any_permission(Permission.DATA_EXPORT, Permission.SYSTEM_ADMIN)
def export_data():
    # Users need either DATA_EXPORT or SYSTEM_ADMIN
    return jsonify({"data": "..."})
```

### Assigning Roles

```python
from backend.security.rbac import get_rbac_manager

rbac = get_rbac_manager()

# Assign role to user
rbac.assign_role_to_user(user, "data_scientist")

# Check permission
has_access = rbac.user_has_permission(user, Permission.UKG_WRITE)
```

---

## Data Classification

### Classification Levels

| Level | Description | Encryption | Audit | Retention |
|-------|-------------|------------|-------|-----------|
| **PUBLIC** | Public information | No | No | Unlimited |
| **INTERNAL** | Internal use only | No | No | 7 years |
| **CONFIDENTIAL** | Sensitive business data | Yes | Yes | 7 years |
| **RESTRICTED** | Highly sensitive (PII/PHI) | Yes | Yes | 7 years |

### PII Detection

Automatically detects:

- **Direct Identifiers:** SSN, Passport, Driver's License, National ID
- **Contact Info:** Email, Phone, Address
- **Financial:** Credit Card, Bank Account, Tax ID
- **Biometric:** Fingerprint, Facial Recognition
- **Health:** Medical Record, Health Insurance, Diagnosis
- **Personal:** Name, DOB, IP Address, Device ID, Geolocation

### Usage

```python
from backend.security.data_classification import get_data_classifier, DataClassification

classifier = get_data_classifier()

# Detect PII
pii_types = classifier.detect_pii("123-45-6789", field_name="ssn")
# Returns: [PIIType.SSN]

# Classify field
classification = classifier.classify_field("credit_card_number")
# Returns: DataClassification.RESTRICTED

# Classify entire dictionary
data = {"name": "John Doe", "email": "john@example.com", "age": 30}
classifications = classifier.classify_dict(data)

# Mask PII for display
masked = classifier.mask_pii("My SSN is 123-45-6789")
# Returns: "My SSN is ***-**-6789"
```

### Data Handling Requirements

```python
# Get handling requirements for classification level
label = classifier.get_data_label(DataClassification.RESTRICTED)

# Returns:
{
    "classification": "restricted",
    "requires_encryption": True,
    "requires_audit": True,
    "retention_days": 2555,
    "handling_instructions": [
        "Highly restricted access",
        "Encryption required at rest and in transit",
        "Comprehensive audit logging mandatory",
        ...
    ],
    "compliance_frameworks": ["SOC 2 Type 2", "ISO 27001", "GDPR", "CCPA", "HIPAA"]
}
```

---

## Security Monitoring

### Real-Time Threat Detection

The security monitor continuously analyzes events for:

1. **Brute Force Attacks:** 5+ failed logins in 5 minutes → Auto-block IP
2. **SQL Injection:** Pattern detection in inputs
3. **XSS Attempts:** Script tag detection
4. **Path Traversal:** Directory traversal patterns
5. **Data Exfiltration:** 10+ exports in 1 hour
6. **Privilege Escalation:** 5+ permission denials in 10 minutes
7. **Anomalous Behavior:** Unusual activity times, locations

### Threat Levels

- **INFO:** Informational events
- **LOW:** Minor suspicious activity
- **MEDIUM:** Moderate security concerns
- **HIGH:** Serious security incidents
- **CRITICAL:** Immediate action required

### Usage

```python
from backend.security.security_monitoring import get_security_monitor, SecurityEventType, ThreatLevel

monitor = get_security_monitor()

# Process security event
monitor.process_event(
    event_type=SecurityEventType.LOGIN_FAILURE,
    details={"username": "admin"},
    user_id="user123",
    ip_address="192.168.1.100"
)

# Get alerts
critical_alerts = monitor.get_alerts(
    threat_level=ThreatLevel.CRITICAL,
    unresolved_only=True
)

# Get metrics
metrics = monitor.get_metrics()
print(f"Total events: {metrics['total_events']}")
print(f"Critical alerts: {metrics['critical_alerts']}")

# Check if IP is blocked
if monitor.is_ip_blocked("192.168.1.100"):
    return jsonify({"error": "Access denied"}), 403
```

### Alert Handlers

Register custom alert handlers for notifications:

```python
def email_alert_handler(alert):
    if alert.threat_level == ThreatLevel.CRITICAL:
        send_email(
            to="security@company.com",
            subject=f"CRITICAL SECURITY ALERT: {alert.message}",
            body=json.dumps(alert.to_dict(), indent=2)
        )

def slack_alert_handler(alert):
    if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        post_to_slack(channel="#security", message=alert.message)

monitor = get_security_monitor(alert_handlers=[email_alert_handler, slack_alert_handler])
```

---

## Compliance Management

### Supported Frameworks

- ✅ SOC 2 Type 2
- ✅ ISO 27001
- ✅ GDPR
- ✅ CCPA
- ✅ HIPAA
- ✅ PCI DSS
- ✅ NIST CSF

### Control Implementation Status

```python
from backend.security.compliance_manager import get_compliance_manager, ComplianceFramework

compliance = get_compliance_manager()

# Get compliance status
status = compliance.get_compliance_status()
print(json.dumps(status, indent=2))

# Output:
{
    "frameworks": {
        "soc2_type2": {
            "total_controls": 7,
            "implemented": 6,
            "compliance_percentage": 85.71
        },
        "iso27001": {
            "total_controls": 8,
            "implemented": 8,
            "compliance_percentage": 100.0
        }
    }
}
```

### Automated Evidence Collection

Evidence is automatically collected for:

- Access control configurations
- Encryption settings and key rotation
- Audit log integrity
- Security monitoring status

```python
# Manually trigger evidence collection
compliance.collect_evidence_automated()
```

### Generate Compliance Reports

```python
from datetime import datetime, timedelta

# Generate SOC 2 report for last 365 days
report = compliance.generate_compliance_report(
    framework=ComplianceFramework.SOC2_TYPE2,
    period_start=datetime.utcnow() - timedelta(days=365),
    period_end=datetime.utcnow()
)

# Report includes:
# - Summary statistics
# - Control status
# - Evidence collected
# - Gap analysis
# - Compliance percentage
```

### Reports Location

- **Reports:** `data/compliance/reports/`
- **Evidence:** `data/compliance/evidence/`
- **Events:** `logs/compliance/events.jsonl`

---

## Vulnerability Management

### Dependency Scanning

```python
from backend.security.vulnerability_scanner import get_vulnerability_scanner

scanner = get_vulnerability_scanner()

# Scan Python dependencies
python_results = scanner.scan_python_dependencies()

# Scan NPM dependencies
npm_results = scanner.scan_npm_dependencies()

# Generate SBOM
sbom = scanner.generate_sbom()

# Run full security scan
results = scanner.run_full_security_scan()

print(f"Risk Level: {results['risk_level']}")
print(f"Critical Vulnerabilities: {results['python_scan']['summary']['critical']}")
```

### Automated Scanning

```bash
# Install pip-audit for Python scanning
pip install pip-audit

# Run manual scan
pip-audit --format json --desc

# For NPM
cd frontend
npm audit --json
```

### SBOM Generation

Software Bill of Materials (SBOM) is automatically generated and includes:

- All Python packages with versions
- All NPM packages with versions
- License information
- Integrity hash for verification

**Location:** `data/security/sbom/sbom_latest.json`

---

## Incident Response

### Incident Response Plan

1. **Detection:** Security monitoring detects threat
2. **Alert:** Alert created and handlers notified
3. **Assessment:** Security team evaluates severity
4. **Containment:** Isolate affected systems
5. **Eradication:** Remove threat
6. **Recovery:** Restore normal operations
7. **Post-Incident:** Review and update procedures

### Security Playbooks

#### Brute Force Attack
1. IP auto-blocked after 5 failed attempts
2. Security alert created (HIGH severity)
3. Account locked for 30 minutes
4. Security team notified
5. Review logs for additional suspicious IPs
6. Update firewall rules if needed

#### Data Exfiltration Attempt
1. Monitor detects unusual export volume
2. Alert created (HIGH severity)
3. User account suspended pending investigation
4. Review all recent exports
5. Check for unauthorized access
6. Audit data access logs
7. Notify compliance team

#### SQL Injection/XSS Attempt
1. Pattern detected in input
2. Request blocked immediately
3. Alert created (CRITICAL severity)
4. IP address logged and potentially blocked
5. Review application logs
6. Check for successful attacks
7. Update WAF rules

---

## Configuration Guide

### Environment Variables

Add to `.env`:

```bash
# Encryption
ENCRYPTION_KEK_SECRET=<64-char-secret>

# Security Monitoring
ENABLE_SECURITY_MONITORING=true
ALERT_EMAIL=security@company.com
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...

# IP Whitelisting (optional)
ADMIN_IP_WHITELIST=192.168.1.0/24,10.0.0.0/8

# Rate Limiting
RATE_LIMIT_STORAGE=redis://localhost:6379

# Compliance
COMPLIANCE_AUTO_COLLECT=true
COMPLIANCE_REPORT_SCHEDULE=daily
```

### Initialize Security Components

In `app.py`:

```python
from backend.security.audit_logger import get_audit_logger
from backend.security.encryption_manager import get_encryption_manager
from backend.security.rbac import get_rbac_manager
from backend.security.data_classification import get_data_classifier
from backend.security.security_monitoring import get_security_monitor
from backend.security.compliance_manager import get_compliance_manager

# Initialize in order
audit_logger = get_audit_logger()
encryption = get_encryption_manager(audit_logger=audit_logger)
rbac = get_rbac_manager(audit_logger=audit_logger)
classifier = get_data_classifier(audit_logger=audit_logger)
monitor = get_security_monitor(audit_logger=audit_logger)
compliance = get_compliance_manager(audit_logger=audit_logger)

# Start automated processes
monitor.start_monitoring()

# Scheduled tasks (use APScheduler or similar)
@scheduler.task('cron', hour=2)  # 2 AM daily
def daily_compliance_collection():
    compliance.collect_evidence_automated()

@scheduler.task('cron', day_of_week='mon', hour=3)  # Monday 3 AM
def weekly_vulnerability_scan():
    scanner = get_vulnerability_scanner(audit_logger=audit_logger)
    results = scanner.run_full_security_scan()

    if results['risk_level'] in ['CRITICAL', 'HIGH']:
        # Send alert to security team
        pass
```

### Database Migrations

Add role field to User model:

```python
class User(db.Model):
    # ... existing fields ...
    role = db.Column(db.String(50), default='user', nullable=False)

    # ... existing methods ...
```

Generate and run migration:

```bash
flask db migrate -m "Add role field to User model"
flask db upgrade
```

---

## Audit & Logging

### Log Locations

| Log Type | Location | Rotation |
|----------|----------|----------|
| Audit Logs | `logs/audit/audit_YYYYMMDD.jsonl` | Daily |
| Security Scans | `logs/security/scan_TIMESTAMP.json` | Per scan |
| Compliance Events | `logs/compliance/events.jsonl` | Append-only |
| Security Alerts | `data/security/alerts.jsonl` | Append-only |

### Log Retention

- **Audit Logs:** 7 years (compliance requirement)
- **Security Logs:** 2 years
- **Application Logs:** 90 days
- **Compliance Evidence:** 7 years

### Log Integrity

- All audit logs include SHA-256 hash
- Integrity verification available
- Tamper detection enabled

```python
from backend.security.audit_logger import get_audit_logger

logger = get_audit_logger()

# Verify log integrity
is_valid = logger.verify_log_integrity("logs/audit/audit_20251212.jsonl")
```

---

## Security Best Practices

### Development

1. ✅ Never commit secrets to Git
2. ✅ Use environment variables for configuration
3. ✅ Always validate and sanitize input
4. ✅ Use parameterized queries (prevent SQL injection)
5. ✅ Implement proper error handling
6. ✅ Keep dependencies updated
7. ✅ Run security scans before deployment
8. ✅ Use HTTPS in production
9. ✅ Enable HSTS headers
10. ✅ Implement CSP headers

### Production Deployment

1. ✅ Set `FLASK_ENV=production`
2. ✅ Use strong random secrets (64+ characters)
3. ✅ Enable Redis for rate limiting
4. ✅ Configure proper CORS origins
5. ✅ Set up SSL/TLS certificates
6. ✅ Enable database SSL connections
7. ✅ Configure firewall rules
8. ✅ Set up monitoring and alerting
9. ✅ Regular security audits
10. ✅ Implement backup and disaster recovery

### Monitoring Checklist

- [ ] Security alerts configured
- [ ] Log aggregation set up (SIEM integration)
- [ ] Automated vulnerability scanning scheduled
- [ ] Compliance evidence collection automated
- [ ] Incident response procedures documented
- [ ] Security metrics dashboard created
- [ ] Uptime monitoring enabled
- [ ] Performance monitoring configured

---

## Compliance Checklist

### SOC 2 Type 2

- [x] CC6.1 - Logical and Physical Access Controls
- [x] CC6.2 - Authentication and Authorization
- [x] CC6.3 - User Access Removal
- [x] CC6.6 - Encryption of Data
- [x] CC6.7 - Data Transmission Protection
- [x] CC7.2 - Security Monitoring
- [ ] CC8.1 - Change Management (Partially Implemented)

### ISO 27001

- [x] A.9.1.1 - Access Control Policy
- [x] A.9.2.1 - User Registration
- [x] A.9.4.1 - Information Access Restriction
- [x] A.10.1.1 - Cryptographic Controls Policy
- [x] A.10.1.2 - Key Management
- [x] A.12.4.1 - Event Logging
- [x] A.12.4.3 - Administrator Logs
- [x] A.18.1.1 - Compliance Requirements

### GDPR

- [x] Article 25 - Data Protection by Design
- [x] Article 32 - Security of Processing
- [ ] Article 33 - Data Breach Notification (Partially Implemented)
- [ ] Article 17 - Right to Erasure (Partially Implemented)

---

## Support & Contact

For security issues or questions:

- **Security Team:** security@datalogicengine.com
- **Compliance Team:** compliance@datalogicengine.com
- **Emergency:** Run incident response procedures

**Never discuss security vulnerabilities in public channels.**

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-12 | Initial enterprise security implementation |

---

**Classification:** CONFIDENTIAL
**Audience:** Internal Engineering & Security Teams Only
