"""
Zero Trust Architecture (ZTA) implementation.

This module implements comprehensive Zero Trust security controls:
- Never trust, always verify
- Least privilege access
- Assume breach
- Verify explicitly
- Continuous validation

Key Components:
- Trust scoring (user, device, context)
- Context-aware access control
- Continuous authentication
- Risk-based authorization
- Session validation

Compliance: NIST 800-207 (Zero Trust Architecture)
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import secrets
from user_agents import parse as parse_user_agent


class TrustLevel(Enum):
    """Trust levels for Zero Trust decisions."""
    UNTRUSTED = 0      # Block access
    LOW = 25           # Very limited access
    MEDIUM = 50        # Standard access
    HIGH = 75          # Elevated access
    VERIFIED = 100     # Full access

    def __ge__(self, other):
        if isinstance(other, TrustLevel):
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, TrustLevel):
            return self.value > other.value
        return NotImplemented


class RiskLevel(Enum):
    """Risk assessment levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DeviceFingerprint:
    """Device fingerprint for trust evaluation."""
    device_id: str
    user_agent: str
    ip_address: str
    os_family: str
    browser_family: str
    is_mobile: bool
    is_tablet: bool
    is_pc: bool
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "os_family": self.os_family,
            "browser_family": self.browser_family,
            "is_mobile": self.is_mobile,
            "is_tablet": self.is_tablet,
            "is_pc": self.is_pc,
            "screen_resolution": self.screen_resolution,
            "timezone": self.timezone,
            "language": self.language
        }


@dataclass
class AccessContext:
    """Context information for access decision."""
    user_id: str
    device: DeviceFingerprint
    location: Optional[Dict[str, Any]] = None
    time_of_day: Optional[int] = None  # Hour 0-23
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    network_type: Optional[str] = None  # corporate, vpn, public
    mfa_verified: bool = False
    last_auth_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "device": self.device.to_dict(),
            "location": self.location,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "network_type": self.network_type,
            "mfa_verified": self.mfa_verified,
            "last_auth_time": self.last_auth_time.isoformat() if self.last_auth_time else None
        }


class TrustScoreCalculator:
    """
    Calculate trust scores for Zero Trust decisions.

    Trust score is calculated from:
    - User behavior and history
    - Device trust level
    - Context (location, time, network)
    - Authentication strength
    """

    def __init__(self, audit_logger=None):
        self.audit_logger = audit_logger
        self.user_profiles_file = "data/security/zero_trust/user_profiles.json"
        self.device_registry_file = "data/security/zero_trust/device_registry.json"
        self.trust_policies_file = "data/security/zero_trust/trust_policies.json"

        os.makedirs("data/security/zero_trust", exist_ok=True)

        self.user_profiles = self._load_user_profiles()
        self.device_registry = self._load_device_registry()
        self.trust_policies = self._load_trust_policies()

    def _load_user_profiles(self) -> Dict[str, Any]:
        """Load user behavioral profiles."""
        if os.path.exists(self.user_profiles_file):
            with open(self.user_profiles_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_user_profiles(self):
        """Save user profiles."""
        with open(self.user_profiles_file, 'w') as f:
            json.dump(self.user_profiles, f, indent=2)

    def _load_device_registry(self) -> Dict[str, Any]:
        """Load device registry."""
        if os.path.exists(self.device_registry_file):
            with open(self.device_registry_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_device_registry(self):
        """Save device registry."""
        with open(self.device_registry_file, 'w') as f:
            json.dump(self.device_registry, f, indent=2)

    def _load_trust_policies(self) -> Dict[str, Any]:
        """Load trust policies."""
        if os.path.exists(self.trust_policies_file):
            with open(self.trust_policies_file, 'r') as f:
                return json.load(f)

        # Default trust policies
        return {
            "require_mfa_for_high_trust": True,
            "max_session_duration_hours": 8,
            "require_reauth_after_hours": 4,
            "block_unknown_devices": False,
            "require_known_location": False,
            "business_hours": {"start": 6, "end": 20},
            "allowed_countries": [],  # Empty = allow all
            "blocked_countries": [],
            "require_corporate_network": False
        }

    def calculate_trust_score(self, context: AccessContext) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate overall trust score (0-100).

        Args:
            context: Access context

        Returns:
            Tuple of (trust_score, score_breakdown)
        """
        scores = {}

        # User trust score (0-30 points)
        scores['user'] = self._calculate_user_trust_score(context.user_id)

        # Device trust score (0-25 points)
        scores['device'] = self._calculate_device_trust_score(context.device)

        # Context trust score (0-25 points)
        scores['context'] = self._calculate_context_trust_score(context)

        # Authentication strength (0-20 points)
        scores['auth'] = self._calculate_auth_trust_score(context)

        # Total score
        total_score = sum(scores.values())

        # Log trust calculation
        self._log_trust_calculation(context, total_score, scores)

        return total_score, scores

    def _calculate_user_trust_score(self, user_id: str) -> int:
        """Calculate user trust score based on behavior history."""
        if user_id not in self.user_profiles:
            # New user - medium trust
            return 15

        profile = self.user_profiles[user_id]
        score = 15  # Base score

        # Increase for account age
        if 'created_at' in profile:
            created = datetime.fromisoformat(profile['created_at'])
            days_old = (datetime.utcnow() - created).days
            if days_old > 365:
                score += 5
            elif days_old > 90:
                score += 3
            elif days_old > 30:
                score += 1

        # Decrease for recent security incidents
        if 'security_incidents' in profile:
            incidents = profile['security_incidents']
            recent_incidents = sum(
                1 for i in incidents
                if datetime.fromisoformat(i['timestamp']) > datetime.utcnow() - timedelta(days=30)
            )
            score -= min(recent_incidents * 5, 15)

        # Increase for consistent behavior
        if profile.get('behavior_consistent', False):
            score += 5

        # Increase for verified identity
        if profile.get('identity_verified', False):
            score += 5

        return max(0, min(30, score))

    def _calculate_device_trust_score(self, device: DeviceFingerprint) -> int:
        """Calculate device trust score."""
        score = 10  # Base score

        if device.device_id in self.device_registry:
            device_info = self.device_registry[device.device_id]

            # Known device bonus
            score += 5

            # First seen date
            if 'first_seen' in device_info:
                first_seen = datetime.fromisoformat(device_info['first_seen'])
                days_known = (datetime.utcnow() - first_seen).days
                if days_known > 90:
                    score += 5
                elif days_known > 30:
                    score += 3

            # Successful auth history
            if device_info.get('successful_auths', 0) > 10:
                score += 3

            # No recent failures
            if device_info.get('recent_failures', 0) == 0:
                score += 2
            else:
                score -= device_info.get('recent_failures', 0)
        else:
            # Unknown device - reduced trust
            score = 5

        return max(0, min(25, score))

    def _calculate_context_trust_score(self, context: AccessContext) -> int:
        """Calculate context trust score (location, time, network)."""
        score = 15  # Base score

        # Time-based trust
        if context.time_of_day is not None:
            policies = self.trust_policies
            business_hours = policies.get('business_hours', {'start': 6, 'end': 20})

            if business_hours['start'] <= context.time_of_day <= business_hours['end']:
                score += 3
            else:
                score -= 2  # After hours access is riskier

        # Network-based trust
        if context.network_type == 'corporate':
            score += 5
        elif context.network_type == 'vpn':
            score += 3
        elif context.network_type == 'public':
            score -= 3

        # Location-based trust
        if context.location:
            # Check if location matches user's known locations
            known_locations = self.user_profiles.get(context.user_id, {}).get('known_locations', [])
            if self._is_known_location(context.location, known_locations):
                score += 4
            else:
                score -= 2

        return max(0, min(25, score))

    def _calculate_auth_trust_score(self, context: AccessContext) -> int:
        """Calculate authentication strength score."""
        score = 5  # Base score

        # MFA verified
        if context.mfa_verified:
            score += 10

        # Recent authentication
        if context.last_auth_time:
            time_since_auth = datetime.utcnow() - context.last_auth_time
            if time_since_auth < timedelta(minutes=15):
                score += 5
            elif time_since_auth < timedelta(hours=1):
                score += 3
            elif time_since_auth > timedelta(hours=4):
                score -= 3

        return max(0, min(20, score))

    def _is_known_location(self, location: Dict[str, Any], known_locations: List[Dict[str, Any]]) -> bool:
        """Check if location is in known locations."""
        if not location or not known_locations:
            return False

        # Simple check - in production, use geolocation API
        country = location.get('country')
        city = location.get('city')

        for known in known_locations:
            if known.get('country') == country and known.get('city') == city:
                return True

        return False

    def get_trust_level(self, trust_score: int) -> TrustLevel:
        """Convert trust score to trust level."""
        if trust_score >= 80:
            return TrustLevel.VERIFIED
        elif trust_score >= 60:
            return TrustLevel.HIGH
        elif trust_score >= 40:
            return TrustLevel.MEDIUM
        elif trust_score >= 20:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED

    def register_device(self, user_id: str, device: DeviceFingerprint):
        """Register a new device."""
        if device.device_id not in self.device_registry:
            self.device_registry[device.device_id] = {
                "user_id": user_id,
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "successful_auths": 0,
                "recent_failures": 0,
                "device_info": device.to_dict()
            }
            self._save_device_registry()

            self._log_audit("device_registered", {
                "user_id": user_id,
                "device_id": device.device_id
            })

    def update_device_auth_success(self, device_id: str):
        """Update device on successful authentication."""
        if device_id in self.device_registry:
            self.device_registry[device_id]["last_seen"] = datetime.utcnow().isoformat()
            self.device_registry[device_id]["successful_auths"] = \
                self.device_registry[device_id].get("successful_auths", 0) + 1
            self.device_registry[device_id]["recent_failures"] = 0
            self._save_device_registry()

    def update_device_auth_failure(self, device_id: str):
        """Update device on failed authentication."""
        if device_id in self.device_registry:
            self.device_registry[device_id]["recent_failures"] = \
                self.device_registry[device_id].get("recent_failures", 0) + 1
            self._save_device_registry()

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "security_incidents": [],
                "known_locations": []
            }

        self.user_profiles[user_id].update(updates)
        self._save_user_profiles()

    def _log_trust_calculation(self, context: AccessContext, total_score: int, breakdown: Dict[str, int]):
        """Log trust score calculation."""
        self._log_audit("trust_score_calculated", {
            "user_id": context.user_id,
            "device_id": context.device.device_id,
            "total_score": total_score,
            "trust_level": self.get_trust_level(total_score).name,
            "breakdown": breakdown
        })

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log to audit logger."""
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type,
                details=details,
                severity="INFO"
            )


class ZeroTrustManager:
    """
    Zero Trust Architecture Manager.

    Implements:
    - Continuous verification
    - Context-aware access control
    - Risk-based authentication
    - Session validation
    - Least privilege enforcement
    """

    def __init__(self, audit_logger=None, rbac_manager=None):
        self.audit_logger = audit_logger
        self.rbac_manager = rbac_manager
        self.trust_calculator = TrustScoreCalculator(audit_logger=audit_logger)

        # Active sessions tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Risk assessment cache
        self.risk_cache: Dict[str, Tuple[RiskLevel, datetime]] = {}

    def create_device_fingerprint(
        self,
        user_agent: str,
        ip_address: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> DeviceFingerprint:
        """
        Create device fingerprint from request information.

        Args:
            user_agent: User-Agent header
            ip_address: Client IP address
            additional_info: Additional device info

        Returns:
            DeviceFingerprint object
        """
        # Parse user agent
        ua = parse_user_agent(user_agent)

        # Generate device ID from fingerprint components
        fingerprint_str = f"{user_agent}:{ip_address}"
        if additional_info:
            fingerprint_str += f":{json.dumps(additional_info, sort_keys=True)}"

        device_id = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

        return DeviceFingerprint(
            device_id=device_id,
            user_agent=user_agent,
            ip_address=ip_address,
            os_family=ua.os.family,
            browser_family=ua.browser.family,
            is_mobile=ua.is_mobile,
            is_tablet=ua.is_tablet,
            is_pc=ua.is_pc,
            screen_resolution=additional_info.get('screen_resolution') if additional_info else None,
            timezone=additional_info.get('timezone') if additional_info else None,
            language=additional_info.get('language') if additional_info else None
        )

    def evaluate_access_request(
        self,
        user_id: str,
        device: DeviceFingerprint,
        resource: str,
        action: str,
        context_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, RiskLevel, Dict[str, Any]]:
        """
        Evaluate Zero Trust access request.

        Args:
            user_id: User ID
            device: Device fingerprint
            resource: Resource being accessed
            action: Action being performed
            context_info: Additional context

        Returns:
            Tuple of (access_granted, risk_level, details)
        """
        # Build access context
        now = datetime.utcnow()
        context = AccessContext(
            user_id=user_id,
            device=device,
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            mfa_verified=context_info.get('mfa_verified', False) if context_info else False,
            last_auth_time=context_info.get('last_auth_time') if context_info else None,
            location=context_info.get('location') if context_info else None,
            network_type=context_info.get('network_type') if context_info else None
        )

        # Calculate trust score
        trust_score, score_breakdown = self.trust_calculator.calculate_trust_score(context)
        trust_level = self.trust_calculator.get_trust_level(trust_score)

        # Assess risk
        risk_level = self._assess_risk(context, resource, action, trust_score)

        # Make access decision
        access_granted = self._make_access_decision(
            trust_level,
            risk_level,
            resource,
            action
        )

        # Log decision
        self._log_access_decision(
            user_id=user_id,
            device_id=device.device_id,
            resource=resource,
            action=action,
            access_granted=access_granted,
            trust_score=trust_score,
            trust_level=trust_level.name,
            risk_level=risk_level.name,
            score_breakdown=score_breakdown
        )

        details = {
            "trust_score": trust_score,
            "trust_level": trust_level.name,
            "risk_level": risk_level.name,
            "score_breakdown": score_breakdown,
            "requires_mfa": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and not context.mfa_verified,
            "requires_reauth": self._requires_reauth(context)
        }

        return access_granted, risk_level, details

    def _assess_risk(
        self,
        context: AccessContext,
        resource: str,
        action: str,
        trust_score: int
    ) -> RiskLevel:
        """Assess risk level for access request."""

        # Base risk on resource sensitivity
        resource_risk = self._get_resource_risk(resource)

        # Adjust for action
        action_multiplier = self._get_action_risk_multiplier(action)

        # Adjust for context
        if not context.mfa_verified and trust_score < 60:
            resource_risk = min(resource_risk + 1, 4)

        if context.network_type == 'public':
            resource_risk = min(resource_risk + 1, 4)

        # Map to risk level
        risk_map = [
            RiskLevel.MINIMAL,
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL
        ]

        return risk_map[min(resource_risk, 4)]

    def _get_resource_risk(self, resource: str) -> int:
        """Get base risk level for resource (0-4)."""
        # High-risk resources
        if any(keyword in resource.lower() for keyword in ['admin', 'security', 'config', 'user', 'delete']):
            return 3

        # Medium-risk resources
        if any(keyword in resource.lower() for keyword in ['data', 'export', 'api', 'backup']):
            return 2

        # Low-risk resources
        return 1

    def _get_action_risk_multiplier(self, action: str) -> float:
        """Get risk multiplier for action."""
        high_risk_actions = ['delete', 'drop', 'destroy', 'admin', 'config']
        medium_risk_actions = ['write', 'update', 'create', 'modify']

        action_lower = action.lower()

        if any(keyword in action_lower for keyword in high_risk_actions):
            return 1.5
        elif any(keyword in action_lower for keyword in medium_risk_actions):
            return 1.2
        else:
            return 1.0

    def _make_access_decision(
        self,
        trust_level: TrustLevel,
        risk_level: RiskLevel,
        resource: str,
        action: str
    ) -> bool:
        """Make final access decision based on trust and risk."""

        # Critical risk requires VERIFIED trust
        if risk_level == RiskLevel.CRITICAL:
            return trust_level == TrustLevel.VERIFIED

        # High risk requires HIGH or VERIFIED trust
        if risk_level == RiskLevel.HIGH:
            return trust_level >= TrustLevel.HIGH

        # Medium risk requires MEDIUM or higher trust
        if risk_level == RiskLevel.MEDIUM:
            return trust_level >= TrustLevel.MEDIUM

        # Low risk requires at least LOW trust
        if risk_level == RiskLevel.LOW:
            return trust_level >= TrustLevel.LOW

        # Minimal risk requires not UNTRUSTED
        return trust_level != TrustLevel.UNTRUSTED

    def _requires_reauth(self, context: AccessContext) -> bool:
        """Check if re-authentication is required."""
        if not context.last_auth_time:
            return True

        time_since_auth = datetime.utcnow() - context.last_auth_time
        max_duration = timedelta(hours=self.trust_calculator.trust_policies.get('require_reauth_after_hours', 4))

        return time_since_auth > max_duration

    def validate_session(self, session_id: str, context: AccessContext) -> Tuple[bool, Dict[str, Any]]:
        """
        Continuously validate active session.

        Args:
            session_id: Session ID
            context: Current access context

        Returns:
            Tuple of (session_valid, validation_details)
        """
        if session_id not in self.active_sessions:
            return False, {"reason": "session_not_found"}

        session = self.active_sessions[session_id]

        # Check session expiration
        created_at = datetime.fromisoformat(session['created_at'])
        max_duration = timedelta(hours=8)
        if datetime.utcnow() - created_at > max_duration:
            self.invalidate_session(session_id)
            return False, {"reason": "session_expired"}

        # Check device consistency
        if session['device_id'] != context.device.device_id:
            self.invalidate_session(session_id)
            self._log_audit("session_hijack_detected", {
                "session_id": session_id,
                "expected_device": session['device_id'],
                "actual_device": context.device.device_id
            })
            return False, {"reason": "device_mismatch"}

        # Check for suspicious activity
        if self._detect_session_anomaly(session, context):
            self.invalidate_session(session_id)
            return False, {"reason": "anomaly_detected"}

        # Update session activity
        session['last_activity'] = datetime.utcnow().isoformat()
        session['activity_count'] = session.get('activity_count', 0) + 1

        return True, {"status": "valid"}

    def _detect_session_anomaly(self, session: Dict[str, Any], context: AccessContext) -> bool:
        """Detect anomalies in session behavior."""

        # Check for rapid location change (impossible travel)
        if 'last_location' in session and context.location:
            # In production, calculate distance and time
            # For now, just check if country changed rapidly
            if session['last_location'].get('country') != context.location.get('country'):
                last_activity = datetime.fromisoformat(session.get('last_activity', session['created_at']))
                if datetime.utcnow() - last_activity < timedelta(hours=1):
                    return True  # Impossible travel detected

        return False

    def create_session(self, user_id: str, device: DeviceFingerprint, context_info: Dict[str, Any]) -> str:
        """Create a new Zero Trust session."""
        session_id = secrets.token_urlsafe(32)

        self.active_sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "device_id": device.device_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "activity_count": 0,
            "mfa_verified": context_info.get('mfa_verified', False),
            "initial_trust_score": None,  # Set after first evaluation
            "last_location": context_info.get('location')
        }

        self._log_audit("session_created", {
            "session_id": session_id,
            "user_id": user_id,
            "device_id": device.device_id
        })

        return session_id

    def invalidate_session(self, session_id: str):
        """Invalidate a session."""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            self._log_audit("session_invalidated", {
                "session_id": session_id,
                "user_id": session.get('user_id'),
                "reason": "explicit_invalidation"
            })

    def get_session_metrics(self) -> Dict[str, Any]:
        """Get Zero Trust session metrics."""
        return {
            "active_sessions": len(self.active_sessions),
            "total_devices_registered": len(self.trust_calculator.device_registry),
            "total_users_profiled": len(self.trust_calculator.user_profiles)
        }

    def _log_access_decision(self, **kwargs):
        """Log access decision."""
        self._log_audit("zero_trust_access_decision", kwargs)

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log to audit logger."""
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type,
                details=details,
                severity="INFO"
            )


# Singleton instance
_zero_trust_manager_instance: Optional[ZeroTrustManager] = None


def get_zero_trust_manager(audit_logger=None, rbac_manager=None) -> ZeroTrustManager:
    """Get or create singleton Zero Trust manager instance."""
    global _zero_trust_manager_instance
    if _zero_trust_manager_instance is None:
        _zero_trust_manager_instance = ZeroTrustManager(
            audit_logger=audit_logger,
            rbac_manager=rbac_manager
        )
    return _zero_trust_manager_instance
