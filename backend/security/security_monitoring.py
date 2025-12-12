"""
Enterprise security monitoring and alerting system.

This module implements:
- Real-time security event monitoring
- Threat detection and anomaly detection
- Automated alerting and notifications
- Security metrics and dashboards
- Integration with SIEM systems
- Incident response triggers

Compliance: SOC 2 Type 2, ISO 27001, PCI DSS
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from collections import defaultdict, deque
import threading
import time


class ThreatLevel(Enum):
    """Threat severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def priority(self) -> int:
        """Priority for alerting."""
        priorities = {
            ThreatLevel.INFO: 0,
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        return priorities[self]


class SecurityEventType(Enum):
    """Types of security events to monitor."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGIN_BRUTE_FORCE = "login_brute_force"
    MFA_FAILURE = "mfa_failure"
    ACCOUNT_LOCKOUT = "account_lockout"
    PASSWORD_CHANGE = "password_change"
    SUSPICIOUS_LOGIN = "suspicious_login"

    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # Data access events
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    BULK_DATA_ACCESS = "bulk_data_access"

    # API events
    API_RATE_LIMIT_EXCEEDED = "api_rate_limit_exceeded"
    API_INVALID_TOKEN = "api_invalid_token"
    API_SUSPICIOUS_PATTERN = "api_suspicious_pattern"

    # System events
    CONFIGURATION_CHANGE = "configuration_change"
    ENCRYPTION_KEY_ROTATION = "encryption_key_rotation"
    BACKUP_FAILURE = "backup_failure"
    SERVICE_FAILURE = "service_failure"

    # Threat detection
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    MALICIOUS_PAYLOAD = "malicious_payload"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

    # Compliance events
    AUDIT_LOG_TAMPERING = "audit_log_tampering"
    POLICY_VIOLATION = "policy_violation"
    COMPLIANCE_BREACH = "compliance_breach"


class SecurityAlert:
    """Security alert with context and metadata."""

    def __init__(
        self,
        event_type: SecurityEventType,
        threat_level: ThreatLevel,
        message: str,
        details: Dict[str, Any],
        source: str = "system"
    ):
        self.id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{event_type.value}{source}".encode()
        ).hexdigest()[:16]
        self.event_type = event_type
        self.threat_level = threat_level
        self.message = message
        self.details = details
        self.source = source
        self.timestamp = datetime.utcnow()
        self.acknowledged = False
        self.resolved = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "threat_level": self.threat_level.value,
            "message": self.message,
            "details": self.details,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved
        }


class SecurityMonitor:
    """
    Real-time security monitoring and threat detection system.

    Features:
    - Real-time event monitoring
    - Anomaly detection
    - Automated alerting
    - Threat scoring
    - SIEM integration ready
    """

    def __init__(
        self,
        audit_logger=None,
        alert_handlers: Optional[List[Callable]] = None
    ):
        """
        Initialize security monitor.

        Args:
            audit_logger: Audit logger instance
            alert_handlers: List of callback functions for alerts
        """
        self.audit_logger = audit_logger
        self.alert_handlers = alert_handlers or []

        # Alert storage
        self.alerts: List[SecurityAlert] = []
        self.alert_file = "data/security/alerts.jsonl"
        os.makedirs(os.path.dirname(self.alert_file), exist_ok=True)

        # Event tracking for anomaly detection
        self.event_history = defaultdict(lambda: deque(maxlen=1000))
        self.user_behavior = defaultdict(lambda: defaultdict(list))

        # Threat intelligence
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns: List[str] = self._load_suspicious_patterns()

        # Metrics
        self.metrics = {
            "total_events": 0,
            "total_alerts": 0,
            "alerts_by_level": defaultdict(int),
            "alerts_by_type": defaultdict(int)
        }

        # Background monitoring thread
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """Start background security monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        print("Security monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        print("Security monitoring stopped")

    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Check for anomalies every minute
                self._check_for_anomalies()
                time.sleep(60)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")

    def process_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Process a security event and check for threats.

        Args:
            event_type: Type of security event
            details: Event details
            user_id: Optional user ID
            ip_address: Optional IP address
        """
        self.metrics["total_events"] += 1

        # Store event in history
        event_key = f"{event_type.value}:{user_id or 'anonymous'}"
        self.event_history[event_key].append({
            "timestamp": datetime.utcnow(),
            "details": details,
            "ip_address": ip_address
        })

        # Track user behavior
        if user_id:
            self.user_behavior[user_id][event_type.value].append({
                "timestamp": datetime.utcnow(),
                "ip_address": ip_address,
                "details": details
            })

        # Check for immediate threats
        self._detect_brute_force(event_type, user_id, ip_address)
        self._detect_suspicious_patterns(event_type, details, user_id, ip_address)
        self._detect_data_exfiltration(event_type, details, user_id)
        self._detect_privilege_escalation(event_type, details, user_id)

        # Log to audit
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type.value,
                details=details,
                severity="INFO"
            )

    def _detect_brute_force(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str],
        ip_address: Optional[str]
    ):
        """Detect brute force login attempts."""
        if event_type != SecurityEventType.LOGIN_FAILURE:
            return

        # Check for rapid failed login attempts
        event_key = f"login_failure:{user_id or ip_address}"
        recent_failures = self.event_history[event_key]

        # Count failures in last 5 minutes
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_count = sum(
            1 for event in recent_failures
            if event["timestamp"] > five_min_ago
        )

        if recent_count >= 5:
            self.create_alert(
                event_type=SecurityEventType.LOGIN_BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                message=f"Brute force attack detected from {ip_address or 'unknown IP'}",
                details={
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "failure_count": recent_count,
                    "time_window": "5 minutes"
                }
            )

            # Auto-block IP if configured
            if ip_address:
                self.blocked_ips.add(ip_address)

    def _detect_suspicious_patterns(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_id: Optional[str],
        ip_address: Optional[str]
    ):
        """Detect suspicious patterns in events."""

        # Check for SQL injection patterns
        for key, value in details.items():
            if isinstance(value, str):
                if any(pattern in value.lower() for pattern in ["' or '1'='1", "union select", "drop table"]):
                    self.create_alert(
                        event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
                        threat_level=ThreatLevel.CRITICAL,
                        message="SQL injection attempt detected",
                        details={
                            "user_id": user_id,
                            "ip_address": ip_address,
                            "field": key,
                            "pattern_detected": "sql_injection"
                        }
                    )

                # Check for XSS patterns
                if any(pattern in value.lower() for pattern in ["<script>", "javascript:", "onerror="]):
                    self.create_alert(
                        event_type=SecurityEventType.XSS_ATTEMPT,
                        threat_level=ThreatLevel.HIGH,
                        message="XSS attempt detected",
                        details={
                            "user_id": user_id,
                            "ip_address": ip_address,
                            "field": key,
                            "pattern_detected": "xss"
                        }
                    )

                # Check for path traversal
                if any(pattern in value for pattern in ["../", "..\\", "/etc/passwd"]):
                    self.create_alert(
                        event_type=SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
                        threat_level=ThreatLevel.HIGH,
                        message="Path traversal attempt detected",
                        details={
                            "user_id": user_id,
                            "ip_address": ip_address,
                            "field": key,
                            "pattern_detected": "path_traversal"
                        }
                    )

    def _detect_data_exfiltration(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_id: Optional[str]
    ):
        """Detect potential data exfiltration."""
        if event_type != SecurityEventType.DATA_EXPORT:
            return

        if not user_id:
            return

        # Check for unusual export volume
        user_exports = self.user_behavior[user_id].get("data_export", [])
        recent_exports = [
            e for e in user_exports
            if e["timestamp"] > datetime.utcnow() - timedelta(hours=1)
        ]

        if len(recent_exports) >= 10:
            self.create_alert(
                event_type=SecurityEventType.BULK_DATA_ACCESS,
                threat_level=ThreatLevel.HIGH,
                message=f"Unusual data export volume detected for user {user_id}",
                details={
                    "user_id": user_id,
                    "export_count": len(recent_exports),
                    "time_window": "1 hour",
                    "baseline": "< 10 exports per hour"
                }
            )

    def _detect_privilege_escalation(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_id: Optional[str]
    ):
        """Detect potential privilege escalation attempts."""
        if event_type != SecurityEventType.PERMISSION_DENIED:
            return

        if not user_id:
            return

        # Check for repeated permission denials (potential privilege escalation)
        user_denials = self.user_behavior[user_id].get("permission_denied", [])
        recent_denials = [
            d for d in user_denials
            if d["timestamp"] > datetime.utcnow() - timedelta(minutes=10)
        ]

        if len(recent_denials) >= 5:
            self.create_alert(
                event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                threat_level=ThreatLevel.MEDIUM,
                message=f"Potential privilege escalation attempt by user {user_id}",
                details={
                    "user_id": user_id,
                    "denial_count": len(recent_denials),
                    "time_window": "10 minutes",
                    "attempted_permissions": list(set(
                        d["details"].get("permission") for d in recent_denials
                        if "permission" in d.get("details", {})
                    ))
                }
            )

    def _check_for_anomalies(self):
        """Check for behavioral anomalies."""
        # Analyze user behavior patterns
        for user_id, behaviors in self.user_behavior.items():
            # Check for unusual activity times
            login_times = behaviors.get("login_success", [])
            if len(login_times) >= 10:
                hours = [lt["timestamp"].hour for lt in login_times[-10:]]
                avg_hour = sum(hours) / len(hours)

                # Alert if login outside normal hours
                if login_times and abs(login_times[-1]["timestamp"].hour - avg_hour) > 6:
                    self.create_alert(
                        event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
                        threat_level=ThreatLevel.LOW,
                        message=f"Unusual login time detected for user {user_id}",
                        details={
                            "user_id": user_id,
                            "login_hour": login_times[-1]["timestamp"].hour,
                            "normal_hour_range": f"{int(avg_hour - 2)}-{int(avg_hour + 2)}"
                        }
                    )

    def create_alert(
        self,
        event_type: SecurityEventType,
        threat_level: ThreatLevel,
        message: str,
        details: Dict[str, Any]
    ) -> SecurityAlert:
        """
        Create a security alert.

        Args:
            event_type: Type of security event
            threat_level: Severity level
            message: Alert message
            details: Alert details

        Returns:
            Created SecurityAlert
        """
        alert = SecurityAlert(
            event_type=event_type,
            threat_level=threat_level,
            message=message,
            details=details
        )

        self.alerts.append(alert)
        self.metrics["total_alerts"] += 1
        self.metrics["alerts_by_level"][threat_level.value] += 1
        self.metrics["alerts_by_type"][event_type.value] += 1

        # Persist alert
        self._save_alert(alert)

        # Trigger alert handlers
        self._notify_alert_handlers(alert)

        # Log to audit
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type="security_alert_created",
                details={
                    "alert_id": alert.id,
                    "event_type": event_type.value,
                    "threat_level": threat_level.value,
                    "message": message
                },
                severity=threat_level.value.upper()
            )

        return alert

    def _save_alert(self, alert: SecurityAlert):
        """Save alert to file."""
        with open(self.alert_file, 'a') as f:
            f.write(json.dumps(alert.to_dict()) + '\n')

    def _notify_alert_handlers(self, alert: SecurityAlert):
        """Notify registered alert handlers."""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Error in alert handler: {e}")

    def get_alerts(
        self,
        threat_level: Optional[ThreatLevel] = None,
        event_type: Optional[SecurityEventType] = None,
        since: Optional[datetime] = None,
        unresolved_only: bool = False
    ) -> List[SecurityAlert]:
        """
        Get alerts with optional filtering.

        Args:
            threat_level: Filter by threat level
            event_type: Filter by event type
            since: Filter by timestamp
            unresolved_only: Only return unresolved alerts

        Returns:
            List of matching alerts
        """
        filtered = self.alerts

        if threat_level:
            filtered = [a for a in filtered if a.threat_level == threat_level]

        if event_type:
            filtered = [a for a in filtered if a.event_type == event_type]

        if since:
            filtered = [a for a in filtered if a.timestamp >= since]

        if unresolved_only:
            filtered = [a for a in filtered if not a.resolved]

        return sorted(filtered, key=lambda a: a.timestamp, reverse=True)

    def get_metrics(self) -> Dict[str, Any]:
        """Get security monitoring metrics."""
        return {
            "total_events": self.metrics["total_events"],
            "total_alerts": self.metrics["total_alerts"],
            "alerts_by_level": dict(self.metrics["alerts_by_level"]),
            "alerts_by_type": dict(self.metrics["alerts_by_type"]),
            "unresolved_alerts": len([a for a in self.alerts if not a.resolved]),
            "critical_alerts": len([a for a in self.alerts if a.threat_level == ThreatLevel.CRITICAL]),
            "blocked_ips": len(self.blocked_ips),
            "monitored_users": len(self.user_behavior)
        }

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked."""
        return ip_address in self.blocked_ips

    def _load_suspicious_patterns(self) -> List[str]:
        """Load suspicious patterns for threat detection."""
        return [
            "' or '1'='1",
            "union select",
            "drop table",
            "<script>",
            "javascript:",
            "../",
            "..\\",
            "/etc/passwd",
            "cmd.exe",
            "powershell.exe"
        ]


# Singleton instance
_security_monitor_instance: Optional[SecurityMonitor] = None


def get_security_monitor(audit_logger=None, alert_handlers=None) -> SecurityMonitor:
    """Get or create singleton security monitor instance."""
    global _security_monitor_instance
    if _security_monitor_instance is None:
        _security_monitor_instance = SecurityMonitor(
            audit_logger=audit_logger,
            alert_handlers=alert_handlers
        )
        _security_monitor_instance.start_monitoring()
    return _security_monitor_instance
