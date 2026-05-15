
"""
Universal Knowledge Graph (UKG) Audit Logging System

This module provides comprehensive audit logging capabilities for the UKG enterprise architecture,
supporting SOC 2 Type 2 compliance requirements.
"""

import os
import logging
import logging.handlers
import json
import hashlib
import hmac
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional
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
        self.immutable_replica_enabled = (
            bool(self.config.get("immutable_replica_enabled"))
            if "immutable_replica_enabled" in self.config
            else str(os.environ.get("AUDIT_IMMUTABLE_REPLICA_ENABLED", "false")).strip().lower() in {"1", "true", "yes", "on"}
        )
        self.immutable_replica_dir = self.config.get(
            "immutable_replica_dir",
            os.environ.get("AUDIT_IMMUTABLE_REPLICA_DIR", "logs/audit_immutable"),
        )
        self.immutable_hmac_secret = str(
            self.config.get("immutable_hmac_secret")
            or os.environ.get("AUDIT_IMMUTABLE_HMAC_SECRET")
            or os.environ.get("SESSION_SECRET")
            or ""
        ).strip()
        self._immutable_last_hash = ""
        if self.immutable_replica_enabled:
            os.makedirs(self.immutable_replica_dir, exist_ok=True)

        # Initialize log rotation thread
        self.log_rotation_active = False
        self.log_rotation_thread = None
        self._rotation_stop_event = threading.Event()
        self._write_lock = threading.Lock()
        self._managed_handlers: List[logging.Handler] = []
        
        # Start log rotation
        self.start_log_rotation()
        
        logger.info("Audit Logger initialized")

    def _normalize_logger_handlers(self) -> None:
        """Ensure attached handlers have comparable log levels."""
        for handler in list(logger.handlers):
            level = getattr(handler, "level", logging.NOTSET)
            if not isinstance(level, int):
                try:
                    handler.level = logging.NOTSET
                except Exception:
                    logger.removeHandler(handler)
    
    def start_log_rotation(self):
        """Start the log rotation thread"""
        self._normalize_logger_handlers()
        if not self.log_rotation_active:
            self.log_rotation_active = True
            self._rotation_stop_event.clear()
            self.log_rotation_thread = threading.Thread(
                target=self._log_rotation_loop,
                daemon=True
            )
            self.log_rotation_thread.start()
            logger.info("Audit log rotation started")
    
    def stop_log_rotation(self):
        """Stop the log rotation thread"""
        self.log_rotation_active = False
        self._rotation_stop_event.set()
        if self.log_rotation_thread:
            self.log_rotation_thread.join(timeout=1)
        for handler in list(self._managed_handlers):
            try:
                logger.removeHandler(handler)
                handler.close()
            except Exception:
                pass
        self._managed_handlers.clear()
        self._normalize_logger_handlers()
        logger.info("Audit log rotation stopped")
    
    def _log_rotation_loop(self):
        """Background thread for log rotation"""
        while self.log_rotation_active and not self._rotation_stop_event.is_set():
            try:
                current_date = datetime.now().strftime("%Y%m%d")
                
                # If the date has changed, rotate the log file
                if current_date != self.current_date:
                    self.current_date = current_date
                    self.current_log_file = f"logs/audit/audit_{self.current_date}.jsonl"
                    logger.info(f"Rotated audit log to {self.current_log_file}")
                
                # Wait up to an hour but wake immediately on shutdown.
                if self._rotation_stop_event.wait(timeout=3600):
                    break
                
            except Exception as e:
                logger.error(f"Error in log rotation: {str(e)}")
                if self._rotation_stop_event.wait(timeout=300):
                    break  # Retry after 5 minutes

    @staticmethod
    def _hash_json(payload: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def _immutable_log_file_path(self) -> str:
        return os.path.join(self.immutable_replica_dir, f"audit_immutable_{self.current_date}.jsonl")

    def _compute_immutable_replica_hash(self, event_hash: str, previous_replica_hash: str, replica_timestamp: str) -> str:
        seed = f"{event_hash}|{previous_replica_hash}|{replica_timestamp}"
        if self.immutable_hmac_secret:
            return hmac.new(
                self.immutable_hmac_secret.encode("utf-8"),
                seed.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        return hashlib.sha256(seed.encode()).hexdigest()

    def _append_immutable_replica(self, audit_event: Dict[str, Any]) -> None:
        if not self.immutable_replica_enabled:
            return

        event_hash = str(audit_event.get("hash") or self._hash_json(audit_event))
        replica_timestamp = datetime.now(UTC).isoformat()
        previous_replica_hash = self._immutable_last_hash
        replica_hash = self._compute_immutable_replica_hash(
            event_hash=event_hash,
            previous_replica_hash=previous_replica_hash,
            replica_timestamp=replica_timestamp,
        )
        replica_event: Dict[str, Any] = {
            "replica_timestamp": replica_timestamp,
            "event_id": audit_event.get("id"),
            "event_hash": event_hash,
            "previous_replica_hash": previous_replica_hash,
            "replica_hash": replica_hash,
            "event": audit_event,
        }

        with open(self._immutable_log_file_path(), 'a') as replica_file:
            replica_file.write(json.dumps(replica_event) + "\n")
        self._immutable_last_hash = replica_hash

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
            timestamp = datetime.now(UTC).isoformat()
            event_id = str(uuid.uuid4())
            
            # Create the audit event
            audit_event: Dict[str, Any] = {
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
            audit_event["hash"] = self._hash_json(audit_event)
            
            # Write to the audit log file
            with self._write_lock:
                with open(self.current_log_file, 'a') as f:
                    f.write(json.dumps(audit_event) + "\n")
                try:
                    self._append_immutable_replica(audit_event)
                except Exception as immutable_err:
                    logger.warning(f"Failed to append immutable audit replica: {immutable_err}")
            
            # --- Windows Desktop: Database Persistence ---
            try:
                # Use deferred import to avoid circular dependency with models
                from models import AuditLog
                from extensions import db
                from flask import has_app_context
                
                if has_app_context():
                    if not db.session.is_active:
                        db.session.rollback()

                    db_audit = AuditLog(
                        user_id=user_id,
                        action=action or event_type,
                        details=json.dumps(details) if details else None,
                        ip_address=ip_address
                    )
                    
                    # If this is a Windows identity, we might have SID in details or as user_id prefix
                    if details and "windows_sid" in details:
                        db_audit.windows_sid = details["windows_sid"]
                    elif user_id and str(user_id).startswith("S-"):
                        db_audit.windows_sid = str(user_id)
                        
                    db.session.add(db_audit)
                    db.session.commit()
            except Exception as db_err:
                 # Roll back failed transaction so the request-scoped session stays usable.
                 try:
                     from extensions import db as _db
                     _db.session.rollback()
                 except Exception:
                     pass
                 # Log error but don't fail the primary file logging
                 logger.warning(f"Failed to persist audit event to DB: {db_err}")

            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            
            # Try to log to a fallback location
            try:
                with open("logs/audit_errors.log", 'a') as f:
                    f.write(f"{datetime.now(UTC).isoformat()} | ERROR | {str(e)}\n")
            except (IOError, OSError):
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
                        
                    current_date = current_date + timedelta(days=1)
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

    def verify_immutable_replica_integrity(self, replica_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify immutable replica hash-chain integrity.
        """
        if not replica_file:
            replica_file = self._immutable_log_file_path()

        results = {
            "replica_file": replica_file,
            "verified": True,
            "total_entries": 0,
            "valid_entries": 0,
            "invalid_entries": 0,
            "invalid_event_ids": [],
        }

        try:
            if not os.path.exists(replica_file):
                results["verified"] = False
                results["error"] = "Replica file does not exist"
                return results

            previous_replica_hash = ""
            with open(replica_file, 'r') as file_obj:
                for line in file_obj:
                    if not line.strip():
                        continue
                    results["total_entries"] += 1
                    entry: Dict[str, Any] = {}
                    try:
                        entry = json.loads(line)
                        event = entry.get("event") or {}
                        stored_event_hash = str(entry.get("event_hash") or "")
                        event_for_hash = dict(event)
                        event_for_hash.pop("hash", None)
                        expected_event_hash = self._hash_json(event_for_hash)
                        if stored_event_hash != expected_event_hash:
                            raise ValueError("event_hash_mismatch")

                        if str(entry.get("previous_replica_hash") or "") != previous_replica_hash:
                            raise ValueError("replica_chain_previous_hash_mismatch")

                        expected_replica_hash = self._compute_immutable_replica_hash(
                            event_hash=stored_event_hash,
                            previous_replica_hash=previous_replica_hash,
                            replica_timestamp=str(entry.get("replica_timestamp") or ""),
                        )
                        if str(entry.get("replica_hash") or "") != expected_replica_hash:
                            raise ValueError("replica_hash_mismatch")

                        previous_replica_hash = expected_replica_hash
                        results["valid_entries"] += 1
                    except Exception:
                        results["invalid_entries"] += 1
                        if entry_id := (entry or {}).get("event_id"):
                            results["invalid_event_ids"].append(str(entry_id))

            results["verified"] = results["invalid_entries"] == 0
            return results
        except Exception as e:
            logger.error(f"Error verifying immutable replica log: {str(e)}")
            results["verified"] = False
            results["error"] = str(e)
            return results

    def enable_syslog_forwarding(self, host: str, port: int = 514, facility: int = logging.handlers.SysLogHandler.LOG_USER) -> bool:
        """
        Enable forwarding audit logs to a remote Syslog server (SIEM).
        
        Args:
            host: Syslog server hostname or IP
            port: Syslog server port (default 514)
            facility: Syslog facility (default LOG_USER)
            
        Returns:
            True if configured successfully
        """
        try:
            handler = logging.handlers.SysLogHandler(address=(host, port), facility=facility)
            formatter = logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            try:
                handler.setLevel(logging.NOTSET)
            except Exception:
                pass
            if not isinstance(getattr(handler, "level", None), int):
                handler.level = logging.NOTSET
            logger.addHandler(handler)
            self._managed_handlers.append(handler)
            logger.info(f"Syslog forwarding enabled to {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable Syslog forwarding: {str(e)}")
            return False

    def export_to_csv(self, output_file: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> int:
        """
        Export audit logs to a CSV file for compliance reporting.
        
        Args:
            output_file: Path to the output CSV file
            start_time: Filter events after this time
            end_time: Filter events before this time
            
        Returns:
            Number of events exported
        """
        import csv
        
        events = self.get_audit_events(start_time=start_time, end_time=end_time, limit=100000)
        
        if not events:
            return 0
            
        # Determine all possible fields from the events
        fieldnames = set()
        for event in events:
            fieldnames.update(event.keys())
            if "details" in event and isinstance(event["details"], dict):
                 # Flatten details for CSV if needed, or keep as JSON string
                 pass

        # Standard fields order
        ordered_fields = ['timestamp', 'event_type', 'status', 'user_id', 'action', 'resource_id', 'ip_address', 'id', 'hash']
        # Add remaining fields
        for field in fieldnames:
            if field not in ordered_fields:
                ordered_fields.append(field)
                
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=ordered_fields, extrasaction='ignore')
                writer.writeheader()
                for event in events:
                    # Ensure details is valid JSON string if it exists, for CSV readability
                    row = event.copy()
                    if "details" in row and isinstance(row["details"], (dict, list)):
                        row["details"] = json.dumps(row["details"])
                    writer.writerow(row)
            
            logger.info(f"Exported {len(events)} audit events to {output_file}")
            return len(events)
        except Exception as e:
            logger.error(f"Failed to export audit logs to CSV: {str(e)}")
            raise e

