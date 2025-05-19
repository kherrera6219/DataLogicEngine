
"""
UKG Security Module

This package provides security and compliance features for the UKG Enterprise Architecture.
"""

from backend.security.security_manager import SecurityManager
from backend.security.audit_logger import AuditLogger
from backend.security.compliance_manager import SOC2ComplianceManager

# Singleton instances
_security_manager = None
_audit_logger = None
_compliance_manager = None

def get_security_manager(config=None):
    """
    Get the singleton SecurityManager instance.
    
    Args:
        config: Optional configuration settings
        
    Returns:
        SecurityManager instance
    """
    global _security_manager
    
    if _security_manager is None:
        _security_manager = SecurityManager(config)
        
    return _security_manager

def get_audit_logger(config=None):
    """
    Get the singleton AuditLogger instance.
    
    Args:
        config: Optional configuration settings
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = AuditLogger(config)
        
    return _audit_logger

def get_compliance_manager(config=None):
    """
    Get the singleton SOC2ComplianceManager instance.
    
    Args:
        config: Optional configuration settings
        
    Returns:
        SOC2ComplianceManager instance
    """
    global _compliance_manager
    
    if _compliance_manager is None:
        _compliance_manager = SOC2ComplianceManager(config)
        
    return _compliance_manager
