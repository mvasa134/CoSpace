"""Unit tests for users router endpoints."""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from app.main import app
from app.schemas import RoleName


class TestUsersMe:
    """Tests for GET /users/me"""

    def test_me_success(self, client, auth_headers, registered_user, mock_db):
        """Test getting current user profile."""
        mock_db.return_value = {"id": registered_user["id"], "email": registered_user["email"], "role": registered_user["role"], "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"}
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == registered_user["id"]
        assert data["email"] == registered_user["email"]
        assert data["role"] == registered_user["role"]

    def test_me_unauthorized(self, client):
        """Test getting profile without auth."""
        response = client.get("/users/me")

        assert response.status_code == 401


class TestUsersList:
    """Tests for GET /users (admin only)"""

    def test_list_users_admin(self, client, admin_headers, mock_db):
        """Test listing users as admin."""
        # Mock both usp_User_GetById (for current_user) and usp_User_List
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            [  # usp_User_List
                {"id": 1, "email": "user1@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
                {"id": 2, "email": "user2@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
            ],
        ]

        response = client.get("/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["email"] == "user1@example.com"

    def test_list_users_with_filters(self, client, admin_headers, mock_db):
        """Test listing users with role filter and search."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            [
                {"id": 1, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
            ],  # usp_User_List
        ]

        response = client.get("/users?role=SpaceManager&q=manager", headers=admin_headers)

        assert response.status_code == 200

    def test_list_users_pagination(self, client, admin_headers, mock_db):
        """Test listing users with pagination."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            [],  # usp_User_List
        ]

        response = client.get("/users?offset=10&page_size=20", headers=admin_headers)

        assert response.status_code == 200

    def test_list_users_forbidden_client(self, client, auth_headers):
        """Test listing users as non-admin (forbidden)."""
        response = client.get("/users", headers=auth_headers)

        assert response.status_code == 403

    def test_list_users_unauthorized(self, client):
        """Test listing users without auth."""
        response = client.get("/users")

        assert response.status_code == 401


class TestUsersGet:
    """Tests for GET /users/{user_id} (admin only)"""

    def test_get_user_admin(self, client, admin_headers, mock_db):
        """Test getting specific user as admin."""
        user_id = 1
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById (current_user)
            {"id": user_id, "email": "user@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById (target user)
        ]

        response = client.get(f"/users/{user_id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "user@example.com"

    def test_get_user_not_found(self, client, admin_headers, mock_db):
        """Test getting nonexistent user."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById (current_user)
            None,  # usp_User_GetById (target user not found)
        ]

        response = client.get("/users/999", headers=admin_headers)

        assert response.status_code == 404
        assert "не знайдено" in response.json()["detail"]

    def test_get_user_forbidden_client(self, client, auth_headers):
        """Test getting user as non-admin."""
        response = client.get("/users/1", headers=auth_headers)

        assert response.status_code == 403


class TestUsersSetRole:
    """Tests for PUT /users/{user_id}/role (admin only)"""

    def test_set_role_admin(self, client, admin_headers, mock_db):
        """Test changing user role as admin."""
        target_id = 1
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user from admin_headers
            None,  # usp_User_SetRole
            None,  # audit log call
        ]

        response = client.put(f"/users/{target_id}/role", json={"role": "SpaceManager"}, headers=admin_headers)

        assert response.status_code == 204

    def test_set_role_self_forbidden(self, client, admin_headers, mock_db):
        """Test admin cannot change their own role."""
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
        ]

        response = client.put(f"/users/{admin_id}/role", json={"role": "Client"}, headers=admin_headers)

        assert response.status_code == 400
        assert "власну роль" in response.json()["detail"]

    def test_set_role_invalid_role(self, client, auth_headers):
        """Test setting invalid role (client trying to access admin endpoint)."""
        response = client.put("/users/1/role", json={"role": "InvalidRole"}, headers=auth_headers)

        assert response.status_code == 403

    def test_set_role_forbidden_client(self, client, auth_headers):
        """Test setting role as non-admin."""
        response = client.put("/users/1/role", json={"role": "Client"}, headers=auth_headers)

        assert response.status_code == 403


class TestUsersSetBlocked:
    """Tests for PUT /users/{user_id}/blocked (admin only)"""

    def test_block_user_admin(self, client, admin_headers, mock_db):
        """Test blocking a user as admin."""
        target_id = 1
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            None,  # usp_User_SetBlocked
            None,  # audit log call
        ]

        response = client.put(f"/users/{target_id}/blocked", json={"is_blocked": True}, headers=admin_headers)

        assert response.status_code == 204

    def test_unblock_user_admin(self, client, admin_headers, mock_db):
        """Test unblocking a user as admin."""
        target_id = 1
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            None,  # usp_User_SetBlocked
            None,  # audit log call
        ]

        response = client.put(f"/users/{target_id}/blocked", json={"is_blocked": False}, headers=admin_headers)

        assert response.status_code == 204

    def test_block_self_forbidden(self, client, admin_headers, mock_db):
        """Test admin cannot block themselves."""
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
        ]

        response = client.put(f"/users/{admin_id}/blocked", json={"is_blocked": True}, headers=admin_headers)

        assert response.status_code == 400
        assert "себе" in response.json()["detail"]

    def test_block_forbidden_client(self, client, auth_headers):
        """Test blocking as non-admin."""
        response = client.put("/users/1/blocked", json={"is_blocked": True}, headers=auth_headers)

        assert response.status_code == 403


class TestUsersDelete:
    """Tests for DELETE /users/{user_id} (admin only)"""

    def test_delete_user_admin(self, client, admin_headers, mock_db):
        """Test deleting a user as admin."""
        target_id = 1
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            None,  # usp_User_Delete
            None,  # audit log call
        ]

        response = client.delete(f"/users/{target_id}", headers=admin_headers)

        assert response.status_code == 204

    def test_delete_self_forbidden(self, client, admin_headers, mock_db):
        """Test admin cannot delete themselves."""
        admin_id = 2
        mock_db.side_effect = [
            {"id": admin_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},
        ]

        response = client.delete(f"/users/{admin_id}", headers=admin_headers)

        assert response.status_code == 400
        assert "себе" in response.json()["detail"]

    def test_delete_forbidden_client(self, client, auth_headers):
        """Test deleting as non-admin."""
        response = client.delete("/users/1", headers=auth_headers)

        assert response.status_code == 403