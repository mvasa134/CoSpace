"""Unit tests for Pydantic schemas validation."""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.schemas import (
    RegisterIn, LoginIn, ChangePasswordIn, TotpCodeIn,
    UserOut, RoleIn, BlockedIn,
    CoworkingIn, CoworkingUpdateIn, WorkspaceCreateIn, WorkspaceUpdateIn, OpenIn,
    BlacklistIn, BookingCreateIn, BookingUpdateIn,
    LayoutItemIn, LayoutIn, ShapeIn, ShapesIn, SettingsIn,
    to_db_dt, RoleName, StatusName,
)


class TestAuthSchemas:
    """Tests for auth-related schemas."""

    def test_register_in_valid(self):
        """Test valid registration input."""
        data = RegisterIn(email="test@example.com", password="ValidPass123")
        assert data.email == "test@example.com"
        assert data.password == "ValidPass123"

    def test_register_in_invalid_email(self):
        """Test registration with invalid email."""
        with pytest.raises(ValueError):
            RegisterIn(email="invalid", password="ValidPass123")

    def test_register_in_short_password(self):
        """Test registration with too short password."""
        with pytest.raises(ValueError):
            RegisterIn(email="test@example.com", password="short")

    def test_register_in_long_password(self):
        """Test registration with too long password."""
        with pytest.raises(ValueError):
            RegisterIn(email="test@example.com", password="x" * 129)

    def test_login_in_valid(self):
        """Test valid login input."""
        data = LoginIn(email="test@example.com", password="anypassword")
        assert data.email == "test@example.com"
        assert data.password == "anypassword"

    def test_login_in_with_totp(self):
        """Test login with TOTP code."""
        data = LoginIn(email="test@example.com", password="pass", totp_code="123456")
        assert data.totp_code == "123456"

    def test_login_in_with_recovery(self):
        """Test login with recovery code."""
        data = LoginIn(email="test@example.com", password="pass", recovery_code="abcd-efgh")
        assert data.recovery_code == "abcd-efgh"

    def test_change_password_in_valid(self):
        """Test valid change password input."""
        data = ChangePasswordIn(old_password="old", new_password="NewPass123")
        assert data.old_password == "old"
        assert data.new_password == "NewPass123"

    def test_totp_code_in_valid(self):
        """Test valid TOTP code input."""
        data = TotpCodeIn(code="123456")
        assert data.code == "123456"


class TestUserSchemas:
    """Tests for user-related schemas."""

    def test_user_out_valid(self):
        """Test UserOut schema."""
        now = datetime.now(timezone.utc)
        data = UserOut(
            id=1, email="test@example.com", role="Client",
            is_blocked=False, is_email_verified=True, created_at=now
        )
        assert data.id == 1
        assert data.role == "Client"

    def test_user_out_invalid_role(self):
        """Test UserOut with invalid role."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            UserOut(id=1, email="test@example.com", role="Invalid", is_blocked=False, is_email_verified=True, created_at=now)

    def test_role_in_valid(self):
        """Test RoleIn schema."""
        data = RoleIn(role="SpaceManager")
        assert data.role == "SpaceManager"

    def test_role_in_invalid(self):
        """Test RoleIn with invalid role."""
        with pytest.raises(ValueError):
            RoleIn(role="InvalidRole")

    def test_blocked_in_valid(self):
        """Test BlockedIn schema."""
        data = BlockedIn(is_blocked=True)
        assert data.is_blocked is True


class TestCoworkingSchemas:
    """Tests for coworking/workspace schemas."""

    def test_coworking_update_in_valid(self):
        """Test valid coworking update."""
        data = CoworkingUpdateIn(name="Name", address="Address", amenities="Amenities")
        assert data.name == "Name"
        assert data.address == "Address"

    def test_coworking_update_in_empty_name(self):
        """Test coworking update with empty name."""
        with pytest.raises(ValueError):
            CoworkingUpdateIn(name="", address="Address")

    def test_coworking_in_with_manager(self):
        """Test CoworkingIn with manager_id."""
        data = CoworkingIn(name="Name", address="Address", manager_id=5)
        assert data.manager_id == 5

    def test_workspace_create_in_valid(self):
        """Test valid workspace creation."""
        data = WorkspaceCreateIn(type="Desk", price_per_hour=Decimal("10.00"), is_open_for_booking=True)
        assert data.type == "Desk"
        assert data.price_per_hour == Decimal("10.00")

    def test_workspace_create_in_negative_price(self):
        """Test workspace creation with negative price."""
        with pytest.raises(ValueError):
            WorkspaceCreateIn(type="Desk", price_per_hour=Decimal("-1.00"))

    def test_workspace_update_in_valid(self):
        """Test valid workspace update."""
        data = WorkspaceUpdateIn(type="Meeting Room", price_per_hour=Decimal("25.00"))
        assert data.type == "Meeting Room"

    def test_open_in_valid(self):
        """Test OpenIn schema."""
        data = OpenIn(is_open_for_booking=False)
        assert data.is_open_for_booking is False


class TestBlacklistSchemas:
    """Tests for blacklist schemas."""

    def test_blacklist_in_valid(self):
        """Test valid blacklist input."""
        data = BlacklistIn(user_id=5, reason="Spam")
        assert data.user_id == 5
        assert data.reason == "Spam"


class TestBookingSchemas:
    """Tests for booking schemas."""

    def test_booking_create_in_valid(self, future_datetime_range):
        """Test valid booking creation."""
        start, end = future_datetime_range
        data = BookingCreateIn(workspace_id=1, start_time=start, end_time=end)
        assert data.workspace_id == 1
        assert data.start_time == start
        assert data.end_time == end

    def test_booking_create_in_invalid_range(self):
        """Test booking creation with end <= start."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            BookingCreateIn(workspace_id=1, start_time=now, end_time=now)

    def test_booking_create_in_end_before_start(self):
        """Test booking creation with end before start."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            BookingCreateIn(workspace_id=1, start_time=now + timedelta(hours=2), end_time=now)

    def test_booking_update_in_valid(self, future_datetime_range):
        """Test valid booking update."""
        start, end = future_datetime_range
        data = BookingUpdateIn(start_time=start, end_time=end)
        assert data.start_time == start


class TestLayoutSchemas:
    """Tests for layout schemas."""

    def test_layout_item_in_valid(self):
        """Test valid layout item."""
        data = LayoutItemIn(workspace_id=1, x=10.0, y=20.0, code="A1", features="sw", capacity=2, hall="Main")
        assert data.workspace_id == 1
        assert data.x == 10.0
        assert data.features == "sw"

    def test_layout_item_in_invalid_x(self):
        """Test layout item with invalid x coordinate."""
        with pytest.raises(ValueError):
            LayoutItemIn(workspace_id=1, x=-1, y=10.0)

    def test_layout_item_in_invalid_y(self):
        """Test layout item with invalid y coordinate."""
        with pytest.raises(ValueError):
            LayoutItemIn(workspace_id=1, x=10.0, y=101)

    def test_layout_item_in_invalid_features(self):
        """Test layout item with invalid features pattern."""
        with pytest.raises(ValueError):
            LayoutItemIn(workspace_id=1, x=10.0, y=10.0, features="xyz")

    def test_layout_item_in_invalid_capacity(self):
        """Test layout item with invalid capacity."""
        with pytest.raises(ValueError):
            LayoutItemIn(workspace_id=1, x=10.0, y=10.0, capacity=0)

    def test_layout_in_valid(self):
        """Test valid layout."""
        items = [
            LayoutItemIn(workspace_id=1, x=10.0, y=10.0, features="s", capacity=1, hall="Main"),
            LayoutItemIn(workspace_id=2, x=20.0, y=20.0, features="w", capacity=1, hall="Main"),
        ]
        data = LayoutIn(items=items)
        assert len(data.items) == 2

    def test_layout_in_duplicate_workspace(self):
        """Test layout with duplicate workspace_id."""
        items = [
            LayoutItemIn(workspace_id=1, x=10.0, y=10.0, features="s", capacity=1, hall="Main"),
            LayoutItemIn(workspace_id=1, x=20.0, y=20.0, features="w", capacity=1, hall="Main"),
        ]
        with pytest.raises(ValueError):
            LayoutIn(items=items)

    def test_layout_in_too_many_items(self):
        """Test layout with too many items."""
        items = [LayoutItemIn(workspace_id=i, x=0, y=0, features="s", capacity=1, hall="Main") for i in range(501)]
        with pytest.raises(ValueError):
            LayoutIn(items=items)


class TestShapeSchemas:
    """Tests for shape schemas."""

    def test_shape_in_valid(self):
        """Test valid shape."""
        data = ShapeIn(kind="wall", hall="Main", x1=0, y1=0, x2=100, y2=0, label="Wall")
        assert data.kind == "wall"
        assert data.label == "Wall"

    def test_shape_in_invalid_kind(self):
        """Test shape with invalid kind."""
        with pytest.raises(ValueError):
            ShapeIn(kind="invalid", hall="Main", x1=0, y1=0, x2=100, y2=0)

    def test_shape_in_invalid_coordinates(self):
        """Test shape with invalid coordinates."""
        with pytest.raises(ValueError):
            ShapeIn(kind="wall", hall="Main", x1=-1, y1=0, x2=100, y2=0)

    def test_shapes_in_valid(self):
        """Test valid shapes list."""
        items = [
            ShapeIn(kind="wall", hall="Main", x1=0, y1=0, x2=100, y2=0),
            ShapeIn(kind="door", hall="Main", x1=50, y1=0, x2=50, y2=10),
        ]
        data = ShapesIn(items=items)
        assert len(data.items) == 2


class TestSettingsSchemas:
    """Tests for settings schemas."""

    def test_settings_in_valid(self):
        """Test valid settings."""
        data = SettingsIn(open_hour=9, close_hour=21, max_desk_hours=4, max_room_hours=8)
        assert data.open_hour == 9
        assert data.close_hour == 21

    def test_settings_in_invalid_hours(self):
        """Test settings with close_hour <= open_hour."""
        with pytest.raises(ValueError):
            SettingsIn(open_hour=22, close_hour=10, max_desk_hours=4, max_room_hours=8)

    def test_settings_in_invalid_open_hour(self):
        """Test settings with invalid open_hour."""
        with pytest.raises(ValueError):
            SettingsIn(open_hour=-1, close_hour=21, max_desk_hours=4, max_room_hours=8)

    def test_settings_in_invalid_max_hours(self):
        """Test settings with invalid max hours."""
        with pytest.raises(ValueError):
            SettingsIn(open_hour=9, close_hour=21, max_desk_hours=0, max_room_hours=8)


class TestToDbDt:
    """Tests for to_db_dt utility function."""

    def test_to_db_dt_utc(self):
        """Test converting UTC datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
        result = to_db_dt(dt)
        assert result == datetime(2024, 1, 15, 10, 30, 45)
        assert result.tzinfo is None

    def test_to_db_dt_with_timezone(self):
        """Test converting datetime with timezone offset."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone(timedelta(hours=2)))
        result = to_db_dt(dt)
        # Should convert to UTC: 10:30:45
        assert result == datetime(2024, 1, 15, 10, 30, 45)
        assert result.tzinfo is None

    def test_to_db_dt_naive(self):
        """Test converting naive datetime (assumed UTC)."""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        result = to_db_dt(dt)
        assert result == datetime(2024, 1, 15, 10, 30, 45)
        assert result.tzinfo is None

    def test_to_db_dt_strips_microseconds(self):
        """Test that microseconds are stripped."""
        dt = datetime(2024, 1, 15, 10, 30, 45, 999999, tzinfo=timezone.utc)
        result = to_db_dt(dt)
        assert result.microsecond == 0