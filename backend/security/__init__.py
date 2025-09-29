"""
UKG Security Module

This package provides security and compliance features for the UKG Enterprise Architecture.
"""

from backend.security.security_manager import SecurityManager
from backend.security.audit_logger import AuditLogger
from backend.security.compliance_manager import SOC2ComplianceManager
from backend.security.enterprise_security import apply_enterprise_security

# Singleton instances
_security_manager = None
_audit_logger = None
_compliance_manager = None


def get_security_manager(config=None):
    """Get the singleton SecurityManager instance."""
    global _security_manager

    if _security_manager is None:
        _security_manager = SecurityManager(config)

    return _security_manager


def get_audit_logger(config=None):
    """Get the singleton AuditLogger instance."""
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger(config)

    return _audit_logger


def get_compliance_manager(config=None):
    """Get the singleton SOC2ComplianceManager instance."""
    global _compliance_manager

    if _compliance_manager is None:
        _compliance_manager = SOC2ComplianceManager(config)

    return _compliance_manager


__all__ = [
    "apply_enterprise_security",
    "get_audit_logger",
    "get_compliance_manager",
    "get_security_manager",
]
