"""Unit tests for security utility functions."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.security import (
    hash_password, verify_password,
    create_access_token, decode_token,
    new_totp_secret, encrypt_secret, decrypt_secret,
    provisioning_uri, match_totp_step,
    new_recovery_codes, hash_recovery,
    hash_token, new_email_token,
)
from app.config import Settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing produces a string."""
        password = "TestPass123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password

    def test_hash_password_deterministic_different_salts(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPass123"
        hashed = hash_password(password)
        assert verify_password("WrongPass", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password."""
        hashed = hash_password("TestPass123")
        assert verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test verifying against invalid hash format."""
        assert verify_password("password", "not-a-valid-hash") is False

    def test_long_password(self):
        """Test hashing very long password (bcrypt limit is 72 bytes after prehash)."""
        # The prehash uses SHA-256 then base64, so input can be any length
        long_password = "x" * 200
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True


class TestJWT:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = 123
        token, ttl = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_decode_token_valid(self):
        """Test decoding valid token."""
        user_id = 123
        token, _ = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        with pytest.raises(Exception):
            decode_token("invalid.token.string")

    def test_decode_token_expired(self):
        """Test decoding expired token."""
        # Create a token with very short expiry by patching settings
        with patch("app.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                jwt_secret="test-secret",
                jwt_expire_min=-1  # Already expired
            )
            token, _ = create_access_token(123)

        # Wait a moment and try to decode
        import time
        time.sleep(0.1)
        with pytest.raises(Exception):
            decode_token(token)

    def test_token_different_users(self):
        """Test tokens for different users are different."""
        token1, _ = create_access_token(1)
        token2, _ = create_access_token(2)
        assert token1 != token2

        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        assert payload1["sub"] == "1"
        assert payload2["sub"] == "2"


class TestTOTP:
    """Tests for TOTP (2FA) functions."""

    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Override settings for TOTP tests."""
        with patch("app.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                totp_enc_key="V8ZUoa0b41F-tpj3bQilzQABUj759HPR9npeu_YoZJg=",
                totp_issuer="CoworkingBooking"
            )
            yield

    def test_new_totp_secret(self):
        """Test generating new TOTP secret."""
        secret = new_totp_secret()
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded 20 bytes

    def test_totp_secret_unique(self):
        """Test that secrets are unique."""
        secret1 = new_totp_secret()
        secret2 = new_totp_secret()
        assert secret1 != secret2

    def test_encrypt_decrypt_secret(self):
        """Test encrypting and decrypting TOTP secret."""
        secret = new_totp_secret()
        encrypted = encrypt_secret(secret)
        assert isinstance(encrypted, bytes)

        decrypted = decrypt_secret(encrypted)
        assert decrypted == secret

    def test_encrypt_decrypt_different_secrets(self):
        """Test encrypting different secrets produces different ciphertexts."""
        secret1 = new_totp_secret()
        secret2 = new_totp_secret()
        encrypted1 = encrypt_secret(secret1)
        encrypted2 = encrypt_secret(secret2)
        assert encrypted1 != encrypted2

    def test_provisioning_uri(self):
        """Test generating provisioning URI for QR code."""
        secret = new_totp_secret()
        email = "test@example.com"
        uri = provisioning_uri(secret, email)
        assert isinstance(uri, str)
        assert uri.startswith("otpauth://totp/")
        assert "CoworkingBooking" in uri  # default issuer from settings
        assert "test%40example.com" in uri  # URL-encoded email
        assert secret in uri

    def test_match_totp_step_valid(self):
        """Test matching valid TOTP code."""
        secret = new_totp_secret()
        totp = __import__('pyotp').TOTP(secret)
        current_code = totp.now()

        step = match_totp_step(secret, current_code)
        assert step is not None
        assert isinstance(step, int)

    def test_match_totp_step_invalid(self):
        """Test matching invalid TOTP code."""
        secret = new_totp_secret()
        step = match_totp_step(secret, "000000")
        assert step is None

    def test_match_totp_step_prev_next_window(self):
        """Test matching code from previous/next time window."""
        secret = new_totp_secret()
        totp = __import__('pyotp').TOTP(secret)

        # Get code from 30 seconds ago (previous window)
        import time
        prev_step = int(time.time() // 30) - 1
        prev_code = totp.at(prev_step * 30)

        step = match_totp_step(secret, prev_code)
        assert step is not None
        assert step == prev_step

    def test_match_totp_step_strips_spaces(self):
        """Test that spaces in code are stripped."""
        secret = new_totp_secret()
        totp = __import__('pyotp').TOTP(secret)
        current_code = totp.now()

        # Add spaces
        code_with_spaces = " ".join(current_code[i:i+2] for i in range(0, len(current_code), 2))
        step = match_totp_step(secret, code_with_spaces)
        assert step is not None


class TestRecoveryCodes:
    """Tests for recovery codes functions."""

    def test_new_recovery_codes_default_count(self):
        """Test generating default number of recovery codes."""
        codes = new_recovery_codes()
        assert isinstance(codes, list)
        assert len(codes) == 10

    def test_new_recovery_codes_custom_count(self):
        """Test generating custom number of recovery codes."""
        codes = new_recovery_codes(5)
        assert len(codes) == 5

    def test_recovery_codes_format(self):
        """Test recovery codes have correct format (hex-hex)."""
        codes = new_recovery_codes(3)
        for code in codes:
            assert "-" in code
            parts = code.split("-")
            assert len(parts) == 2
            assert len(parts[0]) == 8  # 4 bytes = 8 hex chars
            assert len(parts[1]) == 8
            # Verify they're valid hex
            int(parts[0], 16)
            int(parts[1], 16)

    def test_recovery_codes_unique(self):
        """Test recovery codes are unique within a batch."""
        codes = new_recovery_codes(20)
        assert len(codes) == len(set(codes))

    def test_hash_recovery(self):
        """Test hashing recovery code."""
        code = "abcd-efgh"
        hashed = hash_recovery(code)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex

    def test_hash_recovery_case_insensitive(self):
        """Test recovery code hashing is case insensitive."""
        code1 = "ABCD-EFGH"
        code2 = "abcd-efgh"
        assert hash_recovery(code1) == hash_recovery(code2)

    def test_hash_recovery_ignores_dashes(self):
        """Test recovery code hashing ignores dashes."""
        code1 = "abcd-efgh"
        code2 = "abcdefgh"
        assert hash_recovery(code1) == hash_recovery(code2)

    def test_hash_recovery_strips_whitespace(self):
        """Test recovery code hashing strips whitespace."""
        code1 = "abcd-efgh"
        code2 = "  abcd-efgh  "
        assert hash_recovery(code1) == hash_recovery(code2)


class TestEmailTokens:
    """Tests for email token functions."""

    def test_hash_token(self):
        """Test hashing token."""
        token = "test-token-123"
        hashed = hash_token(token)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex

    def test_hash_token_deterministic(self):
        """Test token hashing is deterministic."""
        token = "test-token-123"
        assert hash_token(token) == hash_token(token)

    def test_new_email_token(self):
        """Test generating new email token."""
        token, token_hash = new_email_token()
        assert isinstance(token, str)
        assert len(token) > 20  # URL-safe base64
        assert isinstance(token_hash, str)
        assert len(token_hash) == 64
        assert token_hash == hash_token(token)

    def test_new_email_token_unique(self):
        """Test each call generates unique token."""
        token1, hash1 = new_email_token()
        token2, hash2 = new_email_token()
        assert token1 != token2
        assert hash1 != hash2