# Multi-Factor Authentication (MFA) Guide

**Time-Based One-Time Password (TOTP) Implementation for DataLogicEngine**

This guide covers implementing and using Multi-Factor Authentication (2FA) with TOTP support.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [MFA Setup Flow](#mfa-setup-flow)
- [API Endpoints](#api-endpoints)
- [Backup Codes](#backup-codes)
- [Authenticator Apps](#authenticator-apps)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

### What is MFA?

Multi-Factor Authentication (MFA), also known as Two-Factor Authentication (2FA), adds an extra layer of security by requiring two forms of verification:

1. **Something you know**: Password
2. **Something you have**: TOTP code from authenticator app

### Features

- ✅ **TOTP Support**: Time-Based One-Time Passwords (RFC 6238)
- ✅ **QR Code Generation**: Easy setup with authenticator apps
- ✅ **Backup Codes**: 10 recovery codes for emergencies
- ✅ **Multiple Authenticators**: Google Authenticator, Authy, Microsoft Authenticator, etc.
- ✅ **Secure Storage**: TOTP secrets never logged or exposed
- ✅ **Clock Drift Tolerance**: ±30 second window

### Standards Compliance

- **RFC 6238**: TOTP - Time-Based One-Time Password Algorithm
- **RFC 4226**: HOTP - HMAC-Based One-Time Password Algorithm
- **NIST 800-63B**: Digital Identity Guidelines

---

## Installation

### Dependencies

```bash
# Install MFA dependencies
pip install pyotp==2.9.0 qrcode[pil]==7.4.2

# Or install all Phase 1 requirements
pip install -r requirements-phase1.txt
```

### Verify Installation

```python
from backend.security.mfa import check_mfa_dependencies

is_ready, message = check_mfa_dependencies()
print(message)
# Output: "MFA dependencies installed and ready"
```

---

## Quick Start

### For Users

1. **Login** to your account
2. **Navigate** to security settings
3. **Enable MFA** and scan QR code with authenticator app
4. **Save backup codes** in a secure location
5. **Verify** setup by entering a code from your app
6. **Login** now requires password + MFA code

### For Developers

```python
# Import MFA functions
from backend.security.mfa import setup_mfa, verify_mfa_token

# Setup MFA for a user
data = setup_mfa('user@example.com')
print(f"QR Code: {data['qr_code']}")
print(f"Backup Codes: {data['backup_codes']}")

# Verify TOTP code
is_valid = verify_mfa_token(user.mfa_secret, '123456')
```

---

## MFA Setup Flow

### Step-by-Step Process

```
1. User initiates MFA setup
   POST /auth/mfa/setup

2. Backend generates:
   - TOTP secret
   - QR code
   - Backup codes

3. User scans QR code with authenticator app

4. User enters code from app
   POST /auth/mfa/verify-setup
   { "mfa_code": "123456" }

5. Backend verifies code and enables MFA

6. MFA is now active for login
```

### Implementation Example

#### Step 1: Initiate Setup

```javascript
// Frontend: Initiate MFA setup
const response = await fetch('/auth/mfa/setup', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();

// Display QR code
document.getElementById('qr-code').innerHTML =
  `<img src="data:image/png;base64,${data.qr_code}">`;

// Display manual entry key
document.getElementById('manual-key').textContent =
  data.manual_entry_key;

// Display backup codes (IMPORTANT: Show these only once!)
document.getElementById('backup-codes').innerHTML =
  data.backup_codes.map(code => `<li>${code}</li>`).join('');
```

#### Step 2: Verify Setup

```javascript
// User enters code from authenticator app
const verifyResponse = await fetch('/auth/mfa/verify-setup', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mfa_code: userEnteredCode
  })
});

if (verifyResponse.ok) {
  alert('MFA enabled successfully!');
}
```

#### Step 3: Login with MFA

```javascript
// Login with password
const loginResponse = await fetch('/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'john',
    password: 'SecurePass123!'
  })
});

const loginData = await loginResponse.json();

if (loginData.mfa_required) {
  // Prompt user for MFA code
  const mfaCode = prompt('Enter MFA code from your authenticator app:');

  // Retry login with MFA code
  const mfaLoginResponse = await fetch('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'john',
      password: 'SecurePass123!',
      mfa_code: mfaCode
    })
  });

  const mfaLoginData = await mfaLoginResponse.json();
  // Store access token
  localStorage.setItem('access_token', mfaLoginData.access_token);
}
```

---

## API Endpoints

### POST /auth/mfa/setup

**Initiate MFA setup for the current user.**

**Authentication**: Required (JWT)

**Request**: No body

**Response**:
```json
{
  "message": "MFA setup initiated...",
  "qr_code": "iVBORw0KGgoAAAANS...",  // Base64 PNG
  "manual_entry_key": "JBSWY3DPEHPK3PXP",
  "backup_codes": [
    "A1B2C3D4",
    "E5F6G7H8",
    "..."
  ]
}
```

**Usage**:
```bash
curl -X POST http://localhost:8080/auth/mfa/setup \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### POST /auth/mfa/verify-setup

**Verify MFA setup by checking a TOTP code.**

**Authentication**: Required (JWT)

**Request**:
```json
{
  "mfa_code": "123456"
}
```

**Response**:
```json
{
  "message": "MFA enabled successfully!",
  "backup_codes_count": 10
}
```

**Usage**:
```bash
curl -X POST http://localhost:8080/auth/mfa/verify-setup \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mfa_code": "123456"}'
```

---

### POST /auth/mfa/disable

**Disable MFA for the current user.**

**Authentication**: Required (JWT)

**Request**:
```json
{
  "password": "user_password",
  "mfa_code": "123456"
}
```

**Response**:
```json
{
  "message": "MFA disabled successfully"
}
```

**Usage**:
```bash
curl -X POST http://localhost:8080/auth/mfa/disable \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type": application/json" \
  -d '{"password": "SecurePass123!", "mfa_code": "123456"}'
```

---

### POST /auth/mfa/regenerate-backup-codes

**Generate new backup codes (invalidates old ones).**

**Authentication**: Required (JWT)

**Request**:
```json
{
  "mfa_code": "123456"
}
```

**Response**:
```json
{
  "message": "New backup codes generated...",
  "backup_codes": [
    "X1Y2Z3A4",
    "B5C6D7E8",
    "..."
  ]
}
```

**Usage**:
```bash
curl -X POST http://localhost:8080/auth/mfa/regenerate-backup-codes \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mfa_code": "123456"}'
```

---

### GET /auth/mfa/status

**Get MFA status for the current user.**

**Authentication**: Required (JWT)

**Request**: No body

**Response**:
```json
{
  "mfa_enabled": true,
  "backup_codes_remaining": 8
}
```

**Usage**:
```bash
curl -X GET http://localhost:8080/auth/mfa/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### POST /auth/login (with MFA)

**Login with MFA enabled.**

**Authentication**: None (public endpoint)

**Request**:
```json
{
  "username": "john",
  "password": "SecurePass123!",
  "mfa_code": "123456"  // Required if MFA enabled
}
```

**Response (MFA required but not provided)**:
```json
{
  "error": "MFA code required",
  "mfa_required": true,
  "user_id": 1
}
```

**Response (Success)**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "john",
    "mfa_enabled": true
  }
}
```

---

## Backup Codes

### What are Backup Codes?

Backup codes are one-time use recovery codes for when you:
- Lose your phone
- Can't access your authenticator app
- Need emergency access

### Characteristics

- **Count**: 10 codes by default
- **Length**: 8 characters (uppercase hex)
- **Format**: A1B2C3D4, E5F6G7H8, etc.
- **Storage**: Hashed with SHA-256
- **One-time use**: Each code can only be used once

### Using Backup Codes

```javascript
// Login with backup code (same as MFA code field)
await fetch('/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'john',
    password: 'SecurePass123!',
    mfa_code: 'A1B2C3D4'  // Use backup code instead of TOTP
  })
});
```

### Best Practices

1. **Print them**: Print and store in a safe place
2. **Don't share**: Never share backup codes
3. **Monitor usage**: Check remaining codes regularly
4. **Regenerate**: Create new ones when running low (≤ 3)
5. **Secure storage**: Use password manager or encrypted file

### Regenerating Backup Codes

```python
# Backend: Regenerate backup codes
from backend.security.mfa import generate_backup_codes

plaintext_codes, hashed_codes = generate_backup_codes()

# Update user
user.mfa_backup_codes = hashed_codes
db.session.commit()

# Show plaintext codes to user (ONCE!)
return jsonify({'backup_codes': plaintext_codes})
```

---

## Authenticator Apps

### Supported Apps

MFA works with any TOTP-compatible authenticator app:

#### Google Authenticator
- **iOS**: [App Store](https://apps.apple.com/app/google-authenticator/id388497605)
- **Android**: [Play Store](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)

#### Microsoft Authenticator
- **iOS**: [App Store](https://apps.apple.com/app/microsoft-authenticator/id983156458)
- **Android**: [Play Store](https://play.google.com/store/apps/details?id=com.azure.authenticator)

#### Authy
- **iOS**: [App Store](https://apps.apple.com/app/authy/id494168017)
- **Android**: [Play Store](https://play.google.com/store/apps/details?id=com.authy.authy)
- **Desktop**: [authy.com](https://authy.com/download/)

#### 1Password
- Built-in TOTP support
- [1password.com](https://1password.com/)

#### Bitwarden
- Built-in TOTP support (premium)
- [bitwarden.com](https://bitwarden.com/)

### Setup Instructions

1. **Install** authenticator app on your phone
2. **Open** the app
3. **Tap** "Add account" or "+" button
4. **Scan** the QR code displayed in DataLogicEngine
5. **Enter** the 6-digit code to verify

### Manual Entry

If you can't scan the QR code:

1. Tap **"Enter key manually"** in authenticator app
2. Enter account name: **DataLogicEngine**
3. Enter the secret key: **JBSWY3DPEHPK3PXP** (example)
4. Time-based: **Yes**
5. Save and use the 6-digit code

---

## Security Considerations

### Secret Storage

- **Never log**: TOTP secrets must never appear in logs
- **Encrypted storage**: Secrets stored encrypted in database
- **No exposure**: Secrets never sent to client after setup

### TOTP Parameters

- **Algorithm**: SHA-1 (TOTP standard)
- **Digits**: 6
- **Interval**: 30 seconds
- **Window**: ±30 seconds (for clock drift)

### Brute Force Protection

MFA is protected by existing account lockout:
- 5 failed attempts = 30 minute lock
- Applies to incorrect MFA codes
- Backup codes count toward failed attempts

### Recovery

If user loses access:
1. **Try backup codes** first
2. **Account recovery** via email (if implemented)
3. **Admin reset** as last resort

### Backup Code Security

- **Hashed**: SHA-256 hashing prevents exposure
- **One-time**: Used codes are removed
- **Regeneration**: User can generate new codes anytime

---

## Troubleshooting

### Issue: "Invalid MFA code"

**Causes**:
- Wrong code entered
- Clock drift between server and device
- Code expired (30-second window)

**Solutions**:
1. Wait for new code to generate
2. Check device time is correct
3. Try backup code instead
4. Regenerate QR code and re-setup

### Issue: "Time out of sync"

**Problem**: Device clock is incorrect

**Solution**:
```
iPhone: Settings → General → Date & Time → Set Automatically
Android: Settings → System → Date & Time → Automatic date & time
```

### Issue: "Can't scan QR code"

**Solutions**:
1. Use manual entry instead
2. Increase screen brightness
3. Try different camera angle
4. Use a different device/app

### Issue: "Lost phone/device"

**Solutions**:
1. Use backup codes
2. Account recovery via email
3. Contact administrator

### Issue: "Backup codes not working"

**Checks**:
- Backup code is correct (8 characters, uppercase)
- Code hasn't been used before
- MFA is actually enabled

---

## Best Practices

### For Users

1. **Save backup codes** immediately after setup
2. **Print and store** in safe physical location
3. **Use trusted apps** (Google Authenticator, Authy, etc.)
4. **Set device PIN/biometric** to protect authenticator app
5. **Regenerate codes** when running low (≤ 3)
6. **Test backup codes** before you need them
7. **Keep device time synced** automatically

### For Developers

1. **Never log secrets**: TOTP secrets are sensitive
2. **Hash backup codes**: Never store plaintext
3. **Show codes once**: Backup codes should only be shown during generation
4. **Clear setup data**: Remove temporary secrets if setup fails
5. **Rate limit**: Prevent brute force on MFA codes
6. **Audit logging**: Log MFA enable/disable events
7. **Recovery flow**: Implement secure account recovery

### For Administrators

1. **Enforce MFA**: Require for privileged accounts
2. **Monitor usage**: Track MFA adoption rate
3. **Provide support**: Have recovery process documented
4. **Educate users**: Provide clear setup instructions
5. **Test regularly**: Verify MFA works correctly

---

## Implementation Examples

### Complete MFA Setup Flow (Python)

```python
from backend.security.mfa import MFASetup, verify_mfa_token
from models import User, db

# Step 1: Initiate setup
user = User.query.get(user_id)
setup = MFASetup(user.email)
data = setup.initiate_setup()

# Store secret and backup codes
user.mfa_secret = data['secret']
user.mfa_backup_codes = setup.get_hashed_backup_codes()
db.session.commit()

# Show to user (ONCE!)
return {
    'qr_code': data['qr_code'],
    'manual_entry': data['manual_entry'],
    'backup_codes': data['backup_codes']
}

# Step 2: Verify setup
if setup.verify_setup(user_code):
    user.mfa_enabled = True
    db.session.commit()
    return {'message': 'MFA enabled!'}
```

### Complete Login Flow (Python)

```python
from backend.security.mfa import verify_mfa_token, verify_backup_code

# Check password first
if not user.check_password(password):
    return {'error': 'Invalid credentials'}, 401

# Check if MFA required
if user.mfa_enabled:
    mfa_code = request.json.get('mfa_code')

    if not mfa_code:
        return {'error': 'MFA required', 'mfa_required': True}, 403

    # Try TOTP first
    if verify_mfa_token(user.mfa_secret, mfa_code):
        pass  # Valid TOTP
    # Try backup code
    elif verify_backup_code(mfa_code, user.mfa_backup_codes)[0]:
        is_valid, used_hash = verify_backup_code(mfa_code, user.mfa_backup_codes)
        user.mfa_backup_codes.remove(used_hash)
        db.session.commit()
    else:
        return {'error': 'Invalid MFA code'}, 401

# Generate token
token = create_access_token(identity=user.id)
return {'access_token': token}
```

---

## Quick Reference

### Commands

```bash
# Install dependencies
pip install pyotp==2.9.0 qrcode[pil]==7.4.2

# Test MFA module
python backend/security/mfa.py
```

### API Endpoints

```
POST   /auth/mfa/setup                  # Start MFA setup
POST   /auth/mfa/verify-setup           # Verify and enable MFA
POST   /auth/mfa/disable                # Disable MFA
POST   /auth/mfa/regenerate-backup-codes  # New backup codes
GET    /auth/mfa/status                 # Check MFA status
POST   /auth/login                      # Login (with mfa_code)
```

### Python Functions

```python
from backend.security.mfa import (
    setup_mfa,                # Setup MFA for user
    verify_mfa_token,         # Verify TOTP code
    verify_backup_code,       # Verify backup code
    generate_backup_codes,    # Generate new backup codes
)
```

---

**MFA Implementation Complete! 🔒**

Your application now supports:
- ✅ TOTP-based Multi-Factor Authentication
- ✅ QR code enrollment
- ✅ Backup codes for recovery
- ✅ Support for popular authenticator apps
- ✅ Secure secret storage

See [PHASE_1_STATUS.md](PHASE_1_STATUS.md) for overall Phase 1 progress.
