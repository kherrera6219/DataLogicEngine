# Security Testing Guide

**Automated Security Scanning for DataLogicEngine**

This guide covers automated security testing using Bandit and Safety to identify vulnerabilities before they reach production.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Bandit - Code Security Scanner](#bandit---code-security-scanner)
- [Safety - Dependency Scanner](#safety---dependency-scanner)
- [CI/CD Integration](#cicd-integration)
- [Interpreting Results](#interpreting-results)
- [Fixing Common Issues](#fixing-common-issues)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Security Testing Tools

**Bandit**: Static analysis tool for Python code
- Detects common security issues (SQL injection, hardcoded passwords, etc.)
- Configurable severity levels
- Fast scanning (~seconds for typical project)

**Safety**: Dependency vulnerability scanner
- Checks dependencies against CVE database
- Identifies known security vulnerabilities
- Real-time database updates

### What We Scan For

- 🔍 Hardcoded credentials
- 🔍 SQL injection vulnerabilities
- 🔍 Command injection risks
- 🔍 Unsafe deserialization
- 🔍 Weak cryptography
- 🔍 Known CVEs in dependencies
- 🔍 Insecure random number generation
- 🔍 Path traversal vulnerabilities

---

## Installation

### Install Security Tools

```bash
# Install security testing dependencies
pip install bandit==1.7.5 safety==2.3.5

# Or install all Phase 1 requirements
pip install -r requirements-phase1.txt
```

### Verify Installation

```bash
# Check Bandit
bandit --version
# Output: bandit 1.7.5

# Check Safety
safety --version
# Output: safety, version 2.3.5
```

---

## Quick Start

### Run All Security Scans

```bash
# Development mode (informational)
python run_security_scan.py

# CI mode (fail on issues)
python run_security_scan.py --ci
```

### Run Individual Scans

```bash
# Only run Bandit
python run_security_scan.py --bandit

# Only run Safety
python run_security_scan.py --safety
```

### Check Reports

```bash
# View summary
cat security-reports/scan-summary.json

# View Bandit report
cat security-reports/bandit-report.json

# View Safety report (if vulnerabilities found)
cat security-reports/safety-report.json
```

---

## Bandit - Code Security Scanner

### What Bandit Checks

Bandit scans Python code for over 100 security issues including:

#### High Severity
- **B201**: Flask app with debug=True
- **B301**: Pickle usage (unsafe deserialization)
- **B303**: MD5/SHA1 usage for cryptography
- **B304**: Insecure ciphers
- **B305**: Insecure modes
- **B306**: Unsafe shell usage
- **B307**: eval() usage
- **B308**: mark_safe() in templates
- **B309**: HTTPSConnection without cert validation
- **B310**: urllib with GET parameters
- **B311**: Random instead of secrets module
- **B312**: Telnet usage
- **B315**: XML vulnerabilities
- **B316**: XML vulnerabilities
- **B317**: XML vulnerabilities
- **B318**: XML vulnerabilities
- **B319**: XML vulnerabilities
- **B320**: XML vulnerabilities
- **B321**: FTP usage
- **B322**: Input() usage
- **B323**: Unverified SSL context
- **B324**: Insecure hash functions
- **B325**: Tempfile usage

#### Medium Severity
- **B101**: Assert usage (can be disabled with -O)
- **B102**: exec() usage
- **B103**: chmod with broad permissions
- **B104**: Hardcoded bind_all_interfaces
- **B105**: Hardcoded password strings
- **B106**: Hardcoded password arguments
- **B107**: Hardcoded password defaults
- **B108**: Insecure temp file
- **B110**: Try/except pass
- **B201**: Flask debug mode
- **B601**: Paramiko SSH calls
- **B602**: subprocess with shell=True
- **B603**: subprocess without shell=False
- **B604**: Any shell usage
- **B605**: Starting process with shell
- **B606**: Starting process without shell
- **B607**: Starting partial path

#### Low Severity
- **B108**: Hardcoded temp directory
- **B110**: Try/except pass
- **B112**: Try/except continue
- **B113**: Request without timeout
- **B201**: Flask debug
- **B501**: SSL context weak ciphers
- **B502**: SSL bad defaults
- **B503**: SSL bad version
- **B504**: SSL cert verification
- **B505**: Weak cryptographic key
- **B506**: yaml.load()
- **B507**: SSH no host key verification
- **B508**: SNMPv3 insecure protocols
- **B509**: SNMPv3 no encryption

### Running Bandit Manually

```bash
# Basic scan (current directory)
bandit -r .

# Scan with severity filter (only HIGH)
bandit -r . -ll

# Generate JSON report
bandit -r . -f json -o bandit-report.json

# Scan specific directory
bandit -r backend/

# Exclude directories
bandit -r . -x ./tests,./migrations

# Show detailed issue information
bandit -r . -ll -i
```

### Configuration

Bandit is configured via `.bandit` file:

```ini
[bandit]
recursive = true
exclude_dirs = ['/tests', '/migrations', '/.git']
skips = []  # Test IDs to skip
```

### Example Output

```
Test results:
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'admin123'
   Severity: Medium   Confidence: Medium
   Location: config.py:15
   More Info: https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html
15      DEFAULT_PASSWORD = 'admin123'  # BAD - hardcoded!

>> Issue: [B201:flask_debug_true] A Flask app appears to be run with debug=True
   Severity: High   Confidence: Medium
   Location: main.py:23
   More Info: https://bandit.readthedocs.io/en/latest/plugins/b201_flask_debug_true.html
23      app.run(debug=True)  # BAD - should be environment-based!
```

---

## Safety - Dependency Scanner

### What Safety Checks

Safety checks all installed dependencies against:

- **CVE Database**: Common Vulnerabilities and Exposures
- **Python Security Advisories**: Known security issues
- **GitHub Advisory Database**: Recent disclosures

### Running Safety Manually

```bash
# Check installed packages
safety check

# Check against requirements file
safety check --file requirements.txt

# Generate JSON report
safety check --json --output safety-report.json

# Check specific package
pip show <package-name>
# Then search: https://pyup.io/<package-name>

# Update Safety database
safety --update
```

### Example Output

```
+==============================================================================+
|                                                                              |
|                               /$$$$$$            /$$                         |
|                              /$$__  $$          | $$                         |
|           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$           |
|          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$           |
|         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$           |
|          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$           |
|          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$           |
|         |_______/  \_______/|__/     \_______/   \___/   \____  $$           |
|                                                          /$$  | $$           |
|                                                         |  $$$$$$/           |
|  by pyup.io                                              \______/            |
|                                                                              |
+==============================================================================+
| REPORT                                                                       |
+==============================================================================+
| Checked 65 packages, found 2 vulnerabilities.                               |
+==============================================================================+
| -> Vulnerability found in cryptography version 3.3.1                        |
|    CVE-2020-36242                                                           |
|    In the cryptography package before 3.3.2, certain sequences of update    |
|    calls to symmetrically encrypt multi-GB values could result in an        |
|    integer overflow and buffer overflow, as demonstrated by the Fernet      |
|    class.                                                                    |
|    Recommendation: Update to 3.3.2 or higher.                               |
+==============================================================================+
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run weekly on Mondays at 9am
    - cron: '0 9 * * 1'

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-phase1.txt

    - name: Run Security Scans
      run: |
        python run_security_scan.py --ci

    - name: Upload Security Reports
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: security-reports/
```

### GitLab CI

```yaml
# .gitlab-ci.yml
security_scan:
  stage: test
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-phase1.txt
    - python run_security_scan.py --ci
  artifacts:
    when: always
    paths:
      - security-reports/
    reports:
      junit: security-reports/scan-summary.json
  only:
    - main
    - develop
    - merge_requests
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running security scans..."
python run_security_scan.py --ci

if [ $? -ne 0 ]; then
    echo "❌ Security scan failed! Fix issues before committing."
    exit 1
fi

echo "✅ Security scan passed!"
exit 0
```

```bash
# Make executable
chmod +x .git/hooks/pre-commit
```

---

## Interpreting Results

### Bandit Results

#### Severity Levels

- **HIGH**: Critical security issue, fix immediately
  - Example: Hardcoded credentials, debug mode in production
  - Action: Fix before merging

- **MEDIUM**: Potential security issue, review carefully
  - Example: subprocess with shell=True, assert usage
  - Action: Review and fix or document why it's safe

- **LOW**: Minor security concern, informational
  - Example: Hardcoded temp directory
  - Action: Review, fix if easy

#### Confidence Levels

- **HIGH**: Very likely a security issue
- **MEDIUM**: Probably a security issue, review context
- **LOW**: May or may not be an issue, check manually

#### Response Matrix

| Severity | Confidence | Action |
|----------|-----------|--------|
| HIGH | HIGH | Fix immediately |
| HIGH | MEDIUM | Fix before merge |
| HIGH | LOW | Review and fix |
| MEDIUM | HIGH | Fix before merge |
| MEDIUM | MEDIUM | Review carefully |
| MEDIUM | LOW | Informational |
| LOW | ANY | Informational |

### Safety Results

#### Vulnerability Assessment

Each vulnerability includes:
- **Package**: Affected dependency
- **Installed version**: Current version
- **CVE ID**: Common Vulnerabilities and Exposures ID
- **Description**: What the vulnerability is
- **Recommendation**: How to fix (usually "Update to X.Y.Z")

#### Response Actions

1. **Critical CVE** (Score 9.0-10.0):
   - Update immediately
   - Test thoroughly
   - Deploy emergency patch

2. **High CVE** (Score 7.0-8.9):
   - Update within 7 days
   - Include in next release

3. **Medium CVE** (Score 4.0-6.9):
   - Update within 30 days
   - Schedule in upcoming sprint

4. **Low CVE** (Score 0.1-3.9):
   - Update when convenient
   - Include in quarterly updates

---

## Fixing Common Issues

### Issue: Hardcoded Password

**Bandit Report**:
```
B105: hardcoded_password_string
DEFAULT_PASSWORD = 'admin123'
```

**Fix**:
```python
# ❌ Bad
DEFAULT_PASSWORD = 'admin123'

# ✅ Good
import os
DEFAULT_PASSWORD = os.environ.get('DEFAULT_PASSWORD')
if not DEFAULT_PASSWORD:
    raise ValueError("DEFAULT_PASSWORD must be set!")
```

### Issue: Flask Debug Mode

**Bandit Report**:
```
B201: flask_debug_true
app.run(debug=True)
```

**Fix**:
```python
# ❌ Bad
app.run(debug=True)

# ✅ Good
debug_mode = os.environ.get('FLASK_ENV') == 'development'
app.run(debug=debug_mode)
```

### Issue: SQL Injection

**Bandit Report**:
```
B608: hardcoded_sql_expressions
cursor.execute("SELECT * FROM users WHERE id = " + user_id)
```

**Fix**:
```python
# ❌ Bad
cursor.execute("SELECT * FROM users WHERE id = " + user_id)

# ✅ Good (parameterized query)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ✅ Better (ORM)
user = User.query.get(user_id)
```

### Issue: Vulnerable Dependency

**Safety Report**:
```
cryptography==3.3.1
CVE-2020-36242: Integer overflow and buffer overflow
Recommendation: Update to 3.3.2 or higher
```

**Fix**:
```bash
# Update dependency
pip install --upgrade cryptography>=3.3.2

# Update requirements.txt
# Old: cryptography==3.3.1
# New: cryptography>=3.3.2
```

### Issue: Insecure Random

**Bandit Report**:
```
B311: Standard pseudo-random generators not suitable for security
import random
token = random.randint(1000, 9999)
```

**Fix**:
```python
# ❌ Bad
import random
token = random.randint(1000, 9999)

# ✅ Good
import secrets
token = secrets.randbelow(9000) + 1000

# ✅ Better
token = secrets.token_urlsafe(32)
```

---

## Best Practices

### 1. Run Scans Regularly

```bash
# Before every commit
python run_security_scan.py

# Weekly full scan
python run_security_scan.py --ci > weekly-scan.log

# After dependency updates
pip install --upgrade -r requirements.txt
python run_security_scan.py --safety
```

### 2. Automate in CI/CD

- Run on every push
- Run on pull requests
- Run on schedule (weekly)
- Fail builds on HIGH severity issues

### 3. Fix Issues Promptly

- HIGH severity: Fix immediately
- MEDIUM severity: Fix within sprint
- LOW severity: Fix when convenient
- Document exceptions

### 4. Keep Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update all packages (carefully!)
pip install --upgrade -r requirements.txt

# Run security scan after updates
python run_security_scan.py
```

### 5. Review and Whitelist

Some issues may be false positives or acceptable risks:

```ini
# .bandit config
[bandit]
skips = [
    'B104',  # hardcoded_bind_all_interfaces - acceptable in container
]
```

**Document why you skip**:
```python
# nosec B104: Binding to 0.0.0.0 is intentional in Docker container
app.run(host='0.0.0.0', port=8080)
```

---

## Troubleshooting

### Issue: Bandit Not Found

```bash
# Check installation
which bandit

# Install if missing
pip install bandit==1.7.5

# Verify
bandit --version
```

### Issue: Safety Connection Error

```bash
# Check internet connection
ping pyup.io

# Update Safety database
safety --update

# Use offline mode (if database cached)
safety check --offline
```

### Issue: Too Many False Positives

**Solution**: Configure Bandit exclusions

```ini
# .bandit
[bandit]
# Exclude test files
exclude_dirs = ['/tests']

# Skip specific checks
skips = ['B101']  # Skip assert_used in tests
```

### Issue: Slow Scans

**Solution**: Optimize scanning

```bash
# Scan specific directories only
bandit -r backend/ -r app.py

# Exclude large directories
bandit -r . -x ./node_modules,./venv
```

---

## Quick Reference

### Commands

```bash
# Run all scans (dev mode)
python run_security_scan.py

# Run all scans (CI mode - fail on issues)
python run_security_scan.py --ci

# Run only Bandit
python run_security_scan.py --bandit

# Run only Safety
python run_security_scan.py --safety

# Manual Bandit scan
bandit -r . -ll -i

# Manual Safety scan
safety check --json
```

### Reports Location

```
security-reports/
├── scan-summary.json      # Overall summary
├── bandit-report.json     # Bandit detailed results
└── safety-report.json     # Safety detailed results (if vulns found)
```

### Issue Severity

- **Bandit**: LOW, MEDIUM, HIGH
- **Safety**: CVE score 0.0-10.0
- **CI Mode**: Fails on HIGH or vulnerabilities

---

## Integration with Phase 1

Security scanning complements other Phase 1 security measures:

- ✅ **Password Security**: Detects weak crypto
- ✅ **Input Validation**: Detects SQL injection
- ✅ **HTML Sanitization**: Detects XSS risks
- ✅ **Security Headers**: Complements header validation
- ✅ **Request Limits**: Detects DoS vulnerabilities

**Next Steps**:
1. Install tools: `pip install -r requirements-phase1.txt`
2. Run initial scan: `python run_security_scan.py`
3. Fix HIGH severity issues
4. Integrate into CI/CD
5. Schedule weekly scans

---

**Security Scanning Complete! 🔒**

Automated security testing is now configured:
- ✅ Bandit: Python code security analysis
- ✅ Safety: Dependency vulnerability scanning
- ✅ Automated reports: JSON output for CI/CD
- ✅ CI mode: Fail builds on security issues

See [PHASE_1_STATUS.md](PHASE_1_STATUS.md) for overall progress.
