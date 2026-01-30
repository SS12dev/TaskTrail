"""
Tests for admin authentication and authorization.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch, MagicMock
from app.dependencies_admin import (
    verify_admin_token,
    require_super_admin,
    check_permission,
    Permissions,
    get_role_permissions
)


def test_get_role_permissions():
    """Test that roles have correct default permissions."""
    # Super admin should have all permissions
    super_perms = get_role_permissions("super_admin")
    assert Permissions.VIEW_USERS in super_perms
    assert Permissions.DELETE_USERS in super_perms
    assert Permissions.MANAGE_API_KEYS in super_perms
    
    # Regular admin should have limited permissions
    admin_perms = get_role_permissions("admin")
    assert Permissions.VIEW_USERS in admin_perms
    assert Permissions.EDIT_USERS in admin_perms
    assert Permissions.DELETE_USERS not in admin_perms
    assert Permissions.MANAGE_API_KEYS not in admin_perms
    
    # Support should only have read permissions
    support_perms = get_role_permissions("support")
    assert Permissions.VIEW_USERS in support_perms
    assert Permissions.EDIT_USERS not in support_perms
    assert Permissions.DELETE_USERS not in support_perms


@pytest.mark.asyncio
async def test_verify_admin_token_valid():
    """Test admin token verification with valid token."""
    # Mock Firebase auth
    with patch('app.dependencies_admin.auth.verify_id_token') as mock_verify:
        with patch('app.dependencies_admin.get_firestore_client') as mock_db:
            # Setup mocks
            mock_verify.return_value = {
                "uid": "admin123",
                "email": "admin@tasktrail.com"
            }
            
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "role": "super_admin",
                "is_active": True,
                "permissions": get_role_permissions("super_admin")
            }
            mock_doc.reference.update = MagicMock()
            
            mock_db_client = MagicMock()
            mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db.return_value = mock_db_client
            
            # Create mock credentials
            credentials = Mock()
            credentials.credentials = "valid_token"
            
            # Test verification
            admin_info = await verify_admin_token(credentials)
            
            assert admin_info["uid"] == "admin123"
            assert admin_info["email"] == "admin@tasktrail.com"
            assert admin_info["role"] == "super_admin"


@pytest.mark.asyncio
async def test_verify_admin_token_not_admin():
    """Test that non-admin users are rejected."""
    with patch('app.dependencies_admin.auth.verify_id_token') as mock_verify:
        with patch('app.dependencies_admin.get_firestore_client') as mock_db:
            # Setup mocks - valid token but not in admins collection
            mock_verify.return_value = {
                "uid": "user123",
                "email": "user@tasktrail.com"
            }
            
            mock_doc = MagicMock()
            mock_doc.exists = False  # Not an admin
            
            mock_db_client = MagicMock()
            mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db.return_value = mock_db_client
            
            credentials = Mock()
            credentials.credentials = "valid_token"
            
            # Should raise 403
            with pytest.raises(HTTPException) as exc_info:
                await verify_admin_token(credentials)
            
            assert exc_info.value.status_code == 403
            assert "Admin privileges required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_admin_token_inactive():
    """Test that inactive admin accounts are rejected."""
    with patch('app.dependencies_admin.auth.verify_id_token') as mock_verify:
        with patch('app.dependencies_admin.get_firestore_client') as mock_db:
            # Setup mocks - admin but inactive
            mock_verify.return_value = {
                "uid": "admin123",
                "email": "admin@tasktrail.com"
            }
            
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "role": "admin",
                "is_active": False,  # Inactive
                "permissions": []
            }
            
            mock_db_client = MagicMock()
            mock_db_client.collection.return_value.document.return_value.get.return_value = mock_doc
            mock_db.return_value = mock_db_client
            
            credentials = Mock()
            credentials.credentials = "valid_token"
            
            # Should raise 403
            with pytest.raises(HTTPException) as exc_info:
                await verify_admin_token(credentials)
            
            assert exc_info.value.status_code == 403
            assert "inactive" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_require_super_admin():
    """Test super admin requirement."""
    # Test with super admin
    super_admin = {
        "uid": "admin123",
        "role": "super_admin",
        "permissions": []
    }
    result = await require_super_admin(super_admin)
    assert result == super_admin
    
    # Test with regular admin (should fail)
    regular_admin = {
        "uid": "admin456",
        "role": "admin",
        "permissions": []
    }
    with pytest.raises(HTTPException) as exc_info:
        await require_super_admin(regular_admin)
    
    assert exc_info.value.status_code == 403
    assert "Super admin" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_permission():
    """Test permission checking."""
    # Super admin should pass any permission check
    super_admin = {
        "uid": "admin123",
        "role": "super_admin",
        "permissions": get_role_permissions("super_admin")
    }
    result = await check_permission(Permissions.DELETE_USERS, super_admin)
    assert result == super_admin
    
    # Regular admin with permission should pass
    admin_with_perm = {
        "uid": "admin456",
        "role": "admin",
        "permissions": [Permissions.VIEW_USERS, Permissions.EDIT_USERS]
    }
    result = await check_permission(Permissions.VIEW_USERS, admin_with_perm)
    assert result == admin_with_perm
    
    # Regular admin without permission should fail
    admin_without_perm = {
        "uid": "admin789",
        "role": "admin",
        "permissions": [Permissions.VIEW_USERS]
    }
    with pytest.raises(HTTPException) as exc_info:
        await check_permission(Permissions.DELETE_USERS, admin_without_perm)
    
    assert exc_info.value.status_code == 403
    assert "Permission denied" in exc_info.value.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
