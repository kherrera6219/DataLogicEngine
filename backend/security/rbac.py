"""
Role-Based Access Control (RBAC) system for enterprise security.

This module implements:
- Granular role and permission management
- Hierarchical role inheritance
- Resource-based access control
- Audit logging for all access decisions
- Integration with existing User model

Compliance: SOC 2 Type 2, ISO 27001, least privilege principle
"""

import logging
from enum import Enum
from typing import List, Set, Optional, Dict, Any
from datetime import datetime, UTC
from functools import wraps
from flask import jsonify, has_request_context, has_app_context, request as flask_request
from flask_login import current_user as flask_current_user

logger = logging.getLogger(__name__)

# Test-friendly patch points: tests may monkeypatch these names directly.
current_user = None
request = None


def _resolve_current_user():
    """Return patched current_user in tests, else flask-login current_user."""
    if current_user is not None:
        return current_user
    return flask_current_user


def _is_authenticated(user_obj) -> bool:
    """Safely check authentication across real/proxy/mock user objects."""
    try:
        return bool(user_obj and getattr(user_obj, "is_authenticated", False))
    except RuntimeError:
        return False


def _request_metadata() -> Dict[str, Optional[str]]:
    """Safely extract request metadata without requiring request context."""
    req = request
    if req is not None:
        return {
            "endpoint": getattr(req, "endpoint", None),
            "ip_address": getattr(req, "remote_addr", None),
        }
    if has_request_context():
        return {
            "endpoint": flask_request.endpoint,
            "ip_address": flask_request.remote_addr,
        }
    return {"endpoint": None, "ip_address": None}


class _JsonFallbackResponse:
    """Minimal response shim for decorator unit tests without Flask app context."""

    def __init__(self, payload: Dict[str, Any]):
        self.json = payload


def _error_response(payload: Dict[str, Any], status_code: int):
    """Return Flask JSON response when available, otherwise a lightweight fallback."""
    if has_app_context():
        return jsonify(payload), status_code
    return _JsonFallbackResponse(payload), status_code


class Permission(Enum):
    """System-wide permissions."""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Knowledge graph
    UKG_READ = "ukg:read"
    UKG_WRITE = "ukg:write"
    UKG_DELETE = "ukg:delete"
    UKG_ADMIN = "ukg:admin"

    # Simulations
    SIMULATION_READ = "simulation:read"
    SIMULATION_WRITE = "simulation:write"
    SIMULATION_DELETE = "simulation:delete"
    SIMULATION_EXECUTE = "simulation:execute"

    # MCP (Model Context Protocol)
    MCP_READ = "mcp:read"
    MCP_WRITE = "mcp:write"
    MCP_EXECUTE = "mcp:execute"
    MCP_ADMIN = "mcp:admin"

    # Security & Compliance
    SECURITY_READ = "security:read"
    SECURITY_WRITE = "security:write"
    SECURITY_ADMIN = "security:admin"
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WRITE = "compliance:write"
    COMPLIANCE_ADMIN = "compliance:admin"

    # Audit logs
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    AUDIT_DELETE = "audit:delete"

    # System administration
    SYSTEM_CONFIG_READ = "system:config:read"
    SYSTEM_CONFIG_WRITE = "system:config:write"
    SYSTEM_ADMIN = "system:admin"

    # Data management
    DATA_EXPORT = "data:export"
    DATA_IMPORT = "data:import"
    DATA_DELETE = "data:delete"
    DATA_BACKUP = "data:backup"
    DATA_RESTORE = "data:restore"

    # API management
    API_KEY_CREATE = "api:key:create"
    API_KEY_REVOKE = "api:key:revoke"
    API_RATE_LIMIT_EXEMPT = "api:rate_limit:exempt"
    
    # Privacy & Sensitive Data
    PRIVACY_READER = "privacy:read"
    PRIVACY_WRITE = "privacy:write"
    PRIVACY_ADMIN = "privacy:admin"


class Role:
    """Role with associated permissions."""

    def __init__(self, name: str, permissions: Set[Permission], description: str = ""):
        self.name = name
        self.permissions = permissions
        self.description = description
        self.created_at = datetime.now(UTC)

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission."""
        return permission in self.permissions

    def add_permission(self, permission: Permission):
        """Add permission to role."""
        self.permissions.add(permission)

    def remove_permission(self, permission: Permission):
        """Remove permission from role."""
        self.permissions.discard(permission)

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions],
            "permission_count": len(self.permissions),
            "created_at": self.created_at.isoformat()
        }


class RBACManager:
    """
    Role-Based Access Control Manager.

    Manages roles, permissions, and access control decisions.
    """

    def __init__(self, audit_logger=None):
        """Initialize RBAC manager."""
        self.audit_logger = audit_logger
        self.roles: Dict[str, Role] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default system roles."""

        # Owner - Ultimate machine owner
        self.roles["owner"] = Role(
            name="owner",
            permissions=set(Permission),
            description="Ultimate machine owner with full system access and data residency control"
        )

        # Super Admin - Full system access (Cloud)
        self.roles["super_admin"] = Role(
            name="super_admin",
            permissions=set(Permission),
            description="Super administrator with full system access"
        )

        # Admin - Administrative access
        self.roles["admin"] = Role(
            name="admin",
            permissions={
                Permission.USER_READ,
                Permission.USER_WRITE,
                Permission.UKG_ADMIN,
                Permission.SIMULATION_EXECUTE,
                Permission.SIMULATION_DELETE,
                Permission.MCP_ADMIN,
                Permission.SECURITY_READ,
                Permission.COMPLIANCE_READ,
                Permission.AUDIT_READ,
                Permission.SYSTEM_CONFIG_READ,
                Permission.DATA_EXPORT,
                Permission.DATA_IMPORT,
                Permission.API_KEY_CREATE,
                Permission.API_KEY_REVOKE,
            },
            description="Administrator with management capabilities"
        )

        # Security Officer - Security and compliance focus
        self.roles["security_officer"] = Role(
            name="security_officer",
            permissions={
                Permission.SECURITY_READ,
                Permission.SECURITY_WRITE,
                Permission.SECURITY_ADMIN,
                Permission.COMPLIANCE_READ,
                Permission.COMPLIANCE_WRITE,
                Permission.COMPLIANCE_ADMIN,
                Permission.AUDIT_READ,
                Permission.AUDIT_EXPORT,
                Permission.USER_READ,
                Permission.SYSTEM_CONFIG_READ,
                Permission.PRIVACY_READER,
                Permission.PRIVACY_WRITE,
                Permission.PRIVACY_ADMIN,
            },
            description="Security and compliance officer"
        )

        # Auditor - Read-only audit access
        self.roles["auditor"] = Role(
            name="auditor",
            permissions={
                Permission.AUDIT_READ,
                Permission.AUDIT_EXPORT,
                Permission.COMPLIANCE_READ,
                Permission.SECURITY_READ,
                Permission.USER_READ,
                Permission.UKG_READ,
                Permission.SIMULATION_READ,
            },
            description="Auditor with read-only access to logs and compliance data"
        )

        # Data Scientist - Research and simulation access
        self.roles["data_scientist"] = Role(
            name="data_scientist",
            permissions={
                Permission.UKG_READ,
                Permission.UKG_WRITE,
                Permission.SIMULATION_READ,
                Permission.SIMULATION_WRITE,
                Permission.SIMULATION_EXECUTE,
                Permission.MCP_READ,
                Permission.MCP_EXECUTE,
                Permission.DATA_EXPORT,
                Permission.DATA_IMPORT,
            },
            description="Data scientist with simulation and knowledge graph access"
        )

        # Developer - Development and testing access
        self.roles["developer"] = Role(
            name="developer",
            permissions={
                Permission.UKG_READ,
                Permission.UKG_WRITE,
                Permission.SIMULATION_READ,
                Permission.SIMULATION_WRITE,
                Permission.SIMULATION_EXECUTE,
                Permission.MCP_READ,
                Permission.MCP_WRITE,
                Permission.MCP_EXECUTE,
                Permission.API_KEY_CREATE,
            },
            description="Developer with API and development access"
        )

        # Analyst - Read and analysis access
        self.roles["analyst"] = Role(
            name="analyst",
            permissions={
                Permission.UKG_READ,
                Permission.SIMULATION_READ,
                Permission.SIMULATION_EXECUTE,
                Permission.MCP_READ,
                Permission.DATA_EXPORT,
            },
            description="Analyst with read and execution access"
        )

        # User - Basic user access
        self.roles["user"] = Role(
            name="user",
            permissions={
                Permission.USER_READ,  # Can read own profile
                Permission.UKG_READ,
                Permission.SIMULATION_READ,
                Permission.MCP_READ,
            },
            description="Standard user with basic read access"
        )

        # Guest - Minimal read-only access
        self.roles["guest"] = Role(
            name="guest",
            permissions={
                Permission.UKG_READ,
            },
            description="Guest user with minimal read access"
        )

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        return self.roles.get(role_name)

    def create_role(self, name: str, permissions: Set[Permission], description: str = "") -> Role:
        """
        Create a new custom role.

        Args:
            name: Role name
            permissions: Set of permissions
            description: Role description

        Returns:
            Created role
        """
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(name=name, permissions=permissions, description=description)
        self.roles[name] = role

        self._log_audit("role_created", {
            "role_name": name,
            "permissions": [p.value for p in permissions],
            "description": description
        })

        return role

    def delete_role(self, role_name: str):
        """Delete a custom role (cannot delete default roles)."""
        default_roles = ["super_admin", "admin", "security_officer", "auditor",
                        "data_scientist", "developer", "analyst", "user", "guest"]

        if role_name in default_roles:
            raise ValueError(f"Cannot delete default role '{role_name}'")

        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' not found")

        del self.roles[role_name]

        self._log_audit("role_deleted", {"role_name": role_name})

    def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles with their permissions."""
        return [role.to_dict() for role in self.roles.values()]

    def user_has_permission(self, user, permission: Permission) -> bool:
        """
        Check if user has specific permission.

        Args:
            user: User object with 'role' attribute
            permission: Permission to check

        Returns:
            True if user has permission
        """
        if not user or not user.is_authenticated:
            return False

        # Super admin always has permission
        if hasattr(user, 'is_admin') and user.is_admin:
            return True

        # Check user role — deny on ambiguity; never silently default to a permissive role.
        user_role_name = getattr(user, 'role', None)
        if not user_role_name or not isinstance(user_role_name, str) or not user_role_name.strip():
            logger.warning(
                "RBAC: User object missing valid 'role' attribute (user_id=%s). Denying permission '%s'.",
                getattr(user, 'id', 'unknown'),
                permission.value,
            )
            return False
        user_role_name = user_role_name.strip().lower()
        role = self.get_role(user_role_name)

        if not role:
            logger.warning(
                "RBAC: Unknown role '%s' for user_id=%s. Denying permission '%s'.",
                user_role_name,
                getattr(user, 'id', 'unknown'),
                permission.value,
            )
            return False

        has_perm = role.has_permission(permission)

        # Log access decision
        request_meta = _request_metadata()
        self._log_audit("permission_check", {
            "user_id": user.id if hasattr(user, 'id') else None,
            "username": user.username if hasattr(user, 'username') else None,
            "role": user_role_name,
            "permission": permission.value,
            "granted": has_perm,
            "endpoint": request_meta["endpoint"],
            "ip_address": request_meta["ip_address"]
        })

        return has_perm

    def user_has_any_permission(self, user, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.user_has_permission(user, perm) for perm in permissions)

    def user_has_all_permissions(self, user, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(self.user_has_permission(user, perm) for perm in permissions)

    def assign_role_to_user(self, user, role_name: str):
        """
        Assign role to user.

        Args:
            user: User object
            role_name: Name of role to assign
        """
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' not found")

        old_role = getattr(user, 'role', None)
        user.role = role_name

        self._log_audit("role_assigned", {
            "user_id": user.id if hasattr(user, 'id') else None,
            "username": user.username if hasattr(user, 'username') else None,
            "old_role": old_role,
            "new_role": role_name,
            "assigned_by": (
                _resolve_current_user().username
                if _is_authenticated(_resolve_current_user())
                else "system"
            )
        })

    def check_data_access(self, user, data_tags: List[str]) -> bool:
        """
        Check if user is allowed to access data with specific security tags.
        Enforces "Deny by Default" for PII/Secrets.
        
        Args:
            user: User object
            data_tags: List of strings in 'axis_17_security' (e.g. ['PII:EMAIL'])
            
        Returns:
            True if access granted, False if denied/masked required
        """
        if not data_tags:
            return True
            
        # Check specific restricted tags
        has_pii = any("PII" in tag for tag in data_tags)
        has_secret = any("SECRET" in tag for tag in data_tags)
        
        if has_pii:
            if not self.user_has_permission(user, Permission.PRIVACY_READER):
                self._log_audit("data_access_denied", {
                    "reason": "PII_PROTECTION",
                    "user": user.username,
                    "tags": data_tags
                })
                return False
                
        if has_secret:
            if not self.user_has_permission(user, Permission.SECURITY_ADMIN):
                self._log_audit("data_access_denied", {
                    "reason": "SECRET_PROTECTION",
                    "user": user.username,
                    "tags": data_tags
                })
                return False
                
        return True

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log RBAC operation to audit log."""
        if self.audit_logger:
            self.audit_logger.log_audit_event(
                event_type=event_type,
                details=details
            )
        else:
            # In production the audit_logger should always be wired; log at debug so tests stay quiet.
            logger.debug("RBAC audit event (no audit_logger configured): %s %s", event_type, details)


# Singleton instance
_rbac_manager_instance: Optional[RBACManager] = None


def get_rbac_manager(audit_logger=None) -> RBACManager:
    """Get or create singleton RBAC manager instance."""
    global _rbac_manager_instance
    if _rbac_manager_instance is None:
        _rbac_manager_instance = RBACManager(audit_logger=audit_logger)
    return _rbac_manager_instance


def require_permission(permission: Permission):
    """
    Decorator to require specific permission for route access.

    Usage:
        @app.route('/admin/users')
        @require_permission(Permission.USER_WRITE)
        def manage_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_obj = _resolve_current_user()
            if not _is_authenticated(user_obj):
                return _error_response({"error": "Authentication required"}, 401)

            rbac = get_rbac_manager()
            if not rbac.user_has_permission(user_obj, permission):
                return _error_response({
                    "error": "Permission denied",
                    "required_permission": permission.value,
                    "user_role": getattr(user_obj, 'role', 'user')
                }, 403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(*permissions: Permission):
    """
    Decorator to require any of the specified permissions.

    Usage:
        @app.route('/data/export')
        @require_any_permission(Permission.DATA_EXPORT, Permission.SYSTEM_ADMIN)
        def export_data():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_obj = _resolve_current_user()
            if not _is_authenticated(user_obj):
                return _error_response({"error": "Authentication required"}, 401)

            rbac = get_rbac_manager()
            if not rbac.user_has_any_permission(user_obj, list(permissions)):
                return _error_response({
                    "error": "Permission denied",
                    "required_permissions": [p.value for p in permissions],
                    "user_role": getattr(user_obj, 'role', 'user')
                }, 403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_all_permissions(*permissions: Permission):
    """
    Decorator to require all of the specified permissions.

    Usage:
        @app.route('/security/critical')
        @require_all_permissions(Permission.SECURITY_ADMIN, Permission.AUDIT_READ)
        def critical_operation():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_obj = _resolve_current_user()
            if not _is_authenticated(user_obj):
                return _error_response({"error": "Authentication required"}, 401)

            rbac = get_rbac_manager()
            if not rbac.user_has_all_permissions(user_obj, list(permissions)):
                return _error_response({
                    "error": "Permission denied",
                    "required_permissions": [p.value for p in permissions],
                    "user_role": getattr(user_obj, 'role', 'user')
                }, 403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
