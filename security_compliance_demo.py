
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) Security and Compliance Demo

This script demonstrates the SOC 2 Type 2 compliance and security capabilities
of the UKG enterprise architecture.
"""

import os
import sys
import logging
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('security_demo.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_folders():
    """Create necessary folders for the security demo."""
    folders = ['logs/security', 'logs/compliance', 'logs/audit', 'data/security']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created folder: {folder}")

def init_security_components():
    """Initialize the security components for the demo."""
    # Import the security components
    from backend.security import get_security_manager, get_audit_logger, get_compliance_manager
    
    # Initialize the components
    security_manager = get_security_manager()
    audit_logger = get_audit_logger()
    compliance_manager = get_compliance_manager()
    
    logger.info("Security components initialized")
    
    return security_manager, audit_logger, compliance_manager

def simulate_security_events(security_manager, audit_logger, compliance_manager):
    """Simulate security events for the demo."""
    try:
        logger.info("Simulating security events...")
        
        # Simulate user authentication
        logger.info("Simulating user authentication...")
        audit_logger.log_authentication(
            user_id="user123",
            status="success",
            ip_address="192.168.1.1",
            details={"auth_method": "password"}
        )
        
        # Simulate security scan
        logger.info("Simulating security scan...")
        security_manager._perform_security_scan()
        
        # Simulate data access
        logger.info("Simulating data access...")
        audit_logger.log_data_access(
            user_id="user123",
            resource_id="document456",
            action="read",
            details={"resource_type": "document", "classification": "confidential"}
        )
        
        # Simulate compliance check
        logger.info("Simulating compliance check...")
        compliance_manager._check_security_compliance()
        compliance_manager._check_confidentiality_compliance()
        compliance_manager._check_privacy_compliance()
        
        # Simulate failed authentication
        logger.info("Simulating failed authentication...")
        audit_logger.log_authentication(
            user_id="attacker",
            status="failure",
            ip_address="10.0.0.1",
            details={"auth_method": "password", "reason": "invalid_credentials"}
        )
        
        # Simulate encryption and decryption
        logger.info("Simulating encryption and decryption...")
        sensitive_data = "This is sensitive information that needs protection"
        encrypted = security_manager.encrypt_data(sensitive_data)
        decrypted = security_manager.decrypt_data(encrypted).decode()
        logger.info(f"Encryption test: {'success' if decrypted == sensitive_data else 'failure'}")
        
        # Simulate password hashing
        logger.info("Simulating password hashing...")
        password = "SecurePassword123!"
        hashed, salt = security_manager.hash_password(password)
        verified = security_manager.verify_password(password, hashed, salt)
        logger.info(f"Password verification test: {'success' if verified else 'failure'}")
        
        # Log compliance events
        logger.info("Logging compliance events...")
        compliance_manager.log_compliance_event(
            "security", 
            "check", 
            "Security controls verified during routine audit"
        )
        compliance_manager.log_compliance_event(
            "confidentiality", 
            "violation", 
            "Potential data exposure identified in log files"
        )
        compliance_manager.log_compliance_event(
            "security", 
            "remediation", 
            "Removed exposed credentials from configuration files"
        )
        
        # Generate compliance report
        logger.info("Generating compliance report...")
        report = compliance_manager.generate_compliance_report()
        logger.info(f"Compliance report generated with ID: {report['report_id']}")
        
        logger.info("Security event simulation completed")
        
    except Exception as e:
        logger.error(f"Error simulating security events: {str(e)}")

def display_security_status(security_manager, compliance_manager):
    """Display the current security and compliance status."""
    try:
        # Get security status
        security_status = security_manager.get_security_status()
        
        # Get compliance status
        compliance_status = compliance_manager.get_compliance_status()
        
        # Display status
        print("\n" + "="*80)
        print("UKG SOC 2 SECURITY AND COMPLIANCE STATUS")
        print("="*80 + "\n")
        
        print("SECURITY STATUS:")
        print(f"  Timestamp: {security_status['timestamp']}")
        print(f"  Encryption: {'Enabled' if security_status['encryption_enabled'] else 'Disabled'}")
        print(f"  Last Scan: {security_status['last_scan_time'] or 'Never'}")
        print(f"  Vulnerabilities: {security_status['vulnerabilities_count']}")
        print(f"  Warnings: {security_status['warnings_count']}")
        print(f"  Overall Status: {security_status['status'].upper()}")
        
        print("\nCOMPLIANCE STATUS:")
        print(f"  Timestamp: {compliance_status['timestamp']}")
        print(f"  Overall Status: {compliance_status['overall_status'].upper()}")
        
        for category, state in compliance_status['categories'].items():
            print(f"  {category.upper()}: {state['status'].upper()}")
            print(f"    Last Check: {state['last_check']}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Error displaying security status: {str(e)}")

def display_recent_events(audit_logger, compliance_manager):
    """Display recent audit and compliance events."""
    try:
        # Get recent audit events
        audit_events = audit_logger.get_audit_events(limit=5)
        
        # Get recent compliance events
        compliance_events = compliance_manager.get_compliance_events(limit=5)
        
        # Display events
        print("\nRECENT AUDIT EVENTS:")
        for event in audit_events:
            print(f"  [{event['timestamp']}] {event.get('event_type', 'unknown')}: {event.get('action', '')} - Status: {event.get('status', '')}")
        
        print("\nRECENT COMPLIANCE EVENTS:")
        for event in compliance_events:
            print(f"  [{event['timestamp']}] {event.get('category', 'unknown')}: {event.get('type', '')} - {event.get('details', '')}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Error displaying recent events: {str(e)}")

def run_demo():
    """Run the security and compliance demo."""
    try:
        # Create necessary folders
        setup_folders()
        
        # Initialize security components
        security_manager, audit_logger, compliance_manager = init_security_components()
        
        # Display demo options
        print("\n===== UKG SOC 2 Security and Compliance Demo =====")
        print("This demo simulates the SOC 2 Type 2 compliance capabilities:")
        print("  1. Security Management")
        print("  2. Audit Logging")
        print("  3. Compliance Monitoring")
        print("  4. Threat Detection")
        print("  5. Comprehensive Reporting")
        print("\nAvailable demo options:")
        print("1. Simulate security events (authentication, data access, etc.)")
        print("2. View security and compliance status")
        print("3. View recent audit and compliance events")
        print("4. Generate SOC 2 compliance report")
        print("5. Run security scan")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            # Simulate security events
            simulate_security_events(security_manager, audit_logger, compliance_manager)
            print("\nSecurity events simulated successfully!")
            
        elif choice == "2":
            # View security and compliance status
            display_security_status(security_manager, compliance_manager)
            
        elif choice == "3":
            # View recent events
            display_recent_events(audit_logger, compliance_manager)
            
        elif choice == "4":
            # Generate compliance report
            print("\nGenerating SOC 2 compliance report...")
            report = compliance_manager.generate_compliance_report()
            
            print("\nCOMPLIANCE REPORT SUMMARY:")
            print(f"  Report ID: {report['report_id']}")
            print(f"  Generated: {report['generated_at']}")
            print(f"  Period: {report['period_start']} to {report['period_end']}")
            print(f"  Overall Compliance Score: {report['overall_compliance_score']}%")
            
            print("\nCOMPLIANCE SCORES BY CATEGORY:")
            for category, score in report['compliance_scores'].items():
                print(f"  {category.upper()}: {score}%")
            
            print(f"\nReport saved to: logs/compliance/report_{report['period_start'].split('T')[0]}_{report['period_end'].split('T')[0]}.json")
            
        elif choice == "5":
            # Run security scan
            print("\nRunning security scan...")
            security_manager._perform_security_scan()
            
            results = security_manager.last_scan_results
            print("\nSECURITY SCAN RESULTS:")
            print(f"  Scan ID: {results['scan_id']}")
            print(f"  Timestamp: {results['timestamp']}")
            print(f"  Vulnerabilities: {len(results['vulnerabilities'])}")
            print(f"  Warnings: {len(results['warnings'])}")
            
            if results['vulnerabilities']:
                print("\nVULNERABILITIES:")
                for vuln in results['vulnerabilities']:
                    print(f"  [HIGH] {vuln['description']}")
            
            if results['warnings']:
                print("\nWARNINGS:")
                for warning in results['warnings']:
                    print(f"  [LOW] {warning['description']}")
            
        elif choice == "6":
            print("\nExiting demo.")
            return
        else:
            print("\nInvalid choice. Please run the demo again.")
            return
        
        # Ask if the user wants to continue
        continue_demo = input("\nWould you like to run another demo? (y/n): ")
        if continue_demo.lower() == 'y':
            run_demo()
    
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        print("Please check the logs for more details.")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UKG SOC 2 Compliance Demo")
    parser.add_argument("--setup", action="store_true", help="Create necessary folders")
    args = parser.parse_args()
    
    if args.setup:
        setup_folders()
    
    # Run the demo
    run_demo()
