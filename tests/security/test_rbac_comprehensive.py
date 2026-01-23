"""
Comprehensive RBAC (Role-Based Access Control) Testing Suite

Tests for:
- Role management
- Permission checking
- RBAC decorators
- Role assignment
- Data access control
- Audit logging integration
- Edge cases and security scenarios
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.security.rbac import (
    Permission,
    Role,
    RBACManager,
    get_rbac_manager,
    require_permission,
    require_any_permission,
    require_all_permissions
)
from datetime import datetime, UTC


class TestPermissionEnum:
    """Test Permission enum"""

    def test_permission_enum_has_required_permissions(self):
        """Test that required permissions exist"""
        required_permissions = [
            'USER_READ', 'USER_WRITE', 'USER_DELETE',
            'UKG_READ', 'UKG_WRITE', 'UKG_ADMIN',
            'SIMULATION_EXECUTE', 'SECURITY_ADMIN',
            'AUDIT_READ', 'SYSTEM_ADMIN'
        ]

        for perm in required_permissions:
            assert hasattr(Permission, perm)

    def test_permission_values_are_strings(self):
        """Test permission values are properly formatted"""
        for perm in Permission:
            assert isinstance(perm.value, str)
            assert ':' in perm.value or perm.value.islower()


class TestRole:
    """Test Role class"""

    def test_role_initialization(self):
        """Test Role initialization"""
        permissions = {Permission.USER_READ, Permission.UKG_READ}
        role = Role(
            name="test_role",
            permissions=permissions,
            description="Test role description"
        )

        assert role.name == "test_role"
        assert role.permissions == permissions
        assert role.description == "Test role description"
        assert isinstance(role.created_at, datetime)

    def test_role_has_permission_true(self):
        """Test has_permission returns True for granted permission"""
        permissions = {Permission.USER_READ, Permission.UKG_READ}
        role = Role(name="test", permissions=permissions)

        assert role.has_permission(Permission.USER_READ) is True

    def test_role_has_permission_false(self):
        """Test has_permission returns False for missing permission"""
        permissions = {Permission.USER_READ}
        role = Role(name="test", permissions=permissions)

        assert role.has_permission(Permission.USER_DELETE) is False

    def test_role_add_permission(self):
        """Test adding permission to role"""
        role = Role(name="test", permissions=set())

        role.add_permission(Permission.USER_READ)

        assert Permission.USER_READ in role.permissions

    def test_role_remove_permission(self):
        """Test removing permission from role"""
        permissions = {Permission.USER_READ, Permission.UKG_READ}
        role = Role(name="test", permissions=permissions)

        role.remove_permission(Permission.USER_READ)

        assert Permission.USER_READ not in role.permissions
        assert Permission.UKG_READ in role.permissions

    def test_role_remove_nonexistent_permission(self):
        """Test removing nonexistent permission doesn't crash"""
        role = Role(name="test", permissions=set())

        # Should not raise exception
        role.remove_permission(Permission.USER_READ)

    def test_role_to_dict(self):
        """Test converting role to dictionary"""
        permissions = {Permission.USER_READ, Permission.UKG_READ}
        role = Role(
            name="test_role",
            permissions=permissions,
            description="Test description"
        )

        role_dict = role.to_dict()

        assert role_dict['name'] == "test_role"
        assert role_dict['description'] == "Test description"
        assert len(role_dict['permissions']) == 2
        assert role_dict['permission_count'] == 2
        assert 'created_at' in role_dict


class TestRBACManagerInitialization:
    """Test RBAC Manager initialization"""

    def test_rbac_manager_initializes_default_roles(self):
        """Test that default roles are created"""
        rbac = RBACManager()

        default_roles = [
            'owner', 'super_admin', 'admin', 'security_officer',
            'auditor', 'data_scientist', 'developer', 'analyst',
            'user', 'guest'
        ]

        for role_name in default_roles:
            assert role_name in rbac.roles

    def test_owner_role_has_all_permissions(self):
        """Test owner role has all permissions"""
        rbac = RBACManager()

        owner_role = rbac.get_role('owner')

        assert len(owner_role.permissions) == len(Permission)
        for perm in Permission:
            assert perm in owner_role.permissions

    def test_super_admin_role_has_all_permissions(self):
        """Test super_admin role has all permissions"""
        rbac = RBACManager()

        super_admin_role = rbac.get_role('super_admin')

        assert len(super_admin_role.permissions) == len(Permission)

    def test_admin_role_has_limited_permissions(self):
        """Test admin role has subset of permissions"""
        rbac = RBACManager()

        admin_role = rbac.get_role('admin')

        # Admin should have some but not all permissions
        assert len(admin_role.permissions) < len(Permission)
        assert Permission.USER_READ in admin_role.permissions
        assert Permission.UKG_ADMIN in admin_role.permissions

    def test_guest_role_has_minimal_permissions(self):
        """Test guest role has minimal permissions"""
        rbac = RBACManager()

        guest_role = rbac.get_role('guest')

        # Guest should have very limited permissions
        assert len(guest_role.permissions) <= 2
        assert Permission.UKG_READ in guest_role.permissions

    def test_security_officer_role_has_security_permissions(self):
        """Test security officer has security-focused permissions"""
        rbac = RBACManager()

        sec_officer_role = rbac.get_role('security_officer')

        assert Permission.SECURITY_ADMIN in sec_officer_role.permissions
        assert Permission.COMPLIANCE_ADMIN in sec_officer_role.permissions
        assert Permission.AUDIT_READ in sec_officer_role.permissions

    def test_auditor_role_has_read_only_permissions(self):
        """Test auditor has read-only permissions"""
        rbac = RBACManager()

        auditor_role = rbac.get_role('auditor')

        # Auditor should have read permissions
        assert Permission.AUDIT_READ in auditor_role.permissions
        assert Permission.USER_READ in auditor_role.permissions

        # Auditor should NOT have write/delete permissions
        assert Permission.USER_DELETE not in auditor_role.permissions
        assert Permission.SYSTEM_CONFIG_WRITE not in auditor_role.permissions


class TestRBACManagerRoleOperations:
    """Test RBAC Manager role CRUD operations"""

    def test_get_role_existing(self):
        """Test getting existing role"""
        rbac = RBACManager()

        role = rbac.get_role('admin')

        assert role is not None
        assert role.name == 'admin'

    def test_get_role_nonexistent(self):
        """Test getting nonexistent role returns None"""
        rbac = RBACManager()

        role = rbac.get_role('nonexistent')

        assert role is None

    def test_create_custom_role(self):
        """Test creating custom role"""
        rbac = RBACManager()
        permissions = {Permission.USER_READ, Permission.UKG_READ}

        role = rbac.create_role(
            name="custom_role",
            permissions=permissions,
            description="Custom test role"
        )

        assert role.name == "custom_role"
        assert role.permissions == permissions
        assert 'custom_role' in rbac.roles

    def test_create_duplicate_role_raises_error(self):
        """Test creating duplicate role raises ValueError"""
        rbac = RBACManager()

        with pytest.raises(ValueError, match="already exists"):
            rbac.create_role(
                name="admin",  # Already exists
                permissions={Permission.USER_READ}
            )

    def test_delete_custom_role(self):
        """Test deleting custom role"""
        rbac = RBACManager()

        # Create custom role
        rbac.create_role(name="temp_role", permissions={Permission.USER_READ})

        # Delete it
        rbac.delete_role("temp_role")

        assert 'temp_role' not in rbac.roles

    def test_delete_default_role_raises_error(self):
        """Test deleting default role raises ValueError"""
        rbac = RBACManager()

        with pytest.raises(ValueError, match="Cannot delete default role"):
            rbac.delete_role("admin")

    def test_delete_nonexistent_role_raises_error(self):
        """Test deleting nonexistent role raises ValueError"""
        rbac = RBACManager()

        with pytest.raises(ValueError, match="not found"):
            rbac.delete_role("nonexistent")

    def test_list_roles(self):
        """Test listing all roles"""
        rbac = RBACManager()

        roles_list = rbac.list_roles()

        assert len(roles_list) >= 10  # At least default roles
        assert all('name' in role for role in roles_list)
        assert all('permissions' in role for role in roles_list)


class TestRBACManagerPermissionChecking:
    """Test RBAC Manager permission checking"""

    def test_user_has_permission_admin_always_true(self):
        """Test admin user always has permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = True
        user.id = 1
        user.username = "admin"

        result = rbac.user_has_permission(user, Permission.SYSTEM_ADMIN)

        assert result is True

    def test_user_has_permission_with_correct_role(self):
        """Test user has permission when role grants it"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'security_officer'
        user.id = 1
        user.username = "sec_user"

        result = rbac.user_has_permission(user, Permission.SECURITY_ADMIN)

        assert result is True

    def test_user_has_permission_without_correct_role(self):
        """Test user denied when role doesn't grant permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'guest'
        user.id = 1
        user.username = "guest_user"

        result = rbac.user_has_permission(user, Permission.USER_DELETE)

        assert result is False

    def test_user_has_permission_unauthenticated_denied(self):
        """Test unauthenticated user is denied"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = False

        result = rbac.user_has_permission(user, Permission.USER_READ)

        assert result is False

    def test_user_has_permission_none_user_denied(self):
        """Test None user is denied"""
        rbac = RBACManager()

        result = rbac.user_has_permission(None, Permission.USER_READ)

        assert result is False

    def test_user_has_permission_fallback_to_default_role(self):
        """Test fallback to user role when role not found"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'nonexistent_role'
        user.id = 1
        user.username = "test_user"

        # Should fallback to 'user' role
        result = rbac.user_has_permission(user, Permission.UKG_READ)

        assert result is True  # user role has UKG_READ

    def test_user_has_any_permission_one_granted(self):
        """Test has_any returns True when one permission granted"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'analyst'
        user.id = 1
        user.username = "analyst_user"

        permissions = [
            Permission.USER_DELETE,  # Not granted
            Permission.UKG_READ,     # Granted
        ]

        result = rbac.user_has_any_permission(user, permissions)

        assert result is True

    def test_user_has_any_permission_none_granted(self):
        """Test has_any returns False when no permissions granted"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'guest'
        user.id = 1
        user.username = "guest_user"

        permissions = [
            Permission.USER_DELETE,
            Permission.SYSTEM_ADMIN,
        ]

        result = rbac.user_has_any_permission(user, permissions)

        assert result is False

    def test_user_has_all_permissions_all_granted(self):
        """Test has_all returns True when all permissions granted"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'security_officer'
        user.id = 1
        user.username = "sec_user"

        permissions = [
            Permission.SECURITY_READ,
            Permission.AUDIT_READ,
        ]

        result = rbac.user_has_all_permissions(user, permissions)

        assert result is True

    def test_user_has_all_permissions_some_missing(self):
        """Test has_all returns False when some permissions missing"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'analyst'
        user.id = 1
        user.username = "analyst_user"

        permissions = [
            Permission.UKG_READ,     # Granted
            Permission.USER_DELETE,  # Not granted
        ]

        result = rbac.user_has_all_permissions(user, permissions)

        assert result is False


class TestRBACManagerRoleAssignment:
    """Test role assignment"""

    @patch('backend.security.rbac.current_user')
    def test_assign_role_to_user(self, mock_current_user):
        """Test assigning role to user"""
        rbac = RBACManager()
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.role = "user"

        mock_current_user.is_authenticated = True
        mock_current_user.username = "admin"

        rbac.assign_role_to_user(user, "analyst")

        assert user.role == "analyst"

    def test_assign_nonexistent_role_raises_error(self):
        """Test assigning nonexistent role raises ValueError"""
        rbac = RBACManager()
        user = Mock()
        user.id = 1
        user.username = "test_user"

        with pytest.raises(ValueError, match="not found"):
            rbac.assign_role_to_user(user, "nonexistent_role")


class TestRBACManagerDataAccessControl:
    """Test data access control"""

    def test_check_data_access_no_tags_allowed(self):
        """Test data access with no tags is allowed"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.role = 'user'

        result = rbac.check_data_access(user, [])

        assert result is True

    def test_check_data_access_pii_denied_without_permission(self):
        """Test PII data denied without PRIVACY_READER permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'user'
        user.id = 1
        user.username = "user"

        result = rbac.check_data_access(user, ['PII:EMAIL'])

        assert result is False

    def test_check_data_access_pii_allowed_with_permission(self):
        """Test PII data allowed with PRIVACY_READER permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'security_officer'  # Has PRIVACY_READER
        user.id = 1
        user.username = "sec_user"

        result = rbac.check_data_access(user, ['PII:EMAIL'])

        assert result is True

    def test_check_data_access_secret_denied_without_permission(self):
        """Test SECRET data denied without SECURITY_ADMIN permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'analyst'
        user.id = 1
        user.username = "analyst"

        result = rbac.check_data_access(user, ['SECRET:API_KEY'])

        assert result is False

    def test_check_data_access_secret_allowed_with_permission(self):
        """Test SECRET data allowed with SECURITY_ADMIN permission"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'security_officer'  # Has SECURITY_ADMIN
        user.id = 1
        user.username = "sec_user"

        result = rbac.check_data_access(user, ['SECRET:API_KEY'])

        assert result is True

    def test_check_data_access_multiple_tags(self):
        """Test data access with multiple tags"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'security_officer'
        user.id = 1
        user.username = "sec_user"

        result = rbac.check_data_access(user, ['PII:EMAIL', 'SECRET:TOKEN'])

        # Security officer should have both permissions
        assert result is True


class TestRBACManagerAuditLogging:
    """Test audit logging integration"""

    def test_rbac_logs_role_creation(self):
        """Test role creation is logged"""
        mock_logger = Mock()
        rbac = RBACManager(audit_logger=mock_logger)

        rbac.create_role("test_role", {Permission.USER_READ}, "Test")

        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args
        assert call_args[1]['event_type'] == 'role_created'

    def test_rbac_logs_role_deletion(self):
        """Test role deletion is logged"""
        mock_logger = Mock()
        rbac = RBACManager(audit_logger=mock_logger)

        # Create and delete
        rbac.create_role("temp_role", {Permission.USER_READ})
        mock_logger.reset_mock()

        rbac.delete_role("temp_role")

        mock_logger.log_audit_event.assert_called_once()
        call_args = mock_logger.log_audit_event.call_args
        assert call_args[1]['event_type'] == 'role_deleted'

    @patch('backend.security.rbac.request')
    def test_rbac_logs_permission_checks(self, mock_request):
        """Test permission checks are logged"""
        mock_request.endpoint = '/test'
        mock_request.remote_addr = '127.0.0.1'

        mock_logger = Mock()
        rbac = RBACManager(audit_logger=mock_logger)

        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'user'
        user.id = 1
        user.username = "test_user"

        rbac.user_has_permission(user, Permission.USER_READ)

        mock_logger.log_audit_event.assert_called()
        call_args = mock_logger.log_audit_event.call_args
        assert call_args[1]['event_type'] == 'permission_check'
        assert call_args[1]['details']['user_id'] == 1

    @patch('backend.security.rbac.current_user')
    def test_rbac_logs_role_assignment(self, mock_current_user):
        """Test role assignment is logged"""
        mock_current_user.is_authenticated = True
        mock_current_user.username = "admin"

        mock_logger = Mock()
        rbac = RBACManager(audit_logger=mock_logger)

        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.role = "user"

        rbac.assign_role_to_user(user, "analyst")

        # Should log the assignment
        mock_logger.log_audit_event.assert_called()
        call_args = mock_logger.log_audit_event.call_args
        assert call_args[1]['event_type'] == 'role_assigned'

    def test_rbac_logs_data_access_denial(self):
        """Test data access denials are logged"""
        mock_logger = Mock()
        rbac = RBACManager(audit_logger=mock_logger)

        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'user'
        user.id = 1
        user.username = "user"

        rbac.check_data_access(user, ['PII:EMAIL'])

        # Should log the denial
        mock_logger.log_audit_event.assert_called()


class TestRBACManagerSingleton:
    """Test RBAC Manager singleton pattern"""

    def test_get_rbac_manager_returns_singleton(self):
        """Test get_rbac_manager returns same instance"""
        # Reset singleton
        import backend.security.rbac as rbac_module
        rbac_module._rbac_manager_instance = None

        manager1 = get_rbac_manager()
        manager2 = get_rbac_manager()

        assert manager1 is manager2

    def test_get_rbac_manager_with_audit_logger(self):
        """Test get_rbac_manager with audit logger"""
        # Reset singleton
        import backend.security.rbac as rbac_module
        rbac_module._rbac_manager_instance = None

        mock_logger = Mock()
        manager = get_rbac_manager(audit_logger=mock_logger)

        assert manager.audit_logger is mock_logger


class TestRequirePermissionDecorator:
    """Test require_permission decorator"""

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_allows_user_with_permission(self, mock_get_rbac, mock_current_user):
        """Test decorator allows user with permission"""
        mock_current_user.is_authenticated = True
        mock_rbac = Mock()
        mock_rbac.user_has_permission.return_value = True
        mock_get_rbac.return_value = mock_rbac

        @require_permission(Permission.USER_READ)
        def protected_func():
            return "success"

        result = protected_func()

        assert result == "success"

    @patch('backend.security.rbac.current_user')
    def test_decorator_denies_unauthenticated_user(self, mock_current_user):
        """Test decorator denies unauthenticated user"""
        mock_current_user.is_authenticated = False

        @require_permission(Permission.USER_READ)
        def protected_func():
            return "success"

        result, status_code = protected_func()

        assert status_code == 401
        assert 'error' in result.json

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_denies_user_without_permission(self, mock_get_rbac, mock_current_user):
        """Test decorator denies user without permission"""
        mock_current_user.is_authenticated = True
        mock_current_user.role = 'guest'

        mock_rbac = Mock()
        mock_rbac.user_has_permission.return_value = False
        mock_get_rbac.return_value = mock_rbac

        @require_permission(Permission.USER_DELETE)
        def protected_func():
            return "success"

        result, status_code = protected_func()

        assert status_code == 403
        assert 'Permission denied' in result.json['error']


class TestRequireAnyPermissionDecorator:
    """Test require_any_permission decorator"""

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_allows_user_with_one_permission(self, mock_get_rbac, mock_current_user):
        """Test decorator allows user with at least one permission"""
        mock_current_user.is_authenticated = True

        mock_rbac = Mock()
        mock_rbac.user_has_any_permission.return_value = True
        mock_get_rbac.return_value = mock_rbac

        @require_any_permission(Permission.USER_READ, Permission.USER_WRITE)
        def protected_func():
            return "success"

        result = protected_func()

        assert result == "success"

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_denies_user_without_any_permission(self, mock_get_rbac, mock_current_user):
        """Test decorator denies user without any required permission"""
        mock_current_user.is_authenticated = True

        mock_rbac = Mock()
        mock_rbac.user_has_any_permission.return_value = False
        mock_get_rbac.return_value = mock_rbac

        @require_any_permission(Permission.USER_DELETE, Permission.SYSTEM_ADMIN)
        def protected_func():
            return "success"

        result, status_code = protected_func()

        assert status_code == 403


class TestRequireAllPermissionsDecorator:
    """Test require_all_permissions decorator"""

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_allows_user_with_all_permissions(self, mock_get_rbac, mock_current_user):
        """Test decorator allows user with all required permissions"""
        mock_current_user.is_authenticated = True

        mock_rbac = Mock()
        mock_rbac.user_has_all_permissions.return_value = True
        mock_get_rbac.return_value = mock_rbac

        @require_all_permissions(Permission.SECURITY_READ, Permission.AUDIT_READ)
        def protected_func():
            return "success"

        result = protected_func()

        assert result == "success"

    @patch('backend.security.rbac.current_user')
    @patch('backend.security.rbac.get_rbac_manager')
    def test_decorator_denies_user_missing_some_permissions(self, mock_get_rbac, mock_current_user):
        """Test decorator denies user missing some permissions"""
        mock_current_user.is_authenticated = True

        mock_rbac = Mock()
        mock_rbac.user_has_all_permissions.return_value = False
        mock_get_rbac.return_value = mock_rbac

        @require_all_permissions(Permission.SECURITY_ADMIN, Permission.AUDIT_DELETE)
        def protected_func():
            return "success"

        result, status_code = protected_func()

        assert status_code == 403


class TestRBACEdgeCases:
    """Test RBAC edge cases and security scenarios"""

    def test_permission_revocation_during_session(self):
        """Test permission checking after role change"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'admin'
        user.id = 1
        user.username = "test_user"

        # Initially has permission
        assert rbac.user_has_permission(user, Permission.USER_WRITE) is True

        # Change role
        user.role = 'guest'

        # Should no longer have permission
        assert rbac.user_has_permission(user, Permission.USER_WRITE) is False

    def test_role_hierarchy_no_inheritance(self):
        """Test that roles don't inherit from each other"""
        rbac = RBACManager()

        # Admin and security_officer should have different permissions
        admin = rbac.get_role('admin')
        sec_officer = rbac.get_role('security_officer')

        # They should have some different permissions
        assert admin.permissions != sec_officer.permissions

    def test_least_privilege_principle_guest_role(self):
        """Test guest role follows least privilege principle"""
        rbac = RBACManager()
        guest_role = rbac.get_role('guest')

        # Guest should not have any write, delete, or admin permissions
        dangerous_permissions = [
            Permission.USER_DELETE,
            Permission.SYSTEM_ADMIN,
            Permission.SECURITY_ADMIN,
            Permission.DATA_DELETE,
            Permission.AUDIT_DELETE,
        ]

        for perm in dangerous_permissions:
            assert perm not in guest_role.permissions

    def test_separation_of_duties_auditor_role(self):
        """Test auditor role has read-only access (separation of duties)"""
        rbac = RBACManager()
        auditor_role = rbac.get_role('auditor')

        # Auditor should not have write/admin permissions
        write_permissions = [p for p in Permission if 'WRITE' in p.name or 'DELETE' in p.name or 'ADMIN' in p.name]

        for perm in write_permissions:
            assert perm not in auditor_role.permissions

    def test_concurrent_role_modification(self):
        """Test concurrent modifications to role permissions"""
        rbac = RBACManager()
        role = rbac.create_role("test_role", {Permission.USER_READ})

        # Simulate concurrent modifications
        role.add_permission(Permission.UKG_READ)
        role.add_permission(Permission.SIMULATION_READ)

        assert len(role.permissions) == 3

    def test_permission_check_without_request_context(self):
        """Test permission checking works without Flask request context"""
        rbac = RBACManager()
        user = Mock()
        user.is_authenticated = True
        user.is_admin = False
        user.role = 'user'
        user.id = 1
        user.username = "test"

        # Should not crash even without request context
        result = rbac.user_has_permission(user, Permission.USER_READ)

        assert isinstance(result, bool)

    def test_role_name_case_sensitivity(self):
        """Test role names are case-sensitive"""
        rbac = RBACManager()

        admin_role = rbac.get_role('admin')
        admin_upper = rbac.get_role('ADMIN')

        assert admin_role is not None
        assert admin_upper is None  # Case sensitive

    def test_empty_permissions_set(self):
        """Test role with no permissions"""
        rbac = RBACManager()
        role = rbac.create_role("empty_role", set())

        assert len(role.permissions) == 0
        assert not role.has_permission(Permission.USER_READ)


class TestRBACIntegration:
    """Integration tests for RBAC workflows"""

    @patch('backend.security.rbac.current_user')
    def test_complete_role_lifecycle(self, mock_current_user):
        """Test complete role creation, assignment, and deletion"""
        mock_current_user.is_authenticated = True
        mock_current_user.username = "admin"

        rbac = RBACManager()

        # Create role
        permissions = {Permission.UKG_READ, Permission.SIMULATION_READ}
        role = rbac.create_role("temp_role", permissions, "Temporary role")

        # Assign to user
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.is_authenticated = True
        user.is_admin = False

        rbac.assign_role_to_user(user, "temp_role")
        assert user.role == "temp_role"

        # Check permissions
        assert rbac.user_has_permission(user, Permission.UKG_READ) is True
        assert rbac.user_has_permission(user, Permission.USER_DELETE) is False

        # Delete role
        rbac.delete_role("temp_role")
        assert 'temp_role' not in rbac.roles

    def test_data_classification_workflow(self):
        """Test data access control workflow"""
        rbac = RBACManager()

        # Create users with different roles
        regular_user = Mock()
        regular_user.is_authenticated = True
        regular_user.is_admin = False
        regular_user.role = 'user'
        regular_user.id = 1
        regular_user.username = "user"

        security_officer = Mock()
        security_officer.is_authenticated = True
        security_officer.is_admin = False
        security_officer.role = 'security_officer'
        security_officer.id = 2
        security_officer.username = "sec_officer"

        # Test PII access
        pii_tags = ['PII:EMAIL', 'PII:PHONE']

        assert rbac.check_data_access(regular_user, pii_tags) is False
        assert rbac.check_data_access(security_officer, pii_tags) is True

        # Test SECRET access
        secret_tags = ['SECRET:API_KEY']

        assert rbac.check_data_access(regular_user, secret_tags) is False
        assert rbac.check_data_access(security_officer, secret_tags) is True
