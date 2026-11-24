"""Unit tests for coworkings router endpoints."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from app.main import app


class TestCoworkingsList:
    """Tests for GET /coworkings"""

    def test_list_coworkings_public(self, client, mock_db):
        """Test listing coworkings (public endpoint)."""
        mock_db.return_value = [
            {"id": 1, "name": "Coworking 1", "address": "Addr 1", "amenities": "WiFi", "manager_id": 1, "workspace_count": 5},
            {"id": 2, "name": "Coworking 2", "address": "Addr 2", "amenities": "Coffee", "manager_id": 2, "workspace_count": 3},
        ]

        response = client.get("/coworkings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_coworkings_with_filters(self, client, mock_db):
        """Test listing coworkings with query params."""
        mock_db.return_value = []

        response = client.get("/coworkings?q=test&manager_id=1&offset=0&page_size=10")

        assert response.status_code == 200


class TestCoworkingsCreate:
    """Tests for POST /coworkings"""

    def test_create_coworking_manager(self, client, manager_headers, mock_db, sample_coworking):
        """Test creating coworking as SpaceManager (manager_id = self)."""
        manager_id = 3
        created_coworking = {"id": 1, **sample_coworking, "manager_id": manager_id}
        mock_db.side_effect = [
            {"id": manager_id, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            created_coworking,  # usp_Coworking_Create
            None,  # audit
        ]

        response = client.post(
            "/coworkings",
            json={"name": "New Coworking", "address": "123 St", "amenities": "WiFi"},
            headers=manager_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_coworking["name"]
        assert data["manager_id"] == manager_id

    def test_create_coworking_admin_with_manager(self, client, admin_headers, mock_db, sample_coworking):
        """Test creating coworking as Admin with specific manager_id."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user (from Staff dependency)
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # _check_manager_user
            {"id": 1, **sample_coworking, "manager_id": 3},  # usp_Coworking_Create
            None,  # audit
        ]

        response = client.post(
            "/coworkings",
            json={"name": "New Coworking", "address": "123 St", "amenities": "WiFi", "manager_id": 3},
            headers=admin_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["manager_id"] == 3

    def test_create_coworking_admin_invalid_manager(self, client, admin_headers, mock_db):
        """Test creating coworking as Admin with invalid manager."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 999, "email": "user@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # _check_manager_user - not a manager
        ]

        response = client.post(
            "/coworkings",
            json={"name": "New", "address": "Addr", "manager_id": 999},
            headers=admin_headers
        )

        assert response.status_code == 400
        assert "Менеджером може бути" in response.json()["detail"]

    def test_create_coworking_forbidden_client(self, client, auth_headers):
        """Test creating coworking as Client (forbidden)."""
        response = client.post(
            "/coworkings",
            json={"name": "New", "address": "Addr"},
            headers=auth_headers
        )

        assert response.status_code == 403


class TestCoworkingsGet:
    """Tests for GET /coworkings/{coworking_id}"""

    def test_get_coworking(self, client, mock_db, sample_coworking):
        """Test getting a specific coworking."""
        mock_db.return_value = sample_coworking

        response = client.get("/coworkings/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == sample_coworking["name"]

    def test_get_coworking_not_found(self, client, mock_db):
        """Test getting nonexistent coworking."""
        mock_db.return_value = None

        response = client.get("/coworkings/999")

        assert response.status_code == 404


class TestCoworkingsUpdate:
    """Tests for PUT /coworkings/{coworking_id}"""

    def test_update_coworking_manager(self, client, manager_headers, mock_db, sample_coworking):
        """Test updating coworking as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_coworking,  # get_coworking (from ensure_can_manage)
            None,  # usp_Coworking_Update
            None,  # audit
            {**sample_coworking, "name": "Updated", "address": "New Addr", "amenities": "New"},  # get_coworking after update
        ]

        response = client.put(
            "/coworkings/1",
            json={"name": "Updated", "address": "New Addr", "amenities": "New"},
            headers=manager_headers
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_coworking_forbidden_other_manager(self, client, manager_headers, mock_db):
        """Test updating coworking managed by another manager."""
        other_coworking = {"id": 1, "manager_id": 999, "name": "Other", "address": "Addr", "amenities": None, "workspace_count": 0}
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            other_coworking,  # get_coworking
        ]

        response = client.put(
            "/coworkings/1",
            json={"name": "Updated", "address": "Addr", "amenities": "New"},
            headers=manager_headers
        )

        assert response.status_code == 403
        assert "керуєте" in response.json()["detail"]

    def test_update_coworking_admin(self, client, admin_headers, mock_db, sample_coworking):
        """Test updating coworking as admin (can manage any)."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_coworking,  # get_coworking (from ensure_can_manage)
            None,  # usp_Coworking_Update
            None,  # audit
            {**sample_coworking, "name": "Updated", "address": "New Addr", "amenities": "New"},  # get_coworking after update
        ]

        response = client.put(
            "/coworkings/1",
            json={"name": "Updated", "address": "New Addr", "amenities": "New"},
            headers=admin_headers
        )

        assert response.status_code == 200


class TestCoworkingsAssignManager:
    """Tests for PUT /coworkings/{coworking_id}/manager (admin only)"""

    def test_assign_manager_admin(self, client, admin_headers, mock_db, sample_coworking):
        """Test assigning manager as admin."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_coworking,  # get_coworking
            {"id": 5, "email": "newmanager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # _check_manager_user
            None,  # usp_Coworking_AssignManager
            None,  # audit
            {**sample_coworking, "manager_id": 5},
        ]

        response = client.put(
            "/coworkings/1/manager",
            json={"manager_id": 5},
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["manager_id"] == 5

    def test_assign_invalid_manager(self, client, admin_headers, mock_db, sample_coworking):
        """Test assigning non-manager user."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_coworking,  # get_coworking
            {"id": 5, "email": "user@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # _check_manager_user - not a manager
        ]

        response = client.put(
            "/coworkings/1/manager",
            json={"manager_id": 5},
            headers=admin_headers
        )

        assert response.status_code == 400

    def test_assign_manager_forbidden_non_admin(self, client, manager_headers):
        """Test assigning manager as non-admin."""
        response = client.put(
            "/coworkings/1/manager",
            json={"manager_id": 5},
            headers=manager_headers
        )

        assert response.status_code == 403


class TestCoworkingsDelete:
    """Tests for DELETE /coworkings/{coworking_id}"""

    def test_delete_coworking_manager(self, client, manager_headers, mock_db, sample_coworking):
        """Test deleting coworking as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_coworking,  # get_coworking (from ensure_can_manage)
            None,  # usp_Coworking_Delete
            None,  # audit
        ]

        response = client.delete("/coworkings/1", headers=manager_headers)

        assert response.status_code == 204


# ==================== Workspace Tests ====================

class TestWorkspacesList:
    """Tests for GET /coworkings/{coworking_id}/workspaces"""

    def test_list_workspaces(self, client, mock_db, sample_workspace):
        """Test listing workspaces in a coworking."""
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},  # get_coworking
            [sample_workspace],  # usp_Workspace_ListByCoworking
        ]

        response = client.get("/coworkings/1/workspaces")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "Desk"

    def test_list_workspaces_only_open(self, client, mock_db, sample_workspace):
        """Test listing only open workspaces."""
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},
            [sample_workspace],
        ]

        response = client.get("/coworkings/1/workspaces?only_open=true")

        assert response.status_code == 200


class TestWorkspacesAvailable:
    """Tests for GET /coworkings/{coworking_id}/workspaces/available"""

    def test_available_workspaces(self, client, mock_db, sample_workspace, future_datetime_range):
        """Test finding available workspaces."""
        start, end = future_datetime_range
        # Use format without timezone to avoid + encoding issue
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},
            [sample_workspace],
        ]

        response = client.get(f"/coworkings/1/workspaces/available?start={start_str}&end={end_str}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_available_workspaces_invalid_range(self, client, mock_db, future_datetime):
        """Test available workspaces with end <= start."""
        start = future_datetime
        end = future_datetime  # same time

        mock_db.return_value = {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1}

        start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

        response = client.get(f"/coworkings/1/workspaces/available?start={start_str}&end={end_str}")

        assert response.status_code == 422
        assert "пізніше" in response.json()["detail"]


class TestWorkspacesCreate:
    """Tests for POST /coworkings/{coworking_id}/workspaces"""

    def test_create_workspace_manager(self, client, manager_headers, mock_db, sample_workspace):
        """Test creating workspace as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 0},  # ensure_can_manage -> get_coworking
            {"id": 2, "coworking_id": 1, "type": "Meeting Room", "price_per_hour": 25.00, "is_open_for_booking": True},  # usp_Workspace_Create
            None,  # audit
        ]

        response = client.post(
            "/coworkings/1/workspaces",
            json={"type": "Meeting Room", "price_per_hour": "25.00", "is_open_for_booking": True},
            headers=manager_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "Meeting Room"
        assert float(data["price_per_hour"]) == 25.00


class TestWorkspaceGet:
    """Tests for GET /workspaces/{workspace_id}"""

    def test_get_workspace(self, client, mock_db, sample_workspace):
        """Test getting a specific workspace."""
        mock_db.return_value = sample_workspace

        response = client.get("/workspaces/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestWorkspaceUpdate:
    """Tests for PUT /workspaces/{workspace_id}"""

    def test_update_workspace_manager(self, client, manager_headers, mock_db, sample_workspace):
        """Test updating workspace as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_workspace,  # _workspace_for_manager -> usp_Workspace_GetById
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Workspace_Update
            None,  # audit
            {**sample_workspace, "type": "Updated", "price_per_hour": Decimal("15.00")},  # usp_Workspace_GetById (updated)
        ]

        response = client.put(
            "/workspaces/1",
            json={"type": "Updated", "price_per_hour": "15.00"},
            headers=manager_headers
        )

        assert response.status_code == 200
        assert response.json()["type"] == "Updated"


class TestWorkspaceSetOpen:
    """Tests for PUT /workspaces/{workspace_id}/open"""

    def test_set_workspace_open(self, client, manager_headers, mock_db, sample_workspace):
        """Test setting workspace open/closed for booking."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_workspace,  # _workspace_for_manager -> usp_Workspace_GetById
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Workspace_SetOpen
            None,  # audit
            {**sample_workspace, "is_open_for_booking": False},  # usp_Workspace_GetById (updated)
        ]

        response = client.put(
            "/workspaces/1/open",
            json={"is_open_for_booking": False},
            headers=manager_headers
        )

        assert response.status_code == 200
        assert response.json()["is_open_for_booking"] is False


class TestWorkspaceDelete:
    """Tests for DELETE /workspaces/{workspace_id}"""

    def test_delete_workspace_manager(self, client, manager_headers, mock_db, sample_workspace, sample_coworking):
        """Test deleting workspace as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_workspace,  # _workspace_for_manager -> usp_Workspace_GetById
            sample_coworking,  # ensure_can_manage -> get_coworking
            None,  # usp_Workspace_Delete
            None,  # audit
        ]

        response = client.delete("/workspaces/1", headers=manager_headers)

        assert response.status_code == 204


# ==================== Layout Tests ====================

class TestLayout:
    """Tests for layout endpoints"""

    def test_get_layout(self, client, mock_db):
        """Test getting coworking layout."""
        layout_items = [
            {"workspace_id": 1, "x": 10.0, "y": 20.0, "code": "A1", "features": "sw", "capacity": 1, "hall": "Main"},
        ]
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},
            layout_items,
        ]

        response = client.get("/coworkings/1/layout")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workspace_id"] == 1

    def test_save_layout_manager(self, client, manager_headers, mock_db):
        """Test saving layout as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Layout_Save
            None,  # audit (called before usp_Layout_List)
            [{"workspace_id": 1, "x": 10.0, "y": 20.0, "code": "A1", "features": "sw", "capacity": 1, "hall": "Main"}],  # usp_Layout_List
        ]

        response = client.put(
            "/coworkings/1/layout",
            json={"items": [{"workspace_id": 1, "x": 10.0, "y": 20.0, "code": "A1", "features": "sw", "capacity": 1, "hall": "Main"}]},
            headers=manager_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["workspace_id"] == 1

    def test_save_layout_duplicate_workspace(self, client, manager_headers, mock_db):
        """Test saving layout with duplicate workspace_id."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 2},  # ensure_can_manage -> get_coworking
            None,  # usp_Layout_Save (won't be called due to validation error)
        ]

        response = client.put(
            "/coworkings/1/layout",
            json={"items": [
                {"workspace_id": 1, "x": 10.0, "y": 20.0, "features": "s", "capacity": 1, "hall": "Main"},
                {"workspace_id": 1, "x": 30.0, "y": 40.0, "features": "w", "capacity": 1, "hall": "Main"},
            ]},
            headers=manager_headers
        )

        assert response.status_code == 422
        # FastAPI validation errors are in the detail array
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("двічі" in str(d.get("msg", "")) for d in detail)


# ==================== Shapes Tests ====================

class TestShapes:
    """Tests for shapes endpoints"""

    def test_get_shapes(self, client, mock_db):
        """Test getting shapes."""
        shapes = [
            {"kind": "wall", "hall": "Main", "x1": 0, "y1": 0, "x2": 100, "y2": 0, "label": None},
        ]
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},
            shapes,
        ]

        response = client.get("/coworkings/1/shapes")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_save_shapes_manager(self, client, manager_headers, mock_db):
        """Test saving shapes as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Shape_Save
            None,  # audit (called before usp_Shape_List)
            [{"kind": "wall", "hall": "Main", "x1": 0, "y1": 0, "x2": 100, "y2": 0, "label": None}],  # usp_Shape_List
        ]

        response = client.put(
            "/coworkings/1/shapes",
            json={"items": [{"kind": "wall", "hall": "Main", "x1": 0, "y1": 0, "x2": 100, "y2": 0, "label": None}]},
            headers=manager_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["kind"] == "wall"


# ==================== Settings Tests ====================

class TestSettings:
    """Tests for settings endpoints"""

    def test_get_settings(self, client, mock_db):
        """Test getting coworking settings."""
        settings = {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8}
        mock_db.side_effect = [
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 1, "workspace_count": 1},
            settings,
        ]

        response = client.get("/coworkings/1/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["open_hour"] == 9
        assert data["close_hour"] == 21

    def test_save_settings_manager(self, client, manager_headers, mock_db):
        """Test saving settings as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Settings_Save
            None,  # audit (called before usp_Settings_Get)
            {"open_hour": 10, "close_hour": 22, "max_desk_hours": 3, "max_room_hours": 6},  # usp_Settings_Get
        ]

        response = client.put(
            "/coworkings/1/settings",
            json={"open_hour": 10, "close_hour": 22, "max_desk_hours": 3, "max_room_hours": 6},
            headers=manager_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["open_hour"] == 10
        assert data["close_hour"] == 22
        assert data["max_desk_hours"] == 3
        assert data["max_room_hours"] == 6

    def test_save_settings_invalid_hours(self, client, manager_headers, mock_db):
        """Test saving settings with close_hour <= open_hour."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
        ]

        response = client.put(
            "/coworkings/1/settings",
            json={"open_hour": 22, "close_hour": 10, "max_desk_hours": 3, "max_room_hours": 6},
            headers=manager_headers
        )

        assert response.status_code == 422
        # FastAPI validation errors are in the detail array
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("пізніше" in str(d.get("msg", "")) for d in detail)


# ==================== Blacklist Tests ====================

class TestBlacklist:
    """Tests for blacklist endpoints"""

    def test_list_blacklist_manager(self, client, manager_headers, mock_db):
        """Test listing blacklist as manager."""
        blacklist = [
            {"id": 1, "user_id": 5, "email": "bad@example.com", "coworking_id": 1, "reason": "Spam"},
        ]
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            blacklist,  # usp_Blacklist_ListByCoworking
        ]

        response = client.get("/coworkings/1/blacklist", headers=manager_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == 5

    def test_add_to_blacklist_manager(self, client, manager_headers, mock_db):
        """Test adding user to blacklist."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            {"id": 1, "user_id": 5, "email": "bad@example.com", "coworking_id": 1, "reason": "Spam"},  # usp_Blacklist_Add
            None,  # audit
        ]

        response = client.post(
            "/coworkings/1/blacklist",
            json={"user_id": 5, "reason": "Spam"},
            headers=manager_headers
        )

        assert response.status_code == 201
        assert response.json()["user_id"] == 5

    def test_remove_from_blacklist_manager(self, client, manager_headers, mock_db):
        """Test removing user from blacklist."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            None,  # usp_Blacklist_Remove
            None,  # audit
        ]

        response = client.delete("/coworkings/1/blacklist/5", headers=manager_headers)

        assert response.status_code == 204


# ==================== Coworking Bookings Tests ====================

class TestCoworkingBookings:
    """Tests for GET /coworkings/{coworking_id}/bookings (manager view)"""

    def test_list_coworking_bookings_manager(self, client, manager_headers, mock_db):
        """Test listing bookings for a coworking as manager."""
        bookings = [
            {"id": 1, "user_id": 1, "email": "user@example.com", "workspace_id": 1, "workspace_type": "Desk", "coworking_id": 1, "coworking_name": "Test", "price_per_hour": Decimal("10.00"), "start_time": datetime.now(timezone.utc), "end_time": datetime.now(timezone.utc), "status": "Pending"},
        ]
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            bookings,  # usp_Booking_ListByCoworking
        ]

        response = client.get("/coworkings/1/bookings", headers=manager_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_coworking_bookings_with_filters(self, client, manager_headers, mock_db):
        """Test listing bookings with date and status filters."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "name": "Test", "address": "Addr", "amenities": None, "manager_id": 3, "workspace_count": 1},  # ensure_can_manage -> get_coworking
            [],  # usp_Booking_ListByCoworking
        ]

        response = client.get("/coworkings/1/bookings?from=2024-01-01T00:00:00&to=2024-12-31T23:59:59&status=Confirmed", headers=manager_headers)

        assert response.status_code == 200