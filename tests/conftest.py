"""Pytest configuration and common fixtures for CoSpace tests."""
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "back"))

from app.main import app
from app.config import Settings, get_settings
from app.schemas import to_db_dt
from app.security import create_access_token, new_totp_secret


# ==================== Test Settings ====================
class AppTestSettings(Settings):  # Renamed from TestSettings to prevent pytest collection warning
    """Test-specific settings that override production settings."""
    __test__ = False
    db_host: str = "localhost"
    db_port: int = 1433
    db_name: str = "CoworkingTest"
    db_user: str = "test_user"
    db_password: str = "test_password"
    jwt_secret: str = "test-secret-key-for-testing-only"
    jwt_expire_min: int = 60
    totp_enc_key: str = "V8ZUoa0b41F-tpj3bQilzQABUj759HPR9npeu_YoZJg="  # Fernet key for testing
    totp_issuer: str = "CoSpace Test"
    cors_origins: str = "http://localhost:3000"
    require_email_verification: bool = False
    verify_token_ttl_hours: int = 24
    reset_token_ttl_minutes: int = 15

    @property
    def conn_str(self) -> str:
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.db_host},{self.db_port};"
            f"DATABASE={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
        )


@pytest.fixture(scope="session")
def test_settings() -> AppTestSettings:
    """Provide test settings instance."""
    return AppTestSettings()


@pytest.fixture(autouse=True)
def override_settings(test_settings: AppTestSettings, monkeypatch) -> Generator[None, None, None]:
    """Make every consumer of get_settings see the test settings.

    dependency_overrides only affects Depends(get_settings); code that calls
    get_settings() directly (e.g. app/routers/auth.py) needs a monkeypatch of
    the name imported into its module.
    """
    app.dependency_overrides[get_settings] = lambda: test_settings
    for target in (
        "app.routers.auth.get_settings",
        "app.security.get_settings",
        "app.mailer.get_settings",
        "app.deps.get_settings",
    ):
        monkeypatch.setattr(target, lambda: test_settings, raising=False)
    yield
    app.dependency_overrides.clear()


# ==================== Test Client ====================
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """FastAPI test client for API testing."""
    with TestClient(app) as c:
        yield c


# ==================== Database Mocking ====================
@pytest.fixture(autouse=True)
def mock_db():
    """Mock the database call function for unit testing without real DB.
    This is autouse so all tests get DB mocking by default.
    """
    # Patch at the module where it's used (app.deps and app.routers.*)
    with patch("app.deps.call") as mock_call, \
         patch("app.routers.auth.call", mock_call), \
         patch("app.routers.users.call", mock_call), \
         patch("app.routers.coworkings.call", mock_call), \
         patch("app.routers.bookings.call", mock_call), \
         patch("app.routers.audit.call", mock_call), \
         patch("app.audit.call", mock_call):
        yield mock_call


@pytest.fixture
def db(mock_db, registered_user):
    """Name-based fake for stored procedures.

    Tests set only what matters: db["usp_User_GetForLogin"] = {...}.
    The number and order of calls (audit, current_user, ...) no longer matter.
    Calling a procedure that has no response raises, so missing setup is loud.
    """
    responses = {
        "usp_AuditLog_Add": None,
        "usp_EmailToken_Create": None,
        "usp_User_MarkEmailVerified": None,
        "usp_Auth_ChangePassword": None,
        "usp_Auth_SetTotpSecret": None,
        "usp_Auth_EnableTotp": None,
        "usp_Auth_DisableTotp": None,
        "usp_Auth_RegisterTotpStep": {"accepted": True},
        "usp_RecoveryCode_Clear": None,
        "usp_RecoveryCode_Add": None,
        "usp_User_GetById": registered_user,  # read by deps.current_user
    }

    def fake_call(name, one=False, **kw):
        if name not in responses:
            raise AssertionError(f"Unexpected stored procedure: {name}")
        r = responses[name]
        return r(**kw) if callable(r) else r

    mock_db.side_effect = fake_call
    return responses


@pytest.fixture
def mock_db_connect():
    """Mock the database connection for tests that need connection-level control."""
    with patch("app.db._connect") as mock_connect:
        yield mock_connect


# ==================== Auth Fixtures ====================
@pytest.fixture
def test_password() -> str:
    """Standard test password."""
    return "TestPass123"


@pytest.fixture
def test_user_data(test_password: str) -> dict:
    """Test user data for registration."""
    return {
        "email": "test@example.com",
        "password": test_password,
    }


@pytest.fixture
def registered_user(test_user_data: dict, test_password: str) -> dict:
    """Test user data for registration (without DB mocking)."""
    user_id = 1
    return {"id": user_id, "email": test_user_data["email"], "role": "Client", "is_blocked": False, "is_email_verified": True}


@pytest.fixture
def auth_token(registered_user: dict) -> str:
    """Generate a valid JWT token for the registered user."""
    token, _ = create_access_token(registered_user["id"])
    return token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_user() -> dict:
    """Admin user data (without DB mocking)."""
    user_id = 2
    return {"id": user_id, "email": "admin@example.com", "role": "PlatformAdmin", "is_blocked": False, "is_email_verified": True}


@pytest.fixture
def admin_token(admin_user: dict) -> str:
    """Generate a valid JWT token for the admin user."""
    token, _ = create_access_token(admin_user["id"])
    return token


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_user() -> dict:
    """Manager user data (without DB mocking)."""
    user_id = 3
    return {"id": user_id, "email": "manager@example.com", "role": "SpaceManager", "is_blocked": False, "is_email_verified": True}


@pytest.fixture
def manager_token(manager_user: dict) -> str:
    """Generate a valid JWT token for the manager user."""
    token, _ = create_access_token(manager_user["id"])
    return token


@pytest.fixture
def manager_headers(manager_token: str) -> dict:
    """Authorization headers for manager."""
    return {"Authorization": f"Bearer {manager_token}"}


# ==================== Coworking Fixtures ====================
@pytest.fixture
def sample_coworking() -> dict:
    """Sample coworking data."""
    return {
        "id": 1,
        "name": "Test Coworking",
        "address": "123 Test St",
        "amenities": "WiFi, Coffee, AC",
        "manager_id": 3,
        "workspace_count": 5,
    }


@pytest.fixture
def sample_workspace() -> dict:
    """Sample workspace data."""
    return {
        "id": 1,
        "coworking_id": 1,
        "type": "Desk",
        "price_per_hour": 10.00,
        "is_open_for_booking": True,
    }


@pytest.fixture
def sample_booking() -> dict:
    """Sample booking data."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "user_id": 1,
        "email": "test@example.com",
        "workspace_id": 1,
        "workspace_type": "Desk",
        "coworking_id": 1,
        "coworking_name": "Test Coworking",
        "price_per_hour": 10.00,
        "start_time": to_db_dt(now + timedelta(hours=1)),
        "end_time": to_db_dt(now + timedelta(hours=3)),
        "status": "Pending",
    }


# ==================== TOTP Fixtures ====================
@pytest.fixture
def totp_secret() -> str:
    """Generate a TOTP secret for testing."""
    return new_totp_secret()


# ==================== Utility Fixtures ====================
@pytest.fixture
def future_datetime() -> datetime:
    """A datetime in the future (UTC)."""
    return datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture
def future_datetime_range(future_datetime: datetime) -> tuple[datetime, datetime]:
    """A start and end datetime range in the future."""
    start = future_datetime.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)
    return start, end


# ==================== Async Test Support ====================
@pytest.fixture
def event_loop():
    """Create an event loop for async tests (kept as-is: other tests pass with it)."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()