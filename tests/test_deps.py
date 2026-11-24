"""Unit tests for deps module (dependencies)."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.deps import current_user, require_roles, get_coworking, can_manage, ensure_can_manage
from app.config import Settings


class TestCurrentUser:
    """Tests for current_user dependency."""

    def test_current_user_success(self):
        """Test successful user retrieval from valid token."""
        with patch("app.deps.decode_token", return_value={"sub": "1"}):
            with patch("app.deps.call", return_value={"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"}):
                from fastapi.security import HTTPAuthorizationCredentials
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
                user = current_user(creds)
                assert user["id"] == 1
                assert user["email"] == "test@example.com"

    def test_current_user_no_credentials(self):
        """Test missing credentials raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            current_user(None)
        assert exc_info.value.status_code == 401
        assert "автентифікація" in exc_info.value.detail

    def test_current_user_invalid_token(self):
        """Test invalid token raises 401."""
        import jwt
        with patch("app.deps.decode_token", side_effect=jwt.PyJWTError("Invalid")):
            from fastapi.security import HTTPAuthorizationCredentials
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
            with pytest.raises(HTTPException) as exc_info:
                current_user(creds)
            assert exc_info.value.status_code == 401
            assert "Недійсний" in exc_info.value.detail

    def test_current_user_user_not_found(self):
        """Test user not found in DB raises 401."""
        with patch("app.deps.decode_token", return_value={"sub": "999"}):
            with patch("app.deps.call", return_value=None):
                from fastapi.security import HTTPAuthorizationCredentials
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
                with pytest.raises(HTTPException) as exc_info:
                    current_user(creds)
                assert exc_info.value.status_code == 401
                assert "не знайдено" in exc_info.value.detail

    def test_current_user_blocked(self):
        """Test blocked user raises 403."""
        with patch("app.deps.decode_token", return_value={"sub": "1"}):
            with patch("app.deps.call", return_value={"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": True, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"}):
                from fastapi.security import HTTPAuthorizationCredentials
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
                with pytest.raises(HTTPException) as exc_info:
                    current_user(creds)
                assert exc_info.value.status_code == 403
                assert "заблоковано" in exc_info.value.detail


class TestRequireRoles:
    """Tests for require_roles dependency factory."""

    def test_require_roles_admin_allows_admin(self):
        """Test admin role allowed for admin endpoint."""
        admin_user = {"id": 1, "role": "PlatformAdmin"}
        dep = require_roles("PlatformAdmin")
        result = dep(admin_user)
        assert result == admin_user

    def test_require_roles_manager_allows_manager(self):
        """Test manager role allowed for manager endpoint."""
        manager_user = {"id": 2, "role": "SpaceManager"}
        dep = require_roles("SpaceManager", "PlatformAdmin")
        result = dep(manager_user)
        assert result == manager_user

    def test_require_roles_client_forbidden(self):
        """Test client role forbidden for admin endpoint."""
        client_user = {"id": 3, "role": "Client"}
        dep = require_roles("PlatformAdmin")
        with pytest.raises(HTTPException) as exc_info:
            dep(client_user)
        assert exc_info.value.status_code == 403
        assert "прав" in exc_info.value.detail


class TestGetCoworking:
    """Tests for get_coworking dependency."""

    def test_get_coworking_success(self):
        """Test successful coworking retrieval."""
        with patch("app.deps.call", return_value={"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 5}):
            coworking = get_coworking(1)
            assert coworking["id"] == 1
            assert coworking["name"] == "Test"

    def test_get_coworking_not_found(self):
        """Test nonexistent coworking raises 404."""
        with patch("app.deps.call", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_coworking(999)
            assert exc_info.value.status_code == 404
            assert "не знайдено" in exc_info.value.detail


class TestCanManage:
    """Tests for can_manage function."""

    def test_can_manage_admin(self):
        """Test admin can manage any coworking."""
        admin_user = {"id": 1, "role": "PlatformAdmin"}
        coworking = {"id": 1, "manager_id": 5}
        assert can_manage(admin_user, coworking) is True

    def test_can_manage_manager_owner(self):
        """Test manager can manage their own coworking."""
        manager_user = {"id": 3, "role": "SpaceManager"}
        coworking = {"id": 1, "manager_id": 3}
        assert can_manage(manager_user, coworking) is True

    def test_can_manage_manager_not_owner(self):
        """Test manager cannot manage other's coworking."""
        manager_user = {"id": 3, "role": "SpaceManager"}
        coworking = {"id": 1, "manager_id": 5}
        assert can_manage(manager_user, coworking) is False

    def test_can_manage_client(self):
        """Test client cannot manage any coworking."""
        client_user = {"id": 4, "role": "Client"}
        coworking = {"id": 1, "manager_id": 3}
        assert can_manage(client_user, coworking) is False


class TestEnsureCanManage:
    """Tests for ensure_can_manage dependency."""

    def test_ensure_can_manage_admin(self):
        """Test admin can manage any coworking."""
        admin_user = {"id": 1, "role": "PlatformAdmin"}
        with patch("app.deps.get_coworking", return_value={"id": 1, "manager_id": 5}):
            result = ensure_can_manage(admin_user, 1)
            assert result["id"] == 1

    def test_ensure_can_manage_manager_owner(self):
        """Test manager can manage their own coworking."""
        manager_user = {"id": 3, "role": "SpaceManager"}
        with patch("app.deps.get_coworking", return_value={"id": 1, "manager_id": 3}):
            result = ensure_can_manage(manager_user, 1)
            assert result["id"] == 1

    def test_ensure_can_manage_manager_not_owner(self):
        """Test manager cannot manage other's coworking."""
        manager_user = {"id": 3, "role": "SpaceManager"}
        with patch("app.deps.get_coworking", return_value={"id": 1, "manager_id": 5}):
            with pytest.raises(HTTPException) as exc_info:
                ensure_can_manage(manager_user, 1)
            assert exc_info.value.status_code == 403
            assert "керуєте" in exc_info.value.detail

    def test_ensure_can_manage_client(self):
        """Test client cannot manage any coworking."""
        client_user = {"id": 4, "role": "Client"}
        with patch("app.deps.get_coworking", return_value={"id": 1, "manager_id": 3}):
            with pytest.raises(HTTPException) as exc_info:
                ensure_can_manage(client_user, 1)
            assert exc_info.value.status_code == 403