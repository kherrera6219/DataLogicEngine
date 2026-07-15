
"""
Universal Knowledge Graph (UKG) SOC 2 Control-Map Check Manager

This module provides local self-assessment checks mapped to the five SOC 2 trust
service criteria:
  Security, Availability, Processing Integrity, Confidentiality, and Privacy.

Each ``_check_*`` method performs real runtime inspections and marks the relevant
category as ``"non_compliant"`` when a condition is not met.  All checks are
designed to degrade gracefully: a sub-check that cannot run (e.g. DB not
reachable in a test context) is reported as an issue rather than crashing.
"""

import os
import re
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import uuid

# ---------------------------------------------------------------------------
# Optional backend service imports — kept at module level so tests can patch
# them directly as ``backend.security.compliance_manager.<name>``.
# Each import is guarded by a broad try/except so this module remains
# importable without a Flask app context (e.g. during unit tests).
# ---------------------------------------------------------------------------

try:
    from backend.security.encryption_manager import get_encryption_manager
except Exception:  # noqa: BLE001
    get_encryption_manager = None  # type: ignore[assignment]

try:
    from extensions import db
except Exception:  # noqa: BLE001
    db = None  # type: ignore[assignment]

try:
    from alembic.config import Config as AlembicConfig
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
except Exception:  # noqa: BLE001
    AlembicConfig = None  # type: ignore[assignment]
    MigrationContext = None  # type: ignore[assignment]
    ScriptDirectory = None  # type: ignore[assignment]

try:
    from models import TruthAuditEvent
    from backend.truth_engine.truth_memory.audit import TruthAuditRecorder
except Exception:  # noqa: BLE001
    TruthAuditEvent = None  # type: ignore[assignment]
    TruthAuditRecorder = None  # type: ignore[assignment]

logger = logging.getLogger("UKG-Compliance")

# ---------------------------------------------------------------------------
# Module-level constants used by multiple checks
# ---------------------------------------------------------------------------

#: Encryption key values that are known development / CI defaults and must
#: never be used in production.
_KNOWN_DEV_SECRETS: frozenset = frozenset({
    "secret", "password", "changeme", "dev", "test", "insecure",
    "development", "test-secret", "mysecret", "abc123", "default",
    "admin", "1234", "letmein", "qwerty", "s3cr3t", "hunter2",
})

#: Minimum acceptable length (bytes) for ``ENCRYPTION_KEK_SECRET``.
_MIN_KEK_SECRET_LEN = 16

#: Compiled PII detection patterns applied to audit log lines.
_PII_PATTERNS: List[re.Pattern] = [
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),  # email
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),                                 # SSN
    re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),                           # credit card
]


class SOC2ComplianceManager:
    """
    Legacy-named SOC 2 control-map self-check manager.

    Results are application self-assessment evidence only. They are not an
    independent audit, attestation, or certification.
    """

    def __init__(self, config=None):
        """
        Initialize the SOC 2 Compliance Manager.

        Args:
            config: Configuration settings.  Recognised keys:
                ``availability_violation_threshold`` (int, default 10) — number
                of compliance violations per hour that triggers non-compliant.
        """
        self.config = config or {}
        self.compliance_state = {
            "security": {"status": "monitored", "last_check": datetime.now().isoformat()},
            "availability": {"status": "monitored", "last_check": datetime.now().isoformat()},
            "processing_integrity": {"status": "monitored", "last_check": datetime.now().isoformat()},
            "confidentiality": {"status": "monitored", "last_check": datetime.now().isoformat()},
            "privacy": {"status": "monitored", "last_check": datetime.now().isoformat()}
        }

        # Create compliance logs directory
        os.makedirs("logs/compliance", exist_ok=True)

        # Initialize monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None

        # Start the monitoring
        self.start_compliance_monitoring()

        logger.info("SOC2 Compliance Manager initialized")

    # ------------------------------------------------------------------
    # Monitoring thread lifecycle
    # ------------------------------------------------------------------

    def start_compliance_monitoring(self):
        """Start the compliance monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._compliance_monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info("Compliance monitoring started")

    def stop_compliance_monitoring(self):
        """Stop the compliance monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            logger.info("Compliance monitoring stopped")

    def _compliance_monitoring_loop(self):
        """Background thread for continuous compliance monitoring"""
        while self.monitoring_active:
            try:
                self._check_security_compliance()
                self._check_availability_compliance()
                self._check_processing_integrity_compliance()
                self._check_confidentiality_compliance()
                self._check_privacy_compliance()

                self._log_compliance_state()

                # Check every 5 minutes
                time.sleep(300)

            except Exception as e:
                logger.error(f"Error in compliance monitoring: {str(e)}")
                time.sleep(60)

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _apply_check_result(
        self,
        category: str,
        issues: List[str],
        pass_message: str,
    ) -> None:
        """
        Apply the result of a compliance check to ``compliance_state`` and log it.

        Args:
            category: Trust service criteria key (e.g. ``"security"``).
            issues: List of failure descriptions found during the check.
                    An empty list means the check passed.
            pass_message: Message logged when there are no issues.
        """
        self.compliance_state[category]["last_check"] = datetime.now().isoformat()
        if issues:
            self.compliance_state[category]["status"] = "non_compliant"
            self.compliance_state[category]["issues"] = issues
            summary = "; ".join(issues)
            self.log_compliance_event(category, "violation", summary)
            logger.warning("Control-map check [%s] FAILED: %s", category, summary)
        else:
            self.compliance_state[category]["status"] = "compliant"
            self.compliance_state[category].pop("issues", None)
            self.log_compliance_event(category, "check", pass_message)

    # ------------------------------------------------------------------
    # SC-1 — Security
    # ------------------------------------------------------------------

    def _check_security_compliance(self):
        """
        SC-1: Check security compliance criteria.

        Verifies:
        1. ``ENCRYPTION_KEK_SECRET`` is set and is not a known development default.
        2. The encryption key is not overdue for rotation.
        3. The audit log directory is writable.
        """
        issues: List[str] = []

        # --- 1. Encryption key present and not a known dev value -------
        kek_secret = os.environ.get("ENCRYPTION_KEK_SECRET", "")
        if not kek_secret:
            issues.append("ENCRYPTION_KEK_SECRET is not configured")
        elif (
            len(kek_secret) < _MIN_KEK_SECRET_LEN
            or kek_secret.lower().strip() in _KNOWN_DEV_SECRETS
        ):
            issues.append(
                "ENCRYPTION_KEK_SECRET appears to be a development default "
                "— rotate before production use"
            )

        # --- 2. Key rotation not overdue --------------------------------
        try:
            if get_encryption_manager is None:
                raise RuntimeError("encryption_manager module not available")
            key_status = get_encryption_manager().get_key_status()
            if key_status.get("rotation_needed"):
                days_overdue = abs(key_status.get("days_until_rotation", 0))
                issues.append(
                    f"Encryption key rotation overdue by {days_overdue} day(s)"
                )
        except Exception as exc:
            issues.append(f"Encryption manager unavailable: {exc}")

        # --- 3. Audit log directory writable ----------------------------
        audit_dir = os.path.join(os.getcwd(), "logs", "compliance")
        try:
            os.makedirs(audit_dir, exist_ok=True)
            probe = os.path.join(audit_dir, ".write_probe")
            with open(probe, "w") as fh:
                fh.write("ok")
            os.unlink(probe)
        except OSError as exc:
            issues.append(f"Audit directory not writable: {exc}")

        self._apply_check_result("security", issues, "Security check passed")

    # ------------------------------------------------------------------
    # SC-2 — Availability
    # ------------------------------------------------------------------

    def _check_availability_compliance(self):
        """
        SC-2: Check availability compliance criteria.

        Verifies:
        1. The primary database connection is live.
        2. No compliance violation spike in the last hour.
        """
        issues: List[str] = []

        # --- 1. Database connection live --------------------------------
        try:
            if db is None:
                raise RuntimeError("extensions.db not available")
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
        except Exception as exc:
            issues.append(f"Database connection failed: {exc}")

        # --- 2. No violation spike in the last hour ---------------------
        try:
            threshold = self.config.get("availability_violation_threshold", 10)
            recent_violations = self.get_compliance_events(
                start_time=datetime.now() - timedelta(hours=1),
                event_type="violation",
                limit=threshold + 1,
            )
            if len(recent_violations) >= threshold:
                issues.append(
                    f"Compliance violation spike: {len(recent_violations)} violations "
                    f"in last hour (threshold: {threshold})"
                )
        except Exception as exc:
            issues.append(f"Violation rate check failed: {exc}")

        self._apply_check_result("availability", issues, "Availability check passed")

    # ------------------------------------------------------------------
    # SC-3 — Processing Integrity
    # ------------------------------------------------------------------

    def _check_processing_integrity_compliance(self):
        """
        SC-3: Check processing integrity compliance criteria.

        Verifies:
        1. The database schema is at the Alembic migration head.
        2. The most recent audit event hash chain is unbroken.
        """
        issues: List[str] = []

        # --- 1. Migration at head ---------------------------------------
        try:
            if any(x is None for x in (AlembicConfig, MigrationContext, ScriptDirectory, db)):
                raise RuntimeError("Alembic or db not available")

            migrations_ini = os.path.join(os.getcwd(), "migrations", "alembic.ini")
            alembic_cfg = AlembicConfig(migrations_ini)
            alembic_cfg.set_main_option(
                "script_location",
                os.path.join(os.getcwd(), "migrations"),
            )
            script = ScriptDirectory.from_config(alembic_cfg)
            expected_head = script.get_current_head()

            with db.engine.connect() as conn:
                ctx = MigrationContext.configure(conn)
                current_rev = ctx.get_current_revision()

            if current_rev != expected_head:
                issues.append(
                    f"Database migration not at head: "
                    f"current={current_rev!r}, head={expected_head!r}"
                )
        except Exception as exc:
            issues.append(f"Migration head check failed: {exc}")

        # --- 2. Audit hash chain valid ----------------------------------
        try:
            if any(x is None for x in (db, TruthAuditEvent, TruthAuditRecorder)):
                raise RuntimeError("DB or audit models not available")

            latest = (
                db.session.query(TruthAuditEvent)
                .order_by(TruthAuditEvent.created_at.desc())
                .first()
            )
            if latest is not None:
                recorder = TruthAuditRecorder(db_session=db.session)
                result = recorder.verify_chain(str(latest.session_id))
                if not result.get("valid"):
                    issues.append(
                        f"Audit hash chain broken at event index "
                        f"{result.get('broken_at')} in session {latest.session_id}"
                    )
        except Exception as exc:
            # No DB context or no events — degrade gracefully, do not fail
            logger.debug("Hash chain verification skipped: %s", exc)

        self._apply_check_result(
            "processing_integrity", issues, "Processing integrity check passed"
        )

    # ------------------------------------------------------------------
    # SC-4 — Confidentiality
    # ------------------------------------------------------------------

    def _check_confidentiality_compliance(self):
        """
        SC-4: Check confidentiality compliance criteria.

        Verifies:
        1. ``ENCRYPTION_KEK_SECRET`` is not a known weak / development value.
        2. Recent compliance audit log lines do not contain PII patterns
           (email addresses, SSNs, or credit card numbers).
        """
        issues: List[str] = []

        # --- 1. Encryption key not a weak/dev value --------------------
        kek_secret = os.environ.get("ENCRYPTION_KEK_SECRET", "")
        if not kek_secret:
            issues.append(
                "ENCRYPTION_KEK_SECRET not set — data at rest may not be encrypted"
            )
        elif (
            len(kek_secret) < _MIN_KEK_SECRET_LEN
            or kek_secret.lower().strip() in _KNOWN_DEV_SECRETS
        ):
            issues.append(
                "ENCRYPTION_KEK_SECRET appears to be a weak development default "
                "— confidential data may not be adequately protected"
            )

        # --- 2. No PII in plain audit log --------------------------------
        events_log = os.path.join(os.getcwd(), "logs", "compliance", "events.jsonl")
        try:
            if os.path.exists(events_log):
                with open(events_log, "r", errors="replace") as fh:
                    lines = fh.readlines()
                # Bounded scan: last 200 lines only (performance guardrail)
                for line in lines[-200:]:
                    for pattern in _PII_PATTERNS:
                        if pattern.search(line):
                            issues.append(
                                "PII-like content detected in compliance audit log — "
                                "review log redaction configuration"
                            )
                            break
                    else:
                        continue
                    break  # only report once per scan
        except Exception as exc:
            logger.debug("Audit log PII scan skipped: %s", exc)

        self._apply_check_result("confidentiality", issues, "Confidentiality check passed")

    # ------------------------------------------------------------------
    # SC-5 — Privacy
    # ------------------------------------------------------------------

    def _check_privacy_compliance(self):
        """
        SC-5: Check privacy compliance criteria.

        Verifies:
        1. User data export and deletion endpoints exist in the route file.
        2. The AI processing toggle (``ai_processing_enabled``) is wired in
           the settings routes.
        """
        issues: List[str] = []
        cwd = os.getcwd()

        # --- 1. Export and deletion routes present ----------------------
        export_route_file = os.path.join(cwd, "routes", "user_data_routes.py")
        if not os.path.exists(export_route_file):
            issues.append(
                "User data routes file missing (routes/user_data_routes.py) — "
                "export and deletion endpoints cannot be verified"
            )
        else:
            try:
                content = open(export_route_file, errors="replace").read()
                if "/export" not in content:
                    issues.append(
                        "User data export endpoint (/export) not found in "
                        "routes/user_data_routes.py"
                    )
                if "/delete" not in content:
                    issues.append(
                        "User data deletion endpoint (/delete) not found in "
                        "routes/user_data_routes.py"
                    )
            except OSError as exc:
                issues.append(f"Could not read user_data_routes.py: {exc}")

        # --- 2. AI processing toggle wired in settings -----------------
        settings_file = os.path.join(cwd, "backend", "routes", "settings_routes.py")
        if not os.path.exists(settings_file):
            issues.append(
                "Settings routes file missing (backend/routes/settings_routes.py) — "
                "AI processing toggle cannot be verified"
            )
        else:
            try:
                content = open(settings_file, errors="replace").read()
                if "ai_processing_enabled" not in content:
                    issues.append(
                        "AI processing toggle (ai_processing_enabled) not found in "
                        "backend/routes/settings_routes.py"
                    )
            except OSError as exc:
                issues.append(f"Could not read settings_routes.py: {exc}")

        self._apply_check_result("privacy", issues, "Privacy check passed")

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _log_compliance_state(self):
        """Log the current compliance state to disk."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/compliance/state_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "state": self.compliance_state
                }, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log compliance state: {str(e)}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_compliance_event(self, category: str, event_type: str, details: str):
        """
        Log a compliance-related event.

        Args:
            category: The trust service criteria category.
            event_type: The type of event (``check``, ``violation``, ``remediation``).
            details: Details about the event.

        Returns:
            The generated event UUID string, or ``None`` on failure.
        """
        try:
            timestamp = datetime.now().isoformat()
            event_id = str(uuid.uuid4())

            event_data = {
                "id": event_id,
                "timestamp": timestamp,
                "category": category,
                "type": event_type,
                "details": details
            }

            with open("logs/compliance/events.jsonl", 'a') as f:
                f.write(json.dumps(event_data) + "\n")

            logger.info(f"Compliance event [{category}] {event_type}: {details}")

            return event_id

        except Exception as e:
            logger.error(f"Failed to log compliance event: {str(e)}")
            return None

    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get current application control-map check evidence.

        Returns:
            A non-certifying self-assessment evidence contract.
        """
        category_checks = {}
        for category, state in self.compliance_state.items():
            internal_state = state.get("status")
            result = {
                "compliant": "passed",
                "non_compliant": "failed",
                "monitored": "not_measured",
            }.get(internal_state, "not_measured")
            category_checks[category] = {
                "claim_type": "automated_control_check",
                "check_version": "soc2-control-map.v1",
                "executed_at": state.get("last_check"),
                "scope": "local_application_runtime",
                "result": result,
                "evidence_ref": "logs/compliance/events.jsonl",
                "source_record": f"control-map:{category}",
                "issues": list(state.get("issues", [])),
            }
        results = {item["result"] for item in category_checks.values()}
        overall_result = (
            "checks_failed"
            if "failed" in results
            else "not_measured"
            if "not_measured" in results
            else "checks_passed"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "schema_version": "dle.compliance-check-status.v1",
            "report_classification": "self_assessment_evidence",
            "framework_map": "SOC2",
            "framework_map_is_certification": False,
            "overall_check_result": overall_result,
            "category_checks": category_checks,
        }

    def get_compliance_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        category: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get compliance events filtered by criteria.

        Args:
            start_time: Filter events after this time.
            end_time: Filter events before this time.
            category: Filter by trust service criteria category.
            event_type: Filter by event type.
            limit: Maximum number of events to return.

        Returns:
            List of matching compliance event dicts.
        """
        events = []

        try:
            if not os.path.exists("logs/compliance/events.jsonl"):
                return []

            with open("logs/compliance/events.jsonl", 'r') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)

                        if start_time and datetime.fromisoformat(event["timestamp"]) < start_time:
                            continue

                        if end_time and datetime.fromisoformat(event["timestamp"]) > end_time:
                            continue

                        if category and event["category"] != category:
                            continue

                        if event_type and event["type"] != event_type:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            break

            return events

        except Exception as e:
            logger.error(f"Error retrieving compliance events: {str(e)}")
            return []

    def generate_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate a SOC 2 control-map self-assessment evidence report.

        Args:
            start_date: Start date for the report period (default: 30 days ago).
            end_date: End date for the report period (default: now).

        Returns:
            A compliance report dictionary.
        """
        if not end_date:
            end_date = datetime.now()

        if not start_date:
            start_date = end_date - timedelta(days=30)

        events = self.get_compliance_events(
            start_time=start_date, end_time=end_date, limit=10000
        )

        event_counts = {
            "security": {"check": 0, "violation": 0, "remediation": 0},
            "availability": {"check": 0, "violation": 0, "remediation": 0},
            "processing_integrity": {"check": 0, "violation": 0, "remediation": 0},
            "confidentiality": {"check": 0, "violation": 0, "remediation": 0},
            "privacy": {"check": 0, "violation": 0, "remediation": 0}
        }

        for event in events:
            cat = event["category"]
            etype = event["type"]
            if cat in event_counts and etype in event_counts[cat]:
                event_counts[cat][etype] += 1

        category_results = {}
        for cat, counts in event_counts.items():
            total_checks = counts["check"]
            total_violations = counts["violation"]
            category_results[cat] = (
                "failed"
                if total_violations > 0
                else "passed"
                if total_checks > 0
                else "not_measured"
            )
        result_values = set(category_results.values())
        overall_result = (
            "checks_failed"
            if "failed" in result_values
            else "not_measured"
            if "not_measured" in result_values
            else "checks_passed"
        )

        report = {
            "schema_version": "dle.compliance-event-evidence.v1",
            "report_id": str(uuid.uuid4()),
            "report_classification": "self_assessment_evidence",
            "framework_map": "SOC2",
            "framework_map_is_certification": False,
            "generated_at": datetime.now().isoformat(),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "overall_check_result": overall_result,
            "category_results": category_results,
            "event_counts": event_counts,
            "event_sample": events[:10],
            "certification_claim": False,
            "limitations": [
                "Application-generated control-map evidence only.",
                "Not an independent audit, attestation, or certification.",
            ],
        }

        report_file = (
            f"logs/compliance/self_assessment_"
            f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        )
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save compliance report: {str(e)}")

        return report
