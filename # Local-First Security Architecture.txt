# Local-First Security Architecture Standard

**Applies To:**
- DataLogicEngine (UKG)
- TheFactory
- CyberGenDoc

---

# 1. Design Principle

The application must operate completely locally on Windows.

The application shall not require:

- User accounts
- Application usernames
- Application passwords
- Internet connectivity
- External authentication providers
- External key management systems
- External encryption services
- External databases
- External licensing systems

The Windows user account is the application identity.

---

# 2. Identity Model

Authentication is provided entirely by Windows.

## Application Startup Flow

1. User logs into Windows.
2. Application starts.
3. Application reads current Windows user identity.
4. Application loads local encrypted workspace.
5. Application operates normally.

### Requirements

- No additional login screens.
- No application username/password system.
- No password reset functionality.
- No credential database.
- No authentication API calls.
- No dependency on external identity providers.

---

# 3. Encryption Standard

## Master Key Protection

### Required Technology

- Windows DPAPI
- `DataProtectionScope.CurrentUser`

### Requirements

- Generate a random 256-bit master key.
- Protect the master key using DPAPI.
- Never store raw master keys on disk.
- Never hardcode encryption keys.
- Never store encryption keys in source code.
- Never store encryption keys in configuration files.

---

## Data Encryption

### Required Technology

- AES-256-GCM

### Requirements

- Use a unique nonce for every encryption operation.
- Store nonce and authentication tag with ciphertext.
- Never reuse nonce/key combinations.
- Never implement custom cryptography.
- All sensitive data must be encrypted before being written to disk.

---

# 4. Storage Locations

All application data shall be stored under:

```text
%LOCALAPPDATA%
```

## Examples

- Workspace data
- Project memory
- Knowledge graphs
- Vector databases
- Audit records
- Generated documents
- Application settings

### Requirements

- Sensitive data must be encrypted before storage.
- Temporary files containing sensitive data must be deleted after use.
- No sensitive data shall be stored in plaintext.

---

# 5. Audit Integrity

## Required Technology

- SHA-256
- SHA-512

### Requirements

- Hash generated artifacts.
- Hash generated reports.
- Hash exported packages.
- Store timestamps.
- Store integrity metadata.
- Verify integrity when loading critical artifacts.

---

# 6. Digital Signatures

## Required Technology

- ECDSA P-256

### Requirements

- Sign exported artifacts.
- Sign generated compliance reports.
- Sign audit bundles.
- Verify signatures before import.
- Protect signing keys using DPAPI.

---

# 7. Logging Requirements

## Never Log

- Encryption keys
- Authentication secrets
- API tokens
- Private keys
- Sensitive document contents
- User confidential information
- Protected workspace data

## Requirements

- Use structured logging.
- Log security events.
- Log encryption failures.
- Log signature verification failures.
- Log audit integrity failures.

---

# 8. DataLogicEngine (UKG)

## Requirements

- Encrypt project memory.
- Encrypt graph node payloads.
- Encrypt vector content.
- Encrypt workspace data.
- Encrypt knowledge storage.
- Support key version tracking.
- Support encrypted exports.

---

# 9. TheFactory

## Requirements

- Hash generated artifacts.
- Verify template integrity.
- Verify plugin integrity.
- Verify generated package integrity.
- Require user approval before executing generated code.
- Maintain audit records of generated outputs.

---

# 10. CyberGenDoc

## Requirements

- Encrypt compliance evidence.
- Encrypt generated reports.
- Encrypt generated policies.
- Encrypt audit packages.
- Encrypt customer artifacts.
- Maintain tamper-evident audit records.
- Verify integrity of imported evidence.

---

# 11. Required Security Rules

## Prohibited

- Hardcoded secrets
- Hardcoded encryption keys
- Custom encryption algorithms
- Plaintext storage of sensitive data
- Separate application login systems
- Storing user passwords
- Storing encryption keys in source control

## Mandatory

- Windows identity only
- DPAPI protected master keys
- AES-256-GCM encryption
- SHA-256/SHA-512 integrity validation
- ECDSA signatures
- Structured security logging
- Offline-first operation

---

# 12. Required Codex Review Checklist

Every review must verify:

## Identity

- [ ] Windows identity is used.
- [ ] No application login exists.
- [ ] No password database exists.

## Key Protection

- [ ] DPAPI CurrentUser protects master keys.
- [ ] No raw keys are stored.
- [ ] No keys are hardcoded.

## Encryption

- [ ] AES-256-GCM is used correctly.
- [ ] Unique nonces are generated.
- [ ] Sensitive data is encrypted before disk write.

## Integrity

- [ ] SHA-256 or SHA-512 hashes are generated.
- [ ] Integrity checks are verified during loading.

## Signatures

- [ ] ECDSA signatures are generated.
- [ ] ECDSA signatures are verified.

## Logging

- [ ] Logs do not expose secrets.
- [ ] Logs do not expose encryption keys.
- [ ] Logs contain security-relevant events.

## Application Architecture

- [ ] Application functions completely offline.
- [ ] No external authentication dependencies exist.
- [ ] No external encryption dependencies exist.
- [ ] No external key management dependencies exist.

---

# Compliance Statement

All applications shall operate as local-first Windows desktop applications using the authenticated Windows user as the sole identity source.

Security shall be enforced through:

- Windows DPAPI
- AES-256-GCM encryption
- SHA-256 / SHA-512 integrity validation
- ECDSA P-256 digital signatures

No separate application authentication system shall be implemented.
No internet connection shall be required for core functionality.
All sensitive data shall be encrypted at rest.