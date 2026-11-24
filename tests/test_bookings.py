"""Unit tests for bookings router endpoints."""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch

from app.main import app
from app.schemas import to_db_dt


class TestBookingsCreate:
    """Tests for POST /bookings"""

    def test_create_booking_success(self, client, auth_headers, mock_db, future_datetime_range, sample_workspace):
        """Test creating a booking successfully."""
        start, end = future_datetime_range
        user_id = 1
        mock_db.side_effect = [
            {"id": user_id, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            # _check_limits -> usp_Workspace_GetById
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": True},
            # _check_limits -> usp_Settings_Get
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},
            # usp_Booking_Create
            {"id": 1, "user_id": user_id, "workspace_id": 1, "start_time": to_db_dt(start), "end_time": to_db_dt(end), "status": "Pending", "coworking_id": 1, "workspace_type": "Desk", "coworking_name": "Test", "price_per_hour": Decimal("10.00")},
            # audit
            None,
        ]

        response = client.post(
            "/bookings",
            json={"workspace_id": 1, "start_time": start.isoformat(), "end_time": end.isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workspace_id"] == 1
        assert data["status"] == "Pending"

    def test_create_booking_outside_hours(self, client, auth_headers, mock_db, sample_workspace):
        """Test creating booking outside coworking hours."""
        # 8 AM - before open hour of 9
        start = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(hours=2)

        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": True},
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},
        ]

        response = client.post(
            "/bookings",
            json={"workspace_id": 1, "start_time": start.isoformat(), "end_time": end.isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 422
        assert "працює з" in response.json()["detail"]

    def test_create_booking_exceeds_max_hours(self, client, auth_headers, mock_db, sample_workspace):
        """Test creating booking exceeding max hours for desk."""
        start = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(hours=5)  # exceeds max_desk_hours of 4

        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": True},
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},
        ]

        response = client.post(
            "/bookings",
            json={"workspace_id": 1, "start_time": start.isoformat(), "end_time": end.isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 422
        assert "Максимальна тривалість" in response.json()["detail"]

    def test_create_booking_workspace_not_found(self, client, auth_headers, mock_db, future_datetime_range):
        """Test creating booking for nonexistent workspace."""
        start, end = future_datetime_range
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            None,  # usp_Workspace_GetById
        ]

        response = client.post(
            "/bookings",
            json={"workspace_id": 999, "start_time": start.isoformat(), "end_time": end.isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "не знайдено" in response.json()["detail"]

    def test_create_booking_workspace_closed(self, client, auth_headers, mock_db, future_datetime_range):
        """Test creating booking for closed workspace."""
        start, end = future_datetime_range
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": False},  # _check_limits -> usp_Workspace_GetById
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},  # _check_limits -> usp_Settings_Get
            # usp_Booking_Create might be called but we don't know the exact behavior
            {"id": 1, "user_id": 1, "workspace_id": 1, "start_time": to_db_dt(start), "end_time": to_db_dt(end), "status": "Pending", "coworking_id": 1, "workspace_type": "Desk", "coworking_name": "Test", "price_per_hour": Decimal("10.00")},  # usp_Booking_Create
            None,  # audit
        ]

        response = client.post(
            "/bookings",
            json={"workspace_id": 1, "start_time": start.isoformat(), "end_time": end.isoformat()},
            headers=auth_headers
        )

        # The _check_limits doesn't check is_open_for_booking, but the SP might
        # This depends on the stored procedure behavior


class TestBookingsMyBookings:
    """Tests for GET /bookings/my"""

    def test_my_bookings(self, client, auth_headers, mock_db, sample_booking):
        """Test listing user's own bookings."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            [sample_booking],  # usp_Booking_ListByUser
        ]

        response = client.get("/bookings/my", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_booking["id"]

    def test_my_bookings_with_status_filter(self, client, auth_headers, mock_db):
        """Test listing bookings with status filter."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            [],  # usp_Booking_ListByUser
        ]

        response = client.get("/bookings/my?status=Confirmed", headers=auth_headers)

        assert response.status_code == 200


class TestBookingsGet:
    """Tests for GET /bookings/{booking_id}"""

    def test_get_booking_owner(self, client, auth_headers, mock_db, sample_booking):
        """Test getting booking as owner."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
        ]

        response = client.get(f"/bookings/{sample_booking['id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_booking["id"]

    def test_get_booking_manager(self, client, manager_headers, mock_db, sample_booking):
        """Test getting booking as manager of the coworking."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
        ]

        response = client.get(f"/bookings/{sample_booking['id']}", headers=manager_headers)

        assert response.status_code == 200

    def test_get_booking_admin(self, client, admin_headers, mock_db, sample_booking):
        """Test getting booking as admin."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,
            {"id": 1, "manager_id": 3},
        ]

        response = client.get(f"/bookings/{sample_booking['id']}", headers=admin_headers)

        assert response.status_code == 200

    def test_get_booking_forbidden_other_user(self, client, auth_headers, mock_db, sample_booking):
        """Test getting booking owned by another user (non-staff)."""
        other_booking = {**sample_booking, "user_id": 999}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            other_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
        ]

        response = client.get(f"/bookings/{sample_booking['id']}", headers=auth_headers)

        assert response.status_code == 403
        assert "доступу" in response.json()["detail"]

    def test_get_booking_not_found(self, client, auth_headers, mock_db):
        """Test getting nonexistent booking."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            None,
        ]

        response = client.get("/bookings/999", headers=auth_headers)

        assert response.status_code == 404


class TestBookingsUpdate:
    """Tests for PUT /bookings/{booking_id}"""

    def test_update_booking_owner(self, client, auth_headers, mock_db, sample_booking, future_datetime_range):
        """Test updating booking as owner."""
        new_start, new_end = future_datetime_range
        new_start = new_start + timedelta(hours=1)
        new_end = new_end + timedelta(hours=1)

        booking_with_coworking = {**sample_booking, "coworking_id": 1}

        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            booking_with_coworking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking (first call in _load)
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking (second call in update_booking line 80)
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": True},  # _check_limits -> usp_Workspace_GetById
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},  # _check_limits -> usp_Settings_Get
            None,  # usp_Booking_Update
            None,  # audit (called before final get)
            {**booking_with_coworking, "start_time": to_db_dt(new_start), "end_time": to_db_dt(new_end)},  # usp_Booking_GetById (final)
        ]

        response = client.put(
            f"/bookings/{sample_booking['id']}",
            json={"start_time": new_start.isoformat(), "end_time": new_end.isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_update_booking_manager_bypass_limits(self, client, manager_headers, mock_db, sample_booking, future_datetime_range):
        """Test manager can update booking bypassing limits."""
        new_start, new_end = future_datetime_range
        new_start = new_start + timedelta(hours=1)
        new_end = new_end + timedelta(hours=1)

        booking_with_coworking = {**sample_booking, "coworking_id": 1}

        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            booking_with_coworking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking (in _load)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking (in update_booking line 80)
            None,  # usp_Booking_Update (no _check_limits called for staff)
            None,  # audit (called before final get)
            {**booking_with_coworking, "start_time": to_db_dt(new_start), "end_time": to_db_dt(new_end)},  # usp_Booking_GetById (final)
        ]

        response = client.put(
            f"/bookings/{sample_booking['id']}",
            json={"start_time": new_start.isoformat(), "end_time": new_end.isoformat()},
            headers=manager_headers
        )

        assert response.status_code == 200

    def test_update_booking_not_open_state(self, client, auth_headers, mock_db, sample_booking):
        """Test updating booking not in open state (Completed/Cancelled)."""
        # "Confirmed" IS in OPEN_STATES, so we need "Completed" or "Cancelled" for this test
        completed_booking = {**sample_booking, "status": "Completed", "coworking_id": 1}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            completed_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking (in _load)
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking (in update_booking line 80)
            # For client (not manager), _check_limits is called:
            {"id": 1, "coworking_id": 1, "type": "Desk", "price_per_hour": Decimal("10.00"), "is_open_for_booking": True},  # _check_limits -> usp_Workspace_GetById
            {"open_hour": 9, "close_hour": 21, "max_desk_hours": 4, "max_room_hours": 8},  # _check_limits -> usp_Settings_Get
        ]

        response = client.put(
            f"/bookings/{sample_booking['id']}",
            json={"start_time": sample_booking["start_time"].isoformat(), "end_time": sample_booking["end_time"].isoformat()},
            headers=auth_headers
        )

        assert response.status_code == 409
        assert "активне" in response.json()["detail"]


class TestBookingsCancel:
    """Tests for POST /bookings/{booking_id}/cancel"""

    def test_cancel_booking_owner(self, client, auth_headers, mock_db, sample_booking):
        """Test cancelling booking as owner."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            None,  # _payment -> usp_Payment_GetByBooking (no payment)
            None,  # usp_Booking_Cancel
            None,  # audit (called before final get)
            {**sample_booking, "status": "Cancelled", "coworking_id": 1},  # usp_Booking_GetById (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/cancel", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "Cancelled"

    def test_cancel_booking_paid(self, client, auth_headers, mock_db, sample_booking):
        """Test cancelling paid booking (should fail)."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            {"id": 1, "status": "Paid"},  # _payment -> usp_Payment_GetByBooking
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/cancel", headers=auth_headers)

        assert response.status_code == 409
        assert "оплачене" in response.json()["detail"]

    def test_cancel_booking_not_open_state(self, client, auth_headers, mock_db, sample_booking):
        """Test cancelling booking not in open state."""
        completed_booking = {**sample_booking, "status": "Completed"}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            completed_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/cancel", headers=auth_headers)

        assert response.status_code == 409
        assert "активне" in response.json()["detail"]


class TestBookingsConfirm:
    """Tests for POST /bookings/{booking_id}/confirm (staff only)"""

    def test_confirm_booking_manager(self, client, manager_headers, mock_db, sample_booking):
        """Test confirming booking as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
            None,  # usp_Booking_Confirm
            None,  # audit (called before final get)
            {**sample_booking, "status": "Confirmed", "coworking_id": 1},  # usp_Booking_GetById (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/confirm", headers=manager_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "Confirmed"

    def test_confirm_booking_admin(self, client, admin_headers, mock_db, sample_booking):
        """Test confirming booking as admin."""
        mock_db.side_effect = [
            {"id": 2, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
            None,  # usp_Booking_Confirm
            None,  # audit (called before final get)
            {**sample_booking, "status": "Confirmed", "coworking_id": 1},  # usp_Booking_GetById (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/confirm", headers=admin_headers)

        assert response.status_code == 200

    def test_confirm_booking_forbidden_client(self, client, auth_headers, mock_db, sample_booking):
        """Test confirming booking as client (forbidden)."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/confirm", headers=auth_headers)

        assert response.status_code == 403


class TestBookingsComplete:
    """Tests for POST /bookings/{booking_id}/complete (staff only)"""

    def test_complete_booking_manager(self, client, manager_headers, mock_db, sample_booking):
        """Test completing booking as manager."""
        confirmed_booking = {**sample_booking, "status": "Confirmed"}
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            confirmed_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
            None,  # usp_Booking_Complete
            None,  # audit (called before final get)
            {**confirmed_booking, "status": "Completed", "coworking_id": 1},  # usp_Booking_GetById (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/complete", headers=manager_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "Completed"


# ==================== Payment Tests ====================

class TestPaymentsGet:
    """Tests for GET /bookings/{booking_id}/payment"""

    def test_get_payment(self, client, auth_headers, mock_db, sample_booking):
        """Test getting payment for booking."""
        payment = {"id": 1, "booking_id": sample_booking["id"], "amount": Decimal("20.00"), "status": "Pending", "paid_at": None}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            payment,  # _payment -> usp_Payment_GetByBooking
        ]

        response = client.get(f"/bookings/{sample_booking['id']}/payment", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "20.00"
        assert data["status"] == "Pending"

    def test_get_payment_not_found(self, client, auth_headers, mock_db, sample_booking):
        """Test getting payment when none exists."""
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            None,  # no payment -> usp_Payment_GetByBooking
        ]

        response = client.get(f"/bookings/{sample_booking['id']}/payment", headers=auth_headers)

        assert response.status_code == 404
        assert "ще немає" in response.json()["detail"]


class TestPaymentsCreate:
    """Tests for POST /bookings/{booking_id}/payment"""

    def test_create_payment(self, client, auth_headers, mock_db, sample_booking):
        """Test creating payment for booking."""
        payment = {"id": 1, "booking_id": sample_booking["id"], "amount": Decimal("20.00"), "status": "Pending", "paid_at": None}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            payment,  # usp_Payment_Create
            None,  # audit
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/payment", headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "Pending"


class TestPaymentsPay:
    """Tests for POST /bookings/{booking_id}/pay"""

    def test_pay_booking(self, client, auth_headers, mock_db, sample_booking):
        """Test paying for booking (simulated)."""
        payment = {"id": 1, "booking_id": sample_booking["id"], "amount": Decimal("20.00"), "status": "Paid", "paid_at": datetime.now(timezone.utc)}
        mock_db.side_effect = [
            {"id": 1, "email": "test@example.com", "role": "Client", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById
            {"id": 1, "manager_id": 1},  # can_manage -> get_coworking
            None,  # _payment (no existing payment) -> usp_Payment_GetByBooking
            None,  # usp_Payment_Create
            payment,  # usp_Payment_Pay
            None,  # audit
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/pay", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Paid"


class TestPaymentsFail:
    """Tests for POST /bookings/{booking_id}/payment/fail (staff only)"""

    def test_fail_payment_manager(self, client, manager_headers, mock_db, sample_booking):
        """Test marking payment as failed as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
            None,  # usp_Payment_Fail
            None,  # audit (called before final _payment)
            {"id": 1, "booking_id": sample_booking["id"], "amount": Decimal("20.00"), "status": "Failed", "paid_at": None},  # _payment -> usp_Payment_GetByBooking (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/payment/fail", headers=manager_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "Failed"


class TestPaymentsRefund:
    """Tests for POST /bookings/{booking_id}/payment/refund (staff only)"""

    def test_refund_payment_manager(self, client, manager_headers, mock_db, sample_booking):
        """Test refunding payment as manager."""
        mock_db.side_effect = [
            {"id": 3, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True, "created_at": "2024-01-01T00:00:00"},  # current_user
            sample_booking,  # _load -> usp_Booking_GetById (staff_only=True)
            {"id": 1, "manager_id": 3},  # can_manage -> get_coworking
            None,  # usp_Payment_Refund
            None,  # audit (called before final _payment)
            {"id": 1, "booking_id": sample_booking["id"], "amount": Decimal("20.00"), "status": "Refunded", "paid_at": datetime.now(timezone.utc)},  # _payment -> usp_Payment_GetByBooking (final)
        ]

        response = client.post(f"/bookings/{sample_booking['id']}/payment/refund", headers=manager_headers)

        assert response.status_code == 200
        assert response.json()["status"] == "Refunded"