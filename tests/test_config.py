"""Unit tests for config module."""
import pytest
from unittest.mock import patch

from app.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_settings_defaults(self):
        """Test default values."""
        # Create a fresh Settings instance with test values
        settings = Settings(
            jwt_secret="test-secret",
            totp_enc_key="V8ZUoa0b41F-tpj3bQilzQABUj759HPR9npeu_YoZJg=",
            db_server="localhost",
            db_name="CoworkingDB",
            db_user="",
            db_password="",
            smtp_host="",
            smtp_port=587,
            smtp_starttls=True,
            smtp_ssl=False,
            smtp_from="no-reply@example.com",
            smtp_from_name="Coworking",
            require_email_verification=True,
            verify_token_ttl_hours=24,
            reset_token_ttl_minutes=60,
        )
        assert settings.db_server == "localhost"
        assert settings.db_name == "CoworkingDB"
        assert settings.db_user == ""
        assert settings.db_driver == "ODBC Driver 18 for SQL Server"
        assert settings.db_trust_cert is False
        assert settings.jwt_expire_min == 60
        assert settings.totp_issuer == "CoworkingBooking"
        assert settings.cors_origins == "*"
        assert settings.smtp_host == ""
        assert settings.smtp_port == 587
        assert settings.smtp_starttls is True
        assert settings.smtp_ssl is False
        assert settings.smtp_from == "no-reply@example.com"
        assert settings.smtp_from_name == "Coworking"
        assert settings.require_email_verification is True
        assert settings.verify_token_ttl_hours == 24
        assert settings.reset_token_ttl_minutes == 60

    def test_settings_from_env(self):
        """Test settings loaded from environment variables."""
        with patch.dict("os.environ", {
            "DB_SERVER": "myserver.database.windows.net",
            "DB_NAME": "MyDB",
            "DB_USER": "myuser",
            "DB_PASSWORD": "mypassword",
            "JWT_SECRET": "my-jwt-secret",
            "JWT_EXPIRE_MIN": "120",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
            "TOTP_ISSUER": "MyApp",
            "CORS_ORIGINS": "https://app.example.com,https://admin.example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "smtpuser",
            "SMTP_PASSWORD": "smtppass",
            "SMTP_STARTTLS": "false",
            "SMTP_SSL": "true",
            "SMTP_FROM": "noreply@example.com",
            "SMTP_FROM_NAME": "My App",
            "REQUIRE_EMAIL_VERIFICATION": "false",
            "VERIFY_TOKEN_TTL_HOURS": "48",
            "RESET_TOKEN_TTL_MINUTES": "30",
        }, clear=True):
            settings = Settings()
            assert settings.db_server == "myserver.database.windows.net"
            assert settings.db_name == "MyDB"
            assert settings.db_user == "myuser"
            assert settings.db_password == "mypassword"
            assert settings.jwt_secret == "my-jwt-secret"
            assert settings.jwt_expire_min == 120
            assert settings.totp_issuer == "MyApp"
            assert settings.cors_origins == "https://app.example.com,https://admin.example.com"
            assert settings.smtp_host == "smtp.example.com"
            assert settings.smtp_port == 465
            assert settings.smtp_user == "smtpuser"
            assert settings.smtp_password == "smtppass"
            assert settings.smtp_starttls is False
            assert settings.smtp_ssl is True
            assert settings.smtp_from == "noreply@example.com"
            assert settings.smtp_from_name == "My App"
            assert settings.require_email_verification is False
            assert settings.verify_token_ttl_hours == 48
            assert settings.reset_token_ttl_minutes == 30

    def test_settings_conn_str_with_user(self):
        """Test connection string with user/password."""
        with patch.dict("os.environ", {
            "DB_SERVER": "myserver",
            "DB_NAME": "MyDB",
            "DB_USER": "myuser",
            "DB_PASSWORD": "pass}word",  # Test brace escaping
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
        }, clear=True):
            settings = Settings()
            conn_str = settings.conn_str
            assert "DRIVER={ODBC Driver 18 for SQL Server}" in conn_str
            assert "SERVER=myserver" in conn_str
            assert "DATABASE=MyDB" in conn_str
            assert "UID=myuser" in conn_str
            assert "PWD={pass}}word}" in conn_str  # Braces escaped
            assert "Trusted_Connection=yes" not in conn_str
            assert "Encrypt=yes" in conn_str
            assert "TrustServerCertificate=no" in conn_str

    def test_settings_conn_str_trusted_connection(self):
        """Test connection string with trusted connection (no user)."""
        with patch.dict("os.environ", {
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "V8ZUoa0b41F-tpj3bQilzQABUj759HPR9npeu_YoZJg=",
            "DB_USER": "",
            "DB_PASSWORD": "",
        }, clear=True):
            settings = Settings()
            conn_str = settings.conn_str
            assert "Trusted_Connection=yes" in conn_str
            assert "UID=" not in conn_str
            assert "PWD=" not in conn_str

    def test_settings_conn_str_trust_cert_true(self):
        """Test connection string with trust server certificate."""
        with patch.dict("os.environ", {
            "DB_TRUST_CERT": "true",
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
        }, clear=True):
            settings = Settings()
            conn_str = settings.conn_str
            assert "TrustServerCertificate=yes" in conn_str

    def test_settings_required_fields(self):
        """Test that required fields raise error if missing."""
        # When creating Settings directly, we must provide required fields
        # The validation happens when loading from env, not when constructing directly
        # So we test that loading from empty env raises error
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(Exception):
                Settings(_env_file=None, _env_file_encoding=None)

    def test_settings_extra_ignored(self):
        """Test that extra fields are ignored."""
        with patch.dict("os.environ", {
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
            "NONEXISTENT_FIELD": "value",
        }, clear=True):
            settings = Settings()  # Should not raise


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        with patch.dict("os.environ", {
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
        }, clear=True):
            s1 = get_settings()
            s2 = get_settings()
            assert s1 is s2  # Same instance due to lru_cache

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns Settings instance."""
        with patch.dict("os.environ", {
            "JWT_SECRET": "secret",
            "TOTP_ENC_KEY": "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
        }, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)