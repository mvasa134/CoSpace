"""Unit tests for auth router endpoints."""
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException

from app.security import hash_password, new_totp_secret, encrypt_secret


def login_row(password: str, email: str = "test@example.com", **over) -> dict:
    """Row returned by usp_User_GetForLogin."""
    row = {
        "id": 1,
        "email": email,
        "password_hash": hash_password(password),
        "role": "Client",
        "is_blocked": False,
        "is_email_verified": True,
        "totp_secret": None,
        "is_totp_enabled": False,
    }
    row.update(over)
    return row


class TestAuthRegister:
    """Tests for POST /auth/register"""

    def test_register_success(self, client, db, test_user_data):
        db["usp_User_Register"] = {
            "id": 1,
            "email": test_user_data["email"],
            "role": "Client",
            "is_blocked": False,
            "is_email_verified": False,
            "created_at": datetime.now(timezone.utc),
        }

        with patch("app.routers.auth.mailer.send_verification"):
            response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["email"] == test_user_data["email"]
        assert data["role"] == "Client"
        assert data["is_blocked"] is False
        assert data["is_email_verified"] is False

    def test_register_duplicate_email(self, client, mock_db, test_user_data):
        mock_db.side_effect = HTTPException(409, "Такий запис уже існує.")

        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 409
        assert "уже існує" in response.json()["detail"]

    def test_register_invalid_email(self, client, test_password):
        response = client.post("/auth/register", json={"email": "invalid", "password": test_password})

        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post("/auth/register", json={"email": "test@example.com", "password": "short"})

        assert response.status_code == 422


class TestAuthLogin:
    """Tests for POST /auth/login"""

    def test_login_success(self, client, db, test_user_data, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password)

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": test_password})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client, db, test_user_data):
        db["usp_User_GetForLogin"] = login_row("correct")

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": "wrong"})

        assert response.status_code == 401
        assert "Невірний" in response.json()["detail"]

    def test_login_nonexistent_user(self, client, db, test_user_data):
        db["usp_User_GetForLogin"] = None

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": "anypassword"})

        assert response.status_code == 401
        assert "Невірний" in response.json()["detail"]

    def test_login_blocked_user(self, client, db, test_user_data, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password, is_blocked=True)

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": test_password})

        assert response.status_code == 403
        assert "заблоковано" in response.json()["detail"]

    def test_login_unverified_email(self, client, db, monkeypatch, test_settings, test_user_data, test_password):
        """Login with unverified email when verification is required."""
        strict = test_settings.model_copy(update={"require_email_verification": True})
        monkeypatch.setattr("app.routers.auth.get_settings", lambda: strict)
        db["usp_User_GetForLogin"] = login_row(test_password, is_email_verified=False)

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": test_password})

        assert response.status_code == 403
        assert "Підтвердіть email" in response.json()["detail"]
        assert response.headers.get("X-Auth-Step") == "email_not_verified"

    def test_login_totp_required(self, client, db, test_user_data, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted, is_totp_enabled=True)

        response = client.post("/auth/login", json={"email": test_user_data["email"], "password": test_password})

        assert response.status_code == 401
        assert "Google Authenticator" in response.json()["detail"]
        assert response.headers.get("X-Auth-Step") == "totp_required"

    def test_login_totp_valid_code(self, client, db, test_user_data, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted, is_totp_enabled=True)
        db["usp_Auth_RegisterTotpStep"] = {"accepted": True}

        with patch("app.routers.auth.match_totp_step", return_value=12345):
            response = client.post(
                "/auth/login",
                json={"email": test_user_data["email"], "password": test_password, "totp_code": "123456"},
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_totp_replayed_code(self, client, db, test_user_data, test_password):
        """A TOTP step that was already used must be rejected."""
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted, is_totp_enabled=True)
        db["usp_Auth_RegisterTotpStep"] = {"accepted": False}

        with patch("app.routers.auth.match_totp_step", return_value=12345):
            response = client.post(
                "/auth/login",
                json={"email": test_user_data["email"], "password": test_password, "totp_code": "123456"},
            )

        assert response.status_code == 401

    def test_login_recovery_code(self, client, db, test_user_data, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted, is_totp_enabled=True)
        db["usp_RecoveryCode_Use"] = {"accepted": True}

        response = client.post(
            "/auth/login",
            json={"email": test_user_data["email"], "password": test_password, "recovery_code": "abcd-efgh"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_recovery_code_rejected(self, client, db, test_user_data, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted, is_totp_enabled=True)
        db["usp_RecoveryCode_Use"] = {"accepted": False}

        response = client.post(
            "/auth/login",
            json={"email": test_user_data["email"], "password": test_password, "recovery_code": "abcd-efgh"},
        )

        assert response.status_code == 401


class TestAuthEmailVerification:
    """Tests for email verification endpoints."""

    def test_verify_email_success(self, client, db):
        db["usp_EmailToken_Consume"] = {"user_id": 1}

        response = client.post("/auth/verify-email", json={"token": "valid-token"})

        assert response.status_code == 200
        assert "підтверджено" in response.json()["detail"].lower()

    def test_verify_email_invalid_token(self, client, db):
        db["usp_EmailToken_Consume"] = None

        response = client.post("/auth/verify-email", json={"token": "invalid-token"})

        assert response.status_code == 400
        assert "недійсне" in response.json()["detail"].lower()

    def test_verify_email_link(self, client, db):
        db["usp_EmailToken_Consume"] = {"user_id": 1}

        response = client.get("/auth/verify-email?token=valid-token")

        assert response.status_code == 200
        assert "підтверджено" in response.text.lower()

    def test_verify_email_link_invalid(self, client, db):
        db["usp_EmailToken_Consume"] = None

        response = client.get("/auth/verify-email?token=invalid-token")

        assert response.status_code == 400

    def test_resend_verification(self, client, db, test_user_data):
        db["usp_User_GetByEmail"] = {
            "id": 1,
            "email": test_user_data["email"],
            "is_blocked": False,
            "is_email_verified": False,
        }

        with patch("app.routers.auth.mailer.send_verification") as mock_send:
            response = client.post("/auth/resend-verification", json={"email": test_user_data["email"]})

            assert response.status_code == 202
            mock_send.assert_called_once()

    def test_resend_verification_unknown_email_is_uniform(self, client, db, test_user_data):
        db["usp_User_GetByEmail"] = None

        with patch("app.routers.auth.mailer.send_verification") as mock_send:
            response = client.post("/auth/resend-verification", json={"email": test_user_data["email"]})

            assert response.status_code == 202
            mock_send.assert_not_called()


class TestAuthPasswordReset:
    """Tests for password reset endpoints."""

    def test_forgot_password(self, client, db, test_user_data):
        db["usp_User_GetByEmail"] = {"id": 1, "email": test_user_data["email"], "is_blocked": False}

        with patch("app.routers.auth.mailer.send_password_reset") as mock_send:
            response = client.post("/auth/forgot-password", json={"email": test_user_data["email"]})

            assert response.status_code == 202
            mock_send.assert_called_once()

    def test_forgot_password_nonexistent(self, client, db, test_user_data):
        db["usp_User_GetByEmail"] = None

        response = client.post("/auth/forgot-password", json={"email": test_user_data["email"]})

        assert response.status_code == 202
        assert "надіслали лист" in response.json()["detail"]

    def test_reset_password_page(self, client):
        response = client.get("/auth/reset-password?token=test-token")

        assert response.status_code == 200
        assert "Новий пароль" in response.text

    def test_reset_password_success(self, client, db):
        db["usp_EmailToken_Consume"] = {"user_id": 1}
        db["usp_User_GetById"] = {"id": 1, "email": "test@example.com"}

        with patch("app.routers.auth.mailer.send_password_changed") as mock_send:
            response = client.post(
                "/auth/reset-password",
                json={"token": "valid-token", "new_password": "NewPass123"},
            )

            assert response.status_code == 200
            assert "змінено" in response.json()["detail"].lower()
            mock_send.assert_called_once()

    def test_reset_password_invalid_token(self, client, db):
        db["usp_EmailToken_Consume"] = None

        # token must be >= 10 chars, otherwise Pydantic returns 422 before the logic runs
        response = client.post(
            "/auth/reset-password",
            json={"token": "invalid-token", "new_password": "NewPass123"},
        )

        assert response.status_code == 400
        assert "недійсне" in response.json()["detail"].lower()

    def test_reset_password_short_token_is_422(self, client, db):
        response = client.post(
            "/auth/reset-password",
            json={"token": "short", "new_password": "NewPass123"},
        )

        assert response.status_code == 422

    def test_change_password_success(self, client, db, auth_headers, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password)

        with patch("app.routers.auth.mailer.send_password_changed") as mock_send:
            response = client.post(
                "/auth/change-password",
                json={"old_password": test_password, "new_password": "NewPass123"},
                headers=auth_headers,
            )

            assert response.status_code == 204
            mock_send.assert_called_once()

    def test_change_password_wrong_old(self, client, db, auth_headers):
        db["usp_User_GetForLogin"] = login_row("correct")

        response = client.post(
            "/auth/change-password",
            json={"old_password": "wrong", "new_password": "NewPass123"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "невірний" in response.json()["detail"].lower()

    def test_change_password_requires_auth(self, client, db):
        response = client.post(
            "/auth/change-password",
            json={"old_password": "x", "new_password": "NewPass123"},
        )

        assert response.status_code == 401


class TestAuthTOTP:
    """Tests for TOTP (2FA) endpoints."""

    def test_totp_setup(self, client, db, auth_headers, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password)

        response = client.post("/auth/totp/setup", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "otpauth_uri" in data
        assert "otpauth://totp/" in data["otpauth_uri"]

    def test_totp_setup_already_enabled(self, client, db, auth_headers, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password, is_totp_enabled=True)

        response = client.post("/auth/totp/setup", headers=auth_headers)

        assert response.status_code == 409
        assert "вже увімкнено" in response.json()["detail"]

    def test_totp_enable_success(self, client, db, auth_headers, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted)

        with patch("app.routers.auth.match_totp_step", return_value=12345):
            response = client.post("/auth/totp/enable", json={"code": "123456"}, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "recovery_codes" in data
        assert len(data["recovery_codes"]) == 10

    def test_totp_enable_invalid_code(self, client, db, auth_headers, test_password):
        encrypted = encrypt_secret(new_totp_secret())
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=encrypted)

        with patch("app.routers.auth.match_totp_step", return_value=None):
            response = client.post("/auth/totp/enable", json={"code": "000000"}, headers=auth_headers)

        assert response.status_code == 400
        assert "невірний" in response.json()["detail"].lower()

    def test_totp_enable_no_secret(self, client, db, auth_headers, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password, totp_secret=None)

        response = client.post("/auth/totp/enable", json={"code": "123456"}, headers=auth_headers)

        assert response.status_code == 400
        assert "спочатку викличіть" in response.json()["detail"].lower()

    def test_totp_disable_success(self, client, db, auth_headers, test_password):
        db["usp_User_GetForLogin"] = login_row(test_password, is_totp_enabled=True)

        response = client.post("/auth/totp/disable", json={"password": test_password}, headers=auth_headers)

        assert response.status_code == 204

    def test_totp_disable_wrong_password(self, client, db, auth_headers):
        db["usp_User_GetForLogin"] = login_row("correct", is_totp_enabled=True)

        response = client.post("/auth/totp/disable", json={"password": "wrong"}, headers=auth_headers)

        assert response.status_code == 400
        assert "невірний" in response.json()["detail"].lower()