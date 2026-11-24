"""Unit tests for audit module."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.audit import audit


class TestAudit:
    """Tests for audit function."""

    @patch("app.audit.call")
    def test_audit_success(self, mock_call):
        """Test successful audit logging."""
        audit(1, "test.action")
        mock_call.assert_called_once_with("usp_AuditLog_Add", UserId=1, Action="test.action")

    @patch("app.audit.call")
    def test_audit_action_truncated(self, mock_call):
        """Test that long actions are truncated to 255 chars."""
        long_action = "x" * 300
        audit(1, long_action)
        mock_call.assert_called_once()
        args, kwargs = mock_call.call_args
        assert kwargs["Action"] == "x" * 255

    @patch("app.audit.call")
    def test_audit_http_exception_handled(self, mock_call, caplog):
        """Test that HTTPException from call is caught and logged."""
        mock_call.side_effect = HTTPException(500, "DB Error")

        with caplog.at_level("WARNING"):
            audit(1, "test.action")

        assert "audit failed" in caplog.text
        assert "test.action" in caplog.text

    @patch("app.audit.call")
    def test_audit_other_exception_handled(self, mock_call, caplog):
        """Test that other exceptions are caught and logged."""
        mock_call.side_effect = Exception("Unexpected error")

        with caplog.at_level("WARNING"):
            audit(1, "test.action")

        assert "audit failed" in caplog.text