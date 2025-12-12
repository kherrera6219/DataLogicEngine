# Zero Trust Architecture Implementation

**Last Updated:** 2025-12-12
**Security Model:** Zero Trust (Never Trust, Always Verify)
**Compliance:** NIST SP 800-207

---

## Table of Contents

1. [Overview](#overview)
2. [Zero Trust Principles](#zero-trust-principles)
3. [Architecture](#architecture)
4. [Trust Scoring System](#trust-scoring-system)
5. [Context-Aware Access Control](#context-aware-access-control)
6. [API Security](#api-security)
7. [Session Management](#session-management)
8. [Implementation Guide](#implementation-guide)
9. [Integration Examples](#integration-examples)
10. [Monitoring & Metrics](#monitoring--metrics)

---

## Overview

Zero Trust Architecture (ZTA) is a security framework that eliminates implicit trust and requires continuous verification of all users, devices, and transactions. Unlike traditional perimeter-based security, Zero Trust assumes **no entity is inherently trustworthy**, regardless of location.

### Key Features

- ✅ **Trust Scoring:** Dynamic 0-100 trust scores based on user, device, and context
- ✅ **Context-Aware Access:** Location, time, network, and behavioral analysis
- ✅ **Continuous Verification:** Every request is authenticated and authorized
- ✅ **Device Fingerprinting:** Unique device identification and tracking
- ✅ **Risk-Based Authentication:** Access decisions based on calculated risk
- ✅ **API Request Signing:** HMAC-SHA256 signatures prevent tampering
- ✅ **Session Validation:** Continuous session monitoring for anomalies
- ✅ **Least Privilege:** Minimum necessary access granted

---

## Zero Trust Principles

### 1. Never Trust, Always Verify

Every access request is fully authenticated, authorized, and encrypted **before** granting access.

```python
# Traditional approach (implicit trust)
if user.is_authenticated:
    grant_access()

# Zero Trust approach (continuous verification)
trust_score, risk_level = evaluate_access_request(user, device, resource)
if trust_score >= required_trust_level and risk_level <= acceptable_risk:
    grant_access()
```

### 2. Assume Breach

Design systems assuming attackers are already inside the network.

- No implicit trust for internal traffic
- All communication authenticated and encrypted
- Continuous monitoring for anomalies
- Micro-segmentation to limit lateral movement

### 3. Verify Explicitly

Always authenticate and authorize based on:
- **Identity:** User credentials, MFA
- **Device:** Trusted device, health status
- **Context:** Location, time, network
- **Behavior:** Historical patterns, anomaly detection

### 4. Least Privilege Access

Grant minimum necessary access:
- Just-in-time (JIT) access
- Just-enough-access (JEA)
- Time-limited permissions
- Continuous re-evaluation

### 5. Micro-Segmentation

Segment network and resources to contain breaches:
- Separate network zones
- API-level access control
- Service-to-service authentication
- Network policies enforcement

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                            │
│              (User + Device + Context)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Device Fingerprinting                          │
│  • User-Agent parsing  • IP address  • Screen resolution        │
│  • Timezone  • Language  • Device ID generation                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Trust Score Calculation                        │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │ User Trust  │Device Trust │Context Trust│  Auth Trust │     │
│  │   (0-30)    │   (0-25)    │   (0-25)    │   (0-20)    │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│                     Total Score: 0-100                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Risk Assessment                              │
│  • Resource sensitivity  • Action risk  • Context risk          │
│  • Risk Level: MINIMAL → LOW → MEDIUM → HIGH → CRITICAL        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Access Decision Engine                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐         │
│  │  IF trust_score >= required_trust                  │         │
│  │  AND risk_level <= acceptable_risk                 │         │
│  │  THEN grant_access()                               │         │
│  │  ELSE deny_access()                                │         │
│  └────────────────────────────────────────────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Continuous Monitoring                          │
│  • Session validation  • Anomaly detection                      │
│  • Behavior analysis  • Re-authentication triggers              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Trust Scoring System

### Score Calculation

**Total Trust Score = User Trust + Device Trust + Context Trust + Auth Trust**

| Component | Max Points | Factors |
|-----------|------------|---------|
| **User Trust** | 30 | Account age, security history, behavior consistency, identity verification |
| **Device Trust** | 25 | Device known status, device age, auth history, failure rate |
| **Context Trust** | 25 | Location, time of day, network type, business hours |
| **Auth Trust** | 20 | MFA verified, recent authentication, session freshness |

### Trust Levels

| Score Range | Trust Level | Access |
|-------------|-------------|--------|
| 80-100 | **VERIFIED** | Full access, critical operations |
| 60-79 | **HIGH** | Standard elevated access |
| 40-59 | **MEDIUM** | Standard access |
| 20-39 | **LOW** | Limited access |
| 0-19 | **UNTRUSTED** | Blocked |

### User Trust Scoring (0-30 points)

```python
Base Score: 15 points

Bonuses:
+ Account age > 1 year: +5 points
+ Account age > 90 days: +3 points
+ Account age > 30 days: +1 point
+ Consistent behavior: +5 points
+ Verified identity: +5 points

Penalties:
- Recent security incidents (30 days): -5 points each (max -15)
```

### Device Trust Scoring (0-25 points)

```python
Unknown Device: 5 points
Known Device: 10 points (base)

Bonuses for Known Devices:
+ Device age > 90 days: +5 points
+ Device age > 30 days: +3 points
+ Successful auths > 10: +3 points
+ No recent failures: +2 points

Penalties:
- Recent auth failures: -1 point each
```

### Context Trust Scoring (0-25 points)

```python
Base Score: 15 points

Bonuses:
+ Business hours (6 AM - 8 PM): +3 points
+ Corporate network: +5 points
+ VPN connection: +3 points
+ Known location: +4 points

Penalties:
- After hours access: -2 points
- Public network: -3 points
- Unknown location: -2 points
```

### Authentication Trust Scoring (0-20 points)

```python
Base Score: 5 points

Bonuses:
+ MFA verified: +10 points
+ Auth within 15 minutes: +5 points
+ Auth within 1 hour: +3 points

Penalties:
- Auth > 4 hours ago: -3 points
```

---

## Context-Aware Access Control

### Access Context

Every request is evaluated with complete context:

```python
@dataclass
class AccessContext:
    user_id: str                    # User identifier
    device: DeviceFingerprint       # Device information
    location: Dict                  # Geolocation (country, city)
    time_of_day: int               # Hour 0-23
    day_of_week: int               # 0=Monday, 6=Sunday
    network_type: str              # corporate, vpn, public
    mfa_verified: bool             # MFA status
    last_auth_time: datetime       # Last authentication
```

### Device Fingerprinting

```python
@dataclass
class DeviceFingerprint:
    device_id: str                 # SHA-256 hash of fingerprint
    user_agent: str                # Full User-Agent string
    ip_address: str                # Client IP
    os_family: str                 # Windows, macOS, Linux, iOS, Android
    browser_family: str            # Chrome, Firefox, Safari, Edge
    is_mobile: bool                # Mobile device flag
    is_tablet: bool                # Tablet device flag
    is_pc: bool                    # PC device flag
    screen_resolution: str         # Optional: "1920x1080"
    timezone: str                  # Optional: "America/New_York"
    language: str                  # Optional: "en-US"
```

**Device ID Generation:**

```python
fingerprint_string = f"{user_agent}:{ip_address}:{screen_resolution}:{timezone}"
device_id = SHA256(fingerprint_string)[:32]
```

### Risk Assessment

Risk level is determined by:

1. **Resource Sensitivity**
   - Admin endpoints: HIGH
   - Data/Export endpoints: MEDIUM
   - Read-only endpoints: LOW

2. **Action Type**
   - Delete/Destroy: 1.5x multiplier
   - Write/Update: 1.2x multiplier
   - Read: 1.0x multiplier

3. **Context Factors**
   - No MFA + Low Trust: Risk +1 level
   - Public Network: Risk +1 level
   - Unknown Location: Risk +1 level

### Access Decision Matrix

| Risk Level | Required Trust Level |
|------------|---------------------|
| **CRITICAL** | VERIFIED (80+) only |
| **HIGH** | HIGH (60+) or VERIFIED |
| **MEDIUM** | MEDIUM (40+) or higher |
| **LOW** | LOW (20+) or higher |
| **MINIMAL** | Not UNTRUSTED |

---

## API Security

### Request Signing (HMAC-SHA256)

All API requests must be signed to ensure:
- **Authenticity:** Request is from valid API key holder
- **Integrity:** Request hasn't been tampered with
- **Freshness:** Request is recent (not a replay)

#### Signing Process

```python
# 1. Create canonical string
canonical = f"{METHOD}\n{PATH}\n{TIMESTAMP}\n{BODY_HASH}"

# Example:
# POST
# /api/data/export
# 1702404123
# 5f4dcc3b5aa765d61d8327deb882cf99

# 2. Generate HMAC-SHA256 signature
signature = HMAC-SHA256(canonical, api_secret)
signature_base64 = Base64(signature)

# 3. Add headers to request
headers = {
    'X-API-Key': api_key_id,
    'X-API-Timestamp': timestamp,
    'X-API-Signature': signature_base64,
    'X-API-Nonce': random_nonce  # Optional, prevents replay
}
```

#### Verification Process

```python
# Server verifies:
1. Timestamp within 5 minutes (prevents replay)
2. Nonce not previously used (prevents replay)
3. Recreate canonical string from request
4. Generate expected signature
5. Constant-time comparison of signatures
6. Grant access only if signatures match
```

#### Example: Signing a Request

```python
from backend.security.api_security import get_request_signer

signer = get_request_signer()

# Sign request
headers = signer.sign_request(
    method='POST',
    path='/api/simulation/run',
    body='{"parameters": {...}}',
    api_key_id='key_123abc',
    api_secret='secret_xyz789'
)

# Make request with signed headers
response = requests.post(
    'https://api.example.com/api/simulation/run',
    json={"parameters": {...}},
    headers=headers
)
```

#### Example: Requiring Signed Requests

```python
from backend.security.api_security import require_signed_request

@app.route('/api/secure-endpoint', methods=['POST'])
@require_signed_request(lambda key_id: get_api_secret_from_db(key_id))
def secure_endpoint():
    # Request is verified and authenticated
    return jsonify({"status": "success"})
```

### Request Validation

```python
from backend.security.api_security import validate_json_schema

@app.route('/api/users', methods=['POST'])
@validate_json_schema(
    required_fields=['username', 'email', 'password'],
    optional_fields=['name', 'phone'],
    max_size_kb=100
)
def create_user():
    # Request is validated
    data = request.validated_data
    # Guaranteed to have username, email, password
    return jsonify({"status": "created"})
```

---

## Session Management

### Session Creation

```python
from backend.security.zero_trust import get_zero_trust_manager

zt = get_zero_trust_manager()

# Create device fingerprint
device = zt.create_device_fingerprint(
    user_agent=request.headers.get('User-Agent'),
    ip_address=request.remote_addr,
    additional_info={
        'screen_resolution': '1920x1080',
        'timezone': 'America/New_York',
        'language': 'en-US'
    }
)

# Create session
session_id = zt.create_session(
    user_id=user.id,
    device=device,
    context_info={
        'mfa_verified': True,
        'location': {'country': 'US', 'city': 'New York'}
    }
)
```

### Continuous Session Validation

```python
# On every request, validate session
context = AccessContext(
    user_id=user.id,
    device=device,
    mfa_verified=True,
    last_auth_time=datetime.utcnow() - timedelta(minutes=30)
)

is_valid, details = zt.validate_session(session_id, context)

if not is_valid:
    # Session invalid - force re-authentication
    return redirect('/login')
```

### Anomaly Detection

Sessions are automatically invalidated if:

- **Device mismatch:** Different device accessing same session
- **Impossible travel:** Location change too rapid
- **Session expired:** > 8 hours old
- **Behavior anomaly:** Unusual activity pattern

---

## Implementation Guide

### 1. Initialize Zero Trust Manager

```python
# In app.py
from backend.security.audit_logger import get_audit_logger
from backend.security.zero_trust import get_zero_trust_manager
from backend.security.rbac import get_rbac_manager

audit_logger = get_audit_logger()
rbac = get_rbac_manager(audit_logger=audit_logger)
zt = get_zero_trust_manager(audit_logger=audit_logger, rbac_manager=rbac)
```

### 2. Protect Routes with Zero Trust

```python
from flask import request
from backend.security.zero_trust import get_zero_trust_manager

@app.route('/api/admin/config', methods=['POST'])
@login_required
def admin_config():
    zt = get_zero_trust_manager()

    # Create device fingerprint
    device = zt.create_device_fingerprint(
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr
    )

    # Evaluate access
    access_granted, risk_level, details = zt.evaluate_access_request(
        user_id=current_user.id,
        device=device,
        resource='/api/admin/config',
        action='write',
        context_info={
            'mfa_verified': session.get('mfa_verified', False),
            'last_auth_time': session.get('auth_time'),
            'location': get_user_location(),
            'network_type': detect_network_type()
        }
    )

    if not access_granted:
        return jsonify({
            "error": "Access denied",
            "risk_level": risk_level.value,
            "details": details
        }), 403

    # Process request
    return jsonify({"status": "success"})
```

### 3. Implement API Request Signing

```python
from backend.security.api_security import require_signed_request

def get_api_secret(api_key_id):
    # Look up API key in database
    api_key = APIKey.query.filter_by(key_id=api_key_id).first()
    return api_key.secret if api_key else None

@app.route('/api/v1/data/export', methods=['POST'])
@require_signed_request(get_api_secret)
def export_data():
    # Request is authenticated via signature
    return jsonify({"data": [...]})
```

### 4. Monitor Trust Scores

```python
# Get user trust profile
trust_calc = zt.trust_calculator
profile = trust_calc.user_profiles.get(user_id)

# Update user profile after security incident
trust_calc.update_user_profile(user_id, {
    'security_incidents': [
        {
            'type': 'failed_login',
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
})
```

---

## Integration Examples

### Example 1: Login with Zero Trust

```python
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create device fingerprint
    zt = get_zero_trust_manager()
    device = zt.create_device_fingerprint(
        user_agent=request.headers.get('User-Agent'),
        ip_address=request.remote_addr
    )

    # Register device for user
    zt.trust_calculator.register_device(user.id, device)

    # Calculate initial trust score
    context = AccessContext(
        user_id=user.id,
        device=device,
        time_of_day=datetime.utcnow().hour,
        mfa_verified=False,  # Not yet
        last_auth_time=datetime.utcnow()
    )

    trust_score, breakdown = zt.trust_calculator.calculate_trust_score(context)

    # Require MFA for low trust
    if trust_score < 60:
        return jsonify({
            "status": "mfa_required",
            "trust_score": trust_score,
            "session_token": create_temp_token(user.id)
        }), 202

    # Create session
    session_id = zt.create_session(user.id, device, {
        'mfa_verified': False,
        'location': get_user_location()
    })

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "trust_score": trust_score
    })
```

### Example 2: Risk-Based Re-Authentication

```python
@app.route('/api/account/delete', methods=['POST'])
@login_required
def delete_account():
    zt = get_zero_trust_manager()
    device = zt.create_device_fingerprint(
        request.headers.get('User-Agent'),
        request.remote_addr
    )

    # High-risk operation
    access_granted, risk_level, details = zt.evaluate_access_request(
        user_id=current_user.id,
        device=device,
        resource='/api/account/delete',
        action='delete',  # High-risk action
        context_info={
            'mfa_verified': session.get('mfa_verified', False),
            'last_auth_time': session.get('auth_time')
        }
    )

    # Require re-authentication for high-risk operations
    if details.get('requires_reauth') or risk_level.value in ['HIGH', 'CRITICAL']:
        return jsonify({
            "error": "Re-authentication required for this operation",
            "required_auth_level": "mfa"
        }), 403

    if not access_granted:
        return jsonify({"error": "Access denied"}), 403

    # Proceed with deletion
    delete_user_account(current_user.id)
    return jsonify({"status": "deleted"})
```

---

## Monitoring & Metrics

### Key Metrics

```python
# Get Zero Trust metrics
zt = get_zero_trust_manager()
metrics = zt.get_session_metrics()

{
    "active_sessions": 42,
    "total_devices_registered": 156,
    "total_users_profiled": 89
}
```

### Trust Score Distribution

Monitor trust score distribution across users:

```sql
SELECT
    CASE
        WHEN trust_score >= 80 THEN 'VERIFIED'
        WHEN trust_score >= 60 THEN 'HIGH'
        WHEN trust_score >= 40 THEN 'MEDIUM'
        WHEN trust_score >= 20 THEN 'LOW'
        ELSE 'UNTRUSTED'
    END as trust_level,
    COUNT(*) as count
FROM access_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY trust_level;
```

### Access Denial Tracking

Track denied access requests:

```python
# From audit logs
denied_requests = audit_logger.query_events(
    event_type="zero_trust_access_decision",
    filters={"details.access_granted": False}
)

# Analyze denial reasons
for request in denied_requests:
    print(f"User: {request['user_id']}")
    print(f"Trust Score: {request['trust_score']}")
    print(f"Risk Level: {request['risk_level']}")
```

### Anomaly Alerts

Monitor for security anomalies:

```python
# Session hijacking attempts
hijack_attempts = audit_logger.query_events(
    event_type="session_hijack_detected"
)

# Impossible travel detections
impossible_travel = audit_logger.query_events(
    event_type="session_invalidated",
    filters={"details.reason": "anomaly_detected"}
)
```

---

## Best Practices

### 1. Progressive Trust Building

- ✅ Start with LOW trust for new users/devices
- ✅ Gradually increase trust with positive behavior
- ✅ Quickly decrease trust on security incidents
- ✅ Require MFA for trust scores < 60

### 2. Context Awareness

- ✅ Collect comprehensive context (location, time, network)
- ✅ Establish behavioral baselines
- ✅ Alert on deviations from normal patterns
- ✅ Use geolocation for impossible travel detection

### 3. Continuous Validation

- ✅ Validate sessions on every request
- ✅ Re-authenticate after 4 hours
- ✅ Force re-auth for high-risk operations
- ✅ Monitor for session anomalies

### 4. Least Privilege

- ✅ Grant minimum necessary access
- ✅ Time-limit elevated permissions
- ✅ Require justification for privilege escalation
- ✅ Audit all privileged access

### 5. Monitoring & Response

- ✅ Real-time monitoring of trust scores
- ✅ Alert on unusual patterns
- ✅ Automated response to threats
- ✅ Regular security reviews

---

## Compliance Mapping

| Framework | Control | Zero Trust Implementation |
|-----------|---------|--------------------------|
| **NIST 800-207** | Core ZTA Components | Full implementation |
| **SOC 2** | CC6.2 - Authorization | Context-aware access control |
| **ISO 27001** | A.9.4.2 - Secure Log-on | Device fingerprinting + MFA |
| **GDPR** | Article 32 - Security | Encryption + continuous monitoring |

---

## Support

For Zero Trust implementation questions:
- **Documentation:** See `ENTERPRISE_SECURITY.md` for general security
- **API Security:** See code examples in `backend/security/api_security.py`
- **Integration:** Contact engineering team

---

**Classification:** CONFIDENTIAL
**Last Reviewed:** 2025-12-12
