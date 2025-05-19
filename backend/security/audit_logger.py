
"""
Universal Knowledge Graph (UKG) Audit Logging System

This module provides comprehensive audit logging capabilities for the UKG enterprise architecture,
supporting SOC 2 Type 2 compliance requirements.
"""

import os
import logging
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import threading
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UKG-Audit")

class AuditLogger:
    """
    Audit Logger for UKG Enterprise System
    
    Provides comprehensive audit logging capabilities to support SOC 2 compliance
    and security monitoring.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Audit Logger.
        
        Args:
            config: Configuration settings
        """
        self.config = config or {}
        
        # Create audit logs directory
        os.makedirs("logs/audit", exist_ok=True)
        
        # Initialize the current log file
        self.current_date = datetime.now().strftime("%Y%m%d")
        self.current_log_file = f"logs/audit/audit_{self.current_date}.jsonl"
        
        # Initialize log rotation thread
        self.log_rotation_active = False
        self.log_rotation_thread = None
        
        # Start log rotation
        self.start_log_rotation()
        
        logger.info("Audit Logger initialized")
    
    def start_log_rotation(self):
        """Start the log rotation thread"""
        if not self.log_rotation_active:
            self.log_rotation_active = True
            self.log_rotation_thread = threading.Thread(
                target=self._log_rotation_loop,
                daemon=True
            )
            self.log_rotation_thread.start()
            logger.info("Audit log rotation started")
    
    def stop_log_rotation(self):
        """Stop the log rotation thread"""
        self.log_rotation_active = False
        if self.log_rotation_thread:
            self.log_rotation_thread.join(timeout=5)
            logger.info("Audit log rotation stopped")
    
    def _log_rotation_loop(self):
        """Background thread for log rotation"""
        while self.log_rotation_active:
            try:
                current_date = datetime.now().strftime("%Y%m%d")
                
                # If the date has changed, rotate the log file
                if current_date != self.current_date:
                    self.current_date = current_date
                    self.current_log_file = f"logs/audit/audit_{self.current_date}.jsonl"
                    logger.info(f"Rotated audit log to {self.current_log_file}")
                
                # Sleep until the next day (check every hour)
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in log rotation: {str(e)}")
                time.sleep(300)  # Retry after 5 minutes
    
    def log_audit_event(self, 
                         event_type: str,
                         user_id: Optional[str] = None,
                         resource_id: Optional[str] = None,
                         action: Optional[str] = None,
                         status: str = "success",
                         details: Optional[Dict[str, Any]] = None,
                         request_id: Optional[str] = None,
                         ip_address: Optional[str] = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., authentication, data_access)
            user_id: ID of the user who performed the action
            resource_id: ID of the resource affected
            action: The action performed
            status: Outcome status (success, failure)
            details: Additional details about the event
            request_id: ID of the associated request
            ip_address: IP address of the client
            
        Returns:
            The generated event ID
        """
        try:
            timestamp = datetime.now().isoformat()
            event_id = str(uuid.uuid4())
            
            # Create the audit event
            audit_event = {
                "id": event_id,
                "timestamp": timestamp,
                "event_type": event_type,
                "status": status
            }
            
            # Add optional fields if provided
            if user_id:
                audit_event["user_id"] = user_id
                
            if resource_id:
                audit_event["resource_id"] = resource_id
                
            if action:
                audit_event["action"] = action
                
            if details:
                audit_event["details"] = details
                
            if request_id:
                audit_event["request_id"] = request_id
                
            if ip_address:
                audit_event["ip_address"] = ip_address
            
            # Generate event hash for integrity
            event_data = json.dumps(audit_event, sort_keys=True)
            audit_event["hash"] = hashlib.sha256(event_data.encode()).hexdigest()
            
            # Write to the audit log file
            with open(self.current_log_file, 'a') as f:
                f.write(json.dumps(audit_event) + "\n")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            
            # Try to log to a fallback location
            try:
                with open("logs/audit_errors.log", 'a') as f:
                    f.write(f"{datetime.now().isoformat()} | ERROR | {str(e)}\n")
            except:
                pass
                
            return str(uuid.uuid4())  # Return a generated ID even on failure
    
    def log_authentication(self, user_id: str, status: str, ip_address: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an authentication event.
        
        Args:
            user_id: ID of the user
            status: Outcome (success, failure)
            ip_address: IP address of the client
            details: Additional details
            
        Returns:
            The generated event ID
        """
        return self.log_audit_event(
            event_type="authentication",
            user_id=user_id,
            action="login",
            status=status,
            ip_address=ip_address,
            details=details
        )
    
    def log_authorization(self, user_id: str, resource_id: str, action: str, status: str,
                         details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an authorization event.
        
        Args:
            user_id: ID of the user
            resource_id: ID of the resource
            action: The action attempted
            status: Outcome (success, failure)
            details: Additional details
            
        Returns:
            The generated event ID
        """
        return self.log_audit_event(
            event_type="authorization",
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            status=status,
            details=details
        )
    
    def log_data_access(self, user_id: str, resource_id: str, action: str,
                       details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a data access event.
        
        Args:
            user_id: ID of the user
            resource_id: ID of the resource
            action: The access action (read, write, delete)
            details: Additional details
            
        Returns:
            The generated event ID
        """
        return self.log_audit_event(
            event_type="data_access",
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            status="success",
            details=details
        )
    
    def log_api_request(self, request_id: str, user_id: Optional[str], endpoint: str,
                       method: str, status_code: int, ip_address: Optional[str] = None) -> str:
        """
        Log an API request event.
        
        Args:
            request_id: ID of the request
            user_id: ID of the user (if authenticated)
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            ip_address: IP address of the client
            
        Returns:
            The generated event ID
        """
        details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        }
        
        status = "success" if status_code < 400 else "failure"
        
        return self.log_audit_event(
            event_type="api_request",
            user_id=user_id,
            action="request",
            status=status,
            details=details,
            request_id=request_id,
            ip_address=ip_address
        )
    
    def log_system_event(self, event_type: str, action: str, status: str,
                        details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a system event.
        
        Args:
            event_type: Type of system event
            action: The action performed
            status: Outcome (success, failure)
            details: Additional details
            
        Returns:
            The generated event ID
        """
        return self.log_audit_event(
            event_type=f"system_{event_type}",
            action=action,
            status=status,
            details=details
        )
    
    def get_audit_events(self, start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        event_type: Optional[str] = None,
                        user_id: Optional[str] = None,
                        resource_id: Optional[str] = None,
                        action: Optional[str] = None,
                        status: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit events filtered by criteria.
        
        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_id: Filter by resource ID
            action: Filter by action
            status: Filter by status
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = []
        
        try:
            # Determine which log files to search based on date range
            log_files = []
            
            if start_time and end_time:
                current_date = start_time.date()
                end_date = end_time.date()
                
                while current_date <= end_date:
                    date_str = current_date.strftime("%Y%m%d")
                    log_file = f"logs/audit/audit_{date_str}.jsonl"
                    
                    if os.path.exists(log_file):
                        log_files.append(log_file)
                        
                    current_date = current_date.replace(day=current_date.day + 1)
            else:
                # Use the current log file if no date range specified
                if os.path.exists(self.current_log_file):
                    log_files.append(self.current_log_file)
            
            # Search through the log files
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            
                            # Apply filters
                            if start_time and datetime.fromisoformat(event["timestamp"]) < start_time:
                                continue
                                
                            if end_time and datetime.fromisoformat(event["timestamp"]) > end_time:
                                continue
                                
                            if event_type and event.get("event_type") != event_type:
                                continue
                                
                            if user_id and event.get("user_id") != user_id:
                                continue
                                
                            if resource_id and event.get("resource_id") != resource_id:
                                continue
                                
                            if action and event.get("action") != action:
                                continue
                                
                            if status and event.get("status") != status:
                                continue
                                
                            events.append(event)
                            
                            if len(events) >= limit:
                                break
                                
                    if len(events) >= limit:
                        break
            
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving audit events: {str(e)}")
            return []
    
    def verify_audit_log_integrity(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify the integrity of audit log entries.
        
        Args:
            log_file: Path to the log file to verify, defaults to current log file
            
        Returns:
            Dictionary with verification results
        """
        if not log_file:
            log_file = self.current_log_file
            
        results = {
            "log_file": log_file,
            "verified": True,
            "total_entries": 0,
            "valid_entries": 0,
            "invalid_entries": 0,
            "invalid_entry_ids": []
        }
        
        try:
            if not os.path.exists(log_file):
                results["verified"] = False
                results["error"] = "Log file does not exist"
                return results
                
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        results["total_entries"] += 1
                        
                        try:
                            event = json.loads(line)
                            
                            # Skip if no hash (old entries may not have it)
                            if "hash" not in event:
                                results["valid_entries"] += 1
                                continue
                                
                            # Extract and remove the hash
                            stored_hash = event["hash"]
                            event_copy = event.copy()
                            del event_copy["hash"]
                            
                            # Calculate the hash
                            event_data = json.dumps(event_copy, sort_keys=True)
                            calculated_hash = hashlib.sha256(event_data.encode()).hexdigest()
                            
                            # Verify the hash
                            if calculated_hash == stored_hash:
                                results["valid_entries"] += 1
                            else:
                                results["invalid_entries"] += 1
                                if "id" in event:
                                    results["invalid_entry_ids"].append(event["id"])
                                    
                        except Exception as e:
                            results["invalid_entries"] += 1
                            logger.error(f"Error verifying audit entry: {str(e)}")
            
            # Set the verified flag based on invalid entries
            results["verified"] = results["invalid_entries"] == 0
            
            return results
            
        except Exception as e:
            logger.error(f"Error verifying audit log: {str(e)}")
            results["verified"] = False
            results["error"] = str(e)
            return results
