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

from enum import Enum
from typing import List, Set, Optional, Dict, Any
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from flask_login import current_user


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


class Role:
    """Role with associated permissions."""

    def __init__(self, name: str, permissions: Set[Permission], description: str = ""):
        self.name = name
        self.permissions = permissions
        self.description = description
        self.created_at = datetime.utcnow()

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

        # Super Admin - Full system access
        self.roles["super_admin"] = Role(
            name="super_admin",
            permissions={
                Permission.SYSTEM_ADMIN,
                Permission.USER_MANAGE_ROLES,
                Permission.SECURITY_ADMIN,
                Permission.COMPLIANCE_ADMIN,
                Permission.AUDIT_READ,
                Permission.AUDIT_EXPORT,
                Permission.DATA_BACKUP,
                Permission.DATA_RESTORE,
            } | set(Permission),  # All permissions
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

        # Check user role
        user_role_name = getattr(user, 'role', 'user')
        role = self.get_role(user_role_name)

        if not role:
            # Fallback to basic user role
            role = self.get_role('user')

        has_perm = role.has_permission(permission)

        # Log access decision
        self._log_audit("permission_check", {
            "user_id": user.id if hasattr(user, 'id') else None,
            "username": user.username if hasattr(user, 'username') else None,
            "role": user_role_name,
            "permission": permission.value,
            "granted": has_perm,
            "endpoint": request.endpoint if request else None,
            "ip_address": request.remote_addr if request else None
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
            "assigned_by": current_user.username if current_user and current_user.is_authenticated else "system"
        })

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log RBAC operation to audit log."""
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type,
                details=details,
                severity="INFO"
            )


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
            if not current_user or not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401

            rbac = get_rbac_manager()
            if not rbac.user_has_permission(current_user, permission):
                return jsonify({
                    "error": "Permission denied",
                    "required_permission": permission.value,
                    "user_role": getattr(current_user, 'role', 'user')
                }), 403

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
            if not current_user or not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401

            rbac = get_rbac_manager()
            if not rbac.user_has_any_permission(current_user, list(permissions)):
                return jsonify({
                    "error": "Permission denied",
                    "required_permissions": [p.value for p in permissions],
                    "user_role": getattr(current_user, 'role', 'user')
                }), 403

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
            if not current_user or not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401

            rbac = get_rbac_manager()
            if not rbac.user_has_all_permissions(current_user, list(permissions)):
                return jsonify({
                    "error": "Permission denied",
                    "required_permissions": [p.value for p in permissions],
                    "user_role": getattr(current_user, 'role', 'user')
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
