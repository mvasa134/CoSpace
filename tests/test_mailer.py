"""Unit tests for mailer module."""
import pytest
from unittest.mock import patch, MagicMock, call
from email.message import EmailMessage

from app.mailer import send_email, send_verification, send_password_reset, send_password_changed, _deliver
from app.config import Settings


class TestSendEmail:
    """Tests for send_email function."""

    def test_send_email_dev_mode_logs(self, caplog):
        """Test that dev mode (no SMTP host) logs instead of sending."""
        with patch("app.mailer.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(smtp_host="")
            with caplog.at_level("WARNING"):
                send_email("test@example.com", "Test Subject", "Test body")

            assert "SMTP не налаштовано" in caplog.text
            assert "test@example.com" in caplog.text
            assert "Test Subject" in caplog.text
            assert "Test body" in caplog.text

    @patch("app.mailer.smtplib.SMTP")
    @patch("app.mailer.ssl.create_default_context")
    def test_send_email_smtp_success(self, mock_ssl_context, mock_smtp_class):
        """Test successful email sending via SMTP with STARTTLS."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_starttls = True
        mock_settings.smtp_ssl = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        mock_ssl_context.return_value = MagicMock()

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_email("to@example.com", "Subject", "Body")

        mock_smtp_class.assert_called_once_with("smtp.example.com", 587, timeout=20)
        mock_smtp.ehlo.assert_called()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.send_message.assert_called_once()

    @patch("app.mailer.smtplib.SMTP_SSL")
    @patch("app.mailer.ssl.create_default_context")
    def test_send_email_smtp_ssl_success(self, mock_ssl_context, mock_smtp_ssl_class):
        """Test successful email sending via SMTP_SSL."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 465
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_ssl = True
        mock_settings.smtp_starttls = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp_ssl_class.return_value.__enter__.return_value = mock_smtp
        mock_ssl_context.return_value = MagicMock()

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_email("to@example.com", "Subject", "Body")

        mock_smtp_ssl_class.assert_called_once_with("smtp.example.com", 465, context=mock_ssl_context.return_value, timeout=20)
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.send_message.assert_called_once()

    @patch("app.mailer.smtplib.SMTP")
    @patch("app.mailer.ssl.create_default_context")
    def test_send_email_no_auth(self, mock_ssl_context, mock_smtp_class):
        """Test sending email without authentication."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 25
        mock_settings.smtp_user = ""
        mock_settings.smtp_password = ""
        mock_settings.smtp_starttls = False
        mock_settings.smtp_ssl = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        mock_ssl_context.return_value = MagicMock()

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_email("to@example.com", "Subject", "Body")

        mock_smtp.login.assert_not_called()
        mock_smtp.send_message.assert_called_once()

    @patch("app.mailer.smtplib.SMTP")
    def test_send_email_smtp_exception(self, mock_smtp_class, caplog):
        """Test handling SMTP exception."""
        import smtplib
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_starttls = True
        mock_settings.smtp_ssl = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp.starttls.side_effect = smtplib.SMTPException("Connection failed")
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        with patch("app.mailer.get_settings", return_value=mock_settings):
            with caplog.at_level("ERROR"):
                send_email("to@example.com", "Subject", "Body")

        assert "Не вдалося відправити лист" in caplog.text

    @patch("app.mailer.smtplib.SMTP")
    def test_send_email_smtp_exception_raise_errors(self, mock_smtp_class):
        """Test that raise_errors=True propagates exception."""
        import smtplib
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_starttls = True
        mock_settings.smtp_ssl = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp.starttls.side_effect = smtplib.SMTPException("Connection failed")
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        with patch("app.mailer.get_settings", return_value=mock_settings):
            with pytest.raises(smtplib.SMTPException):
                send_email("to@example.com", "Subject", "Body", raise_errors=True)

    @patch("app.mailer.smtplib.SMTP")
    def test_send_email_message_format(self, mock_smtp_class):
        """Test that email message is properly formatted."""
        mock_settings = MagicMock()
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_starttls = True
        mock_settings.smtp_ssl = False
        mock_settings.smtp_from = "from@example.com"
        mock_settings.smtp_from_name = "Test App"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_email("to@example.com", "Test Subject", "Test body content")

        # Check the message that was sent
        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert isinstance(sent_msg, EmailMessage)
        assert sent_msg["Subject"] == "Test Subject"
        assert sent_msg["To"] == "to@example.com"
        assert "Test App <from@example.com>" in sent_msg["From"]
        assert sent_msg.get_content().strip() == "Test body content"
        assert "Message-ID" in sent_msg


class TestDeliver:
    """Tests for _deliver internal function."""

    def test_deliver_with_auth(self):
        """Test _deliver with authentication."""
        mock_srv = MagicMock()
        mock_settings = MagicMock()
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"

        msg = EmailMessage()
        msg["Subject"] = "Test"
        msg["From"] = "from@example.com"
        msg["To"] = "to@example.com"
        msg.set_content("Body")

        _deliver(mock_srv, mock_settings, msg)

        mock_srv.login.assert_called_once_with("user", "pass")
        mock_srv.send_message.assert_called_once_with(msg)

    def test_deliver_without_auth(self):
        """Test _deliver without authentication."""
        mock_srv = MagicMock()
        mock_settings = MagicMock()
        mock_settings.smtp_user = ""
        mock_settings.smtp_password = ""

        msg = EmailMessage()
        msg.set_content("Body")

        _deliver(mock_srv, mock_settings, msg)

        mock_srv.login.assert_not_called()
        mock_srv.send_message.assert_called_once_with(msg)


class TestTemplateEmails:
    """Tests for template email functions."""

    @patch("app.mailer.send_email")
    def test_send_verification(self, mock_send_email):
        """Test send_verification creates correct link and calls send_email."""
        mock_settings = MagicMock()
        mock_settings.verify_url_template = "https://app.example.com/verify?token={token}"
        mock_settings.verify_token_ttl_hours = 24

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_verification("user@example.com", "test-token-123")

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "user@example.com"
        assert args[1] == "Підтвердіть email"
        assert "https://app.example.com/verify?token=test-token-123" in args[2]
        assert "24 год." in args[2]

    @patch("app.mailer.send_email")
    def test_send_password_reset(self, mock_send_email):
        """Test send_password_reset creates correct link and calls send_email."""
        mock_settings = MagicMock()
        mock_settings.reset_url_template = "https://app.example.com/reset?token={token}"
        mock_settings.reset_token_ttl_minutes = 60

        with patch("app.mailer.get_settings", return_value=mock_settings):
            send_password_reset("user@example.com", "reset-token-456")

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "user@example.com"
        assert args[1] == "Скидання пароля"
        assert "https://app.example.com/reset?token=reset-token-456" in args[2]
        assert "60 хв." in args[2]

    @patch("app.mailer.send_email")
    def test_send_password_changed(self, mock_send_email):
        """Test send_password_changed calls send_email with correct content."""
        with patch("app.mailer.get_settings"):
            send_password_changed("user@example.com")

        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert args[0] == "user@example.com"
        assert args[1] == "Пароль змінено"
        assert "змінино" in args[2].lower() or "змінен" in args[2].lower()