"""Unit tests for audit router endpoints."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.main import app


class TestAuditList:
    """Tests for GET /audit"""

    def test_list_audit_admin(self, client, admin_headers, mock_db):
        """Test listing audit logs as admin."""
        audit_logs = [
            {"id": 1, "user_id": 1, "action": "login", "created_at": datetime.now(timezone.utc)},
            {"id": 2, "user_id": 2, "action": "booking.create", "created_at": datetime.now(timezone.utc)},
        ]
        # Mock both usp_User_GetById (for current_user) and usp_AuditLog_List
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            audit_logs,  # usp_AuditLog_List
        ]

        response = client.get("/audit", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["action"] == "login"

    def test_list_audit_with_filters(self, client, admin_headers, mock_db):
        """Test listing audit logs with filters."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            [],  # usp_AuditLog_List
        ]

        # Use datetime without timezone for URL params to avoid + encoding issue
        start = datetime.now(timezone.utc) - timedelta(days=7)
        end = datetime.now(timezone.utc)
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

        response = client.get(
            f"/audit?user_id=1&from={start_str}&to={end_str}&offset=0&page_size=50",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_list_audit_pagination(self, client, admin_headers, mock_db):
        """Test audit logs pagination."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # usp_User_GetById
            [],  # usp_AuditLog_List
        ]

        response = client.get("/audit?offset=100&page_size=200", headers=admin_headers)

        assert response.status_code == 200

    def test_list_audit_forbidden_non_admin(self, client, auth_headers):
        """Test listing audit logs as non-admin (forbidden)."""
        response = client.get("/audit", headers=auth_headers)

        assert response.status_code == 403

    def test_list_audit_forbidden_manager(self, client, manager_headers):
        """Test listing audit logs as manager (forbidden - admin only)."""
        response = client.get("/audit", headers=manager_headers)

        assert response.status_code == 403

    def test_list_audit_unauthorized(self, client):
        """Test listing audit logs without auth."""
        response = client.get("/audit")

        assert response.status_code == 401