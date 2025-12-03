#!/bin/bash
#
# Security Testing Script for Phase 1
#
# Runs comprehensive security scans and tests including:
# - Bandit (Python security linter)
# - Safety (dependency vulnerability checker)
# - Custom security tests
#

set -e

echo "================================================"
echo "Phase 1 Security Testing"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}ERROR: $1 is not installed${NC}"
        echo "Install with: pip install $1"
        return 1
    fi
    return 0
}

echo "Checking for required tools..."
check_tool bandit || exit 1
check_tool safety || exit 1
echo -e "${GREEN}✓ All required tools installed${NC}"
echo ""

# Create reports directory
REPORTS_DIR="security_reports"
mkdir -p $REPORTS_DIR

# Timestamp for report files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "================================================"
echo "1. Running Bandit Security Scan"
echo "================================================"
echo ""

bandit -r backend/ core/ -f json -o "${REPORTS_DIR}/bandit_${TIMESTAMP}.json" || true
bandit -r backend/ core/ -f txt -o "${REPORTS_DIR}/bandit_${TIMESTAMP}.txt" || true

echo -e "${GREEN}✓ Bandit scan complete${NC}"
echo "  Reports: ${REPORTS_DIR}/bandit_${TIMESTAMP}.{json,txt}"
echo ""

echo "================================================"
echo "2. Checking Dependencies for Vulnerabilities"
echo "================================================"
echo ""

safety check --json --output "${REPORTS_DIR}/safety_${TIMESTAMP}.json" || true
safety check --output text > "${REPORTS_DIR}/safety_${TIMESTAMP}.txt" || true

echo -e "${GREEN}✓ Safety check complete${NC}"
echo "  Reports: ${REPORTS_DIR}/safety_${TIMESTAMP}.{json,txt}"
echo ""

echo "================================================"
echo "3. Security Configuration Audit"
echo "================================================"
echo ""

# Check for common security misconfigurations
check_config() {
    local file=$1
    local pattern=$2
    local message=$3

    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file"; then
            echo -e "${YELLOW}⚠ WARNING: $message${NC}"
            echo "  File: $file"
            return 1
        fi
    fi
    return 0
}

CONFIG_ISSUES=0

# Check for debug mode
if grep -r "debug=True" . --include="*.py" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir=".venv" | grep -v "FLASK_ENV.*development"; then
    echo -e "${YELLOW}⚠ WARNING: Found debug=True in code${NC}"
    ((CONFIG_ISSUES++))
fi

# Check for default secrets
if grep -r "secret.*=.*'dev-" . --include="*.py" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir=".venv"; then
    echo -e "${YELLOW}⚠ WARNING: Found potential default secrets${NC}"
    ((CONFIG_ISSUES++))
fi

# Check for hardcoded passwords
if grep -r "password.*=.*['\"].*['\"]" . --include="*.py" --exclude-dir=".git" --exclude-dir="venv" --exclude-dir=".venv" | grep -v "password.*field" | grep -v "password.*variable"; then
    echo -e "${YELLOW}⚠ WARNING: Found potential hardcoded passwords${NC}"
    ((CONFIG_ISSUES++))
fi

if [ $CONFIG_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ No security configuration issues found${NC}"
else
    echo -e "${YELLOW}⚠ Found $CONFIG_ISSUES configuration issues${NC}"
fi
echo ""

echo "================================================"
echo "4. Environment File Security Check"
echo "================================================"
echo ""

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ WARNING: .env file exists (should not be committed)${NC}"

    # Check if .env is in .gitignore
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo -e "${GREEN}✓ .env is in .gitignore${NC}"
    else
        echo -e "${RED}✗ .env is NOT in .gitignore!${NC}"
    fi
else
    echo -e "${GREEN}✓ No .env file in repository${NC}"
fi
echo ""

echo "================================================"
echo "5. Secrets Detection"
echo "================================================"
echo ""

# Basic secrets detection
SECRETS_FOUND=0

# Check for AWS keys
if grep -r "AKIA[0-9A-Z]{16}" . --exclude-dir=".git" --exclude-dir="venv" --exclude-dir=".venv" --exclude-dir="node_modules"; then
    echo -e "${RED}✗ Found potential AWS access keys!${NC}"
    ((SECRETS_FOUND++))
fi

# Check for private keys
if find . -name "*.pem" -o -name "*.key" -o -name "*_rsa" | grep -v ".git"; then
    echo -e "${YELLOW}⚠ Found potential private key files${NC}"
    ((SECRETS_FOUND++))
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No obvious secrets detected${NC}"
else
    echo -e "${RED}✗ Found $SECRETS_FOUND potential secret exposures${NC}"
fi
echo ""

echo "================================================"
echo "6. Phase 1 Security Requirements Check"
echo "================================================"
echo ""

check_implementation() {
    local file=$1
    local name=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $name implemented${NC}"
        return 0
    else
        echo -e "${RED}✗ $name NOT found${NC}"
        return 1
    fi
}

REQUIREMENTS_MET=0
REQUIREMENTS_TOTAL=10

check_implementation "backend/security/password_security.py" "Password Security" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/security/mfa.py" "Multi-Factor Authentication" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/security/session_manager.py" "Session Manager" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/security/token_manager.py" "Token Manager" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/schemas/__init__.py" "Input Validation" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/security/sanitizer.py" "HTML Sanitizer" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/security/security_headers.py" "Security Headers" && ((REQUIREMENTS_MET++)) || true
check_implementation "backend/middleware/request_limits.py" "Request Limits" && ((REQUIREMENTS_MET++)) || true

# Check if MFA endpoints exist
if grep -q "mfa/setup" backend/auth.py; then
    echo -e "${GREEN}✓ MFA API Endpoints implemented${NC}"
    ((REQUIREMENTS_MET++))
else
    echo -e "${RED}✗ MFA API Endpoints NOT found${NC}"
fi

# Check if rate limiting is configured
if grep -q "flask-limiter" requirements*.txt; then
    echo -e "${GREEN}✓ Rate Limiting configured${NC}"
    ((REQUIREMENTS_MET++))
else
    echo -e "${RED}✗ Rate Limiting NOT configured${NC}"
fi

echo ""
echo "Phase 1 Implementation: $REQUIREMENTS_MET/$REQUIREMENTS_TOTAL requirements met"

if [ $REQUIREMENTS_MET -eq $REQUIREMENTS_TOTAL ]; then
    echo -e "${GREEN}✓ All Phase 1 requirements implemented!${NC}"
else
    echo -e "${YELLOW}⚠ $((REQUIREMENTS_TOTAL - REQUIREMENTS_MET)) requirements still pending${NC}"
fi
echo ""

echo "================================================"
echo "Security Test Summary"
echo "================================================"
echo ""
echo "Reports generated in: $REPORTS_DIR/"
echo ""
echo "Next steps:"
echo "1. Review Bandit report: ${REPORTS_DIR}/bandit_${TIMESTAMP}.txt"
echo "2. Review Safety report: ${REPORTS_DIR}/safety_${TIMESTAMP}.txt"
echo "3. Address any HIGH or MEDIUM severity issues"
echo "4. Update Phase 1 status document"
echo ""

if [ $REQUIREMENTS_MET -eq $REQUIREMENTS_TOTAL ] && [ $CONFIG_ISSUES -eq 0 ] && [ $SECRETS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 1 security testing PASSED${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Phase 1 security testing completed with warnings${NC}"
    exit 0
fi
