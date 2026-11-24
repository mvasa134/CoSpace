"""Unit tests for database utility functions."""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call

import pyodbc

from app.db import call, ping, _snake, _translate, _connect
from app.config import Settings


class TestSnakeCase:
    """Tests for _snake utility function."""

    def test_snake_case_simple(self):
        """Test converting simple CamelCase to snake_case."""
        assert _snake("CamelCase") == "camel_case"
        assert _snake("PascalCase") == "pascal_case"
        assert _snake("Simple") == "simple"

    def test_snake_case_with_acronyms(self):
        """Test converting with acronyms."""
        # The current implementation inserts _ before each capital letter
        assert _snake("XMLParser") == "x_m_l_parser"
        assert _snake("HTTPSConnection") == "h_t_t_p_s_connection"
        assert _snake("UserID") == "user_i_d"

    def test_snake_case_already_snake(self):
        """Test converting already snake_case."""
        assert _snake("already_snake") == "already_snake"
        assert _snake("lowercase") == "lowercase"

    def test_snake_case_numbers(self):
        """Test converting with numbers."""
        assert _snake("Version2") == "version2"
        assert _snake("V2API") == "v2_a_p_i"


class TestTranslateError:
    """Tests for _translate error mapping function."""

    def test_translate_raiserror_50001(self):
        """Test mapping error 50001 (user blocked)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]User blocked (50001)",)
        result = _translate(exc)
        assert result.status_code == 403

    def test_translate_raiserror_50002(self):
        """Test mapping error 50002 (blacklisted)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]In blacklist (50002)",)
        result = _translate(exc)
        assert result.status_code == 403

    def test_translate_raiserror_50003(self):
        """Test mapping error 50003 (workspace closed)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Workspace closed (50003)",)
        result = _translate(exc)
        assert result.status_code == 409

    def test_translate_raiserror_50004(self):
        """Test mapping error 50004 (not found)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Not found (50004)",)
        result = _translate(exc)
        assert result.status_code == 404

    def test_translate_unique_violation_2627(self):
        """Test mapping unique constraint violation (2627)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Duplicate key (2627)",)
        result = _translate(exc)
        assert result.status_code == 409
        assert "уже існує" in result.detail

    def test_translate_unique_violation_2601(self):
        """Test mapping unique constraint violation (2601)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Duplicate key (2601)",)
        result = _translate(exc)
        assert result.status_code == 409
        assert "уже існує" in result.detail

    def test_translate_fk_violation_547(self):
        """Test mapping foreign key violation (547)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]FK violation (547)",)
        result = _translate(exc)
        assert result.status_code == 409
        assert "зв'язку" in result.detail

    def test_translate_trigger_abort_3609(self):
        """Test mapping trigger abort (3609)."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Trigger abort (3609)",)
        result = _translate(exc)
        assert result.status_code == 409
        assert "конфлікт" in result.detail

    def test_translate_unknown_error(self):
        """Test unknown error returns 500."""
        exc = MagicMock()
        exc.args = ("[SQL Server]Some unknown error (99999)",)
        result = _translate(exc)
        assert result.status_code == 500
        assert "Помилка бази даних" in result.detail

    def test_translate_malformed_error(self):
        """Test malformed error message."""
        exc = MagicMock()
        exc.args = ("Some random error without SQL Server pattern",)
        result = _translate(exc)
        assert result.status_code == 500


class TestCall:
    """Tests for call function."""

    @patch("app.db._connect")
    def test_call_no_params(self, mock_connect):
        """Test calling procedure with no parameters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("Id",), ("Name",)]
        mock_cursor.fetchall.return_value = [(1, "Test")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_TestProc")

        assert result == [{"id": 1, "name": "Test"}]
        mock_cursor.execute.assert_called_once_with("EXEC dbo.usp_TestProc")

    @patch("app.db._connect")
    def test_call_with_params(self, mock_connect):
        """Test calling procedure with parameters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("Id",)]
        mock_cursor.fetchall.return_value = [(1,)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_TestProc", Param1="value1", Param2=123)

        assert result == [{"id": 1}]
        # Check that parameters were passed
        args, kwargs = mock_cursor.execute.call_args
        assert "value1" in args
        assert 123 in args

    @patch("app.db._connect")
    def test_call_one_true(self, mock_connect):
        """Test calling procedure with one=True returns single dict."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("Id",), ("Name",)]
        mock_cursor.fetchall.return_value = [(1, "Test")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_TestProc", one=True)

        assert result == {"id": 1, "name": "Test"}

    @patch("app.db._connect")
    def test_call_one_true_empty(self, mock_connect):
        """Test calling procedure with one=True and no results."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("ID",)]
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_TestProc", one=True)

        assert result is None

    @patch("app.db._connect")
    def test_call_none_params_filtered(self, mock_connect):
        """Test that None parameters are filtered out."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("Id",)]
        mock_cursor.fetchall.return_value = [(1,)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_TestProc", Param1="value", Param2=None, Param3=123)

        assert result == [{"id": 1}]
        # Should only have Param1 and Param3
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        assert "@Param1=?" in sql
        assert "@Param3=?" in sql
        assert "@Param2=?" not in sql

    @patch("app.db._connect")
    def test_call_commit_on_success(self, mock_connect):
        """Test that commit is called on success."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        call("usp_TestProc")

        mock_conn.commit.assert_called_once()

    @patch("app.db._connect")
    def test_call_rollback_on_error(self, mock_connect):
        """Test that rollback is called on error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = pyodbc.Error("Test error")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with pytest.raises(Exception):
            call("usp_TestProc")

        mock_conn.rollback.assert_called_once()

    @patch("app.db._connect")
    def test_call_connection_closed(self, mock_connect):
        """Test that connection is closed in finally block."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        call("usp_TestProc")

        mock_conn.close.assert_called_once()


class TestPing:
    """Tests for ping function."""

    @patch("app.db._connect")
    def test_ping_success(self, mock_connect):
        """Test successful ping."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        ping()  # Should not raise

        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("app.db._connect")
    def test_ping_closes_connection(self, mock_connect):
        """Test that ping closes connection."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        ping()

        mock_conn.close.assert_called_once()


class TestConnect:
    """Tests for _connect function."""

    @patch("app.db.pyodbc.connect")
    @patch("app.db.get_settings")
    @patch("app.db.time.sleep")
    def test_connect_success_first_try(self, mock_sleep, mock_get_settings, mock_pyodbc_connect):
        """Test successful connection on first try."""
        mock_settings = MagicMock()
        mock_settings.conn_str = "test-connection-string"
        mock_get_settings.return_value = mock_settings

        mock_conn = MagicMock()
        mock_pyodbc_connect.return_value = mock_conn

        conn = _connect()

        assert conn == mock_conn
        mock_pyodbc_connect.assert_called_once_with("test-connection-string", autocommit=False)
        mock_sleep.assert_not_called()

    @patch("app.db.pyodbc.connect")
    @patch("app.db.get_settings")
    @patch("app.db.time.sleep")
    def test_connect_retry_on_failure(self, mock_sleep, mock_get_settings, mock_pyodbc_connect):
        """Test retry logic on connection failure."""
        mock_settings = MagicMock()
        mock_settings.conn_str = "test-connection-string"
        mock_get_settings.return_value = mock_settings

        # Fail first 2 times, succeed on 3rd
        mock_pyodbc_connect.side_effect = [
            pyodbc.Error("Fail 1"),
            pyodbc.Error("Fail 2"),
            MagicMock(),  # Success
        ]

        conn = _connect()

        assert mock_pyodbc_connect.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(5)

    @patch("app.db.pyodbc.connect")
    @patch("app.db.get_settings")
    @patch("app.db.time.sleep")
    def test_connect_all_retries_fail(self, mock_sleep, mock_get_settings, mock_pyodbc_connect):
        """Test all retries fail raises HTTPException."""
        mock_settings = MagicMock()
        mock_settings.conn_str = "test-connection-string"
        mock_get_settings.return_value = mock_settings

        mock_pyodbc_connect.side_effect = pyodbc.Error("Always fails")

        with pytest.raises(Exception) as exc_info:
            _connect()

        assert "БД недоступна" in str(exc_info.value)
        assert mock_pyodbc_connect.call_count == 4


class TestCallIntegration:
    """Integration-style tests for call function with various scenarios."""

    @patch("app.db._connect")
    def test_call_multiple_result_sets(self, mock_connect):
        """Test handling multiple result sets (if any)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("Id",), ("Name",)]
        mock_cursor.fetchall.return_value = [(1, "A"), (2, "B")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_GetList")

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["name"] == "B"

    @patch("app.db._connect")
    def test_call_no_result_set(self, mock_connect):
        """Test procedure with no result set (e.g., INSERT/UPDATE)."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_InsertSomething", Name="Test")

        assert result == []

    @patch("app.db._connect")
    def test_call_column_names_case_conversion(self, mock_connect):
        """Test that column names are converted to snake_case."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("UserId",), ("UserName",), ("EmailAddress",)]
        mock_cursor.fetchall.return_value = [(1, "John", "john@example.com")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = call("usp_GetUser")

        assert result == [{
            "user_id": 1,
            "user_name": "John",
            "email_address": "john@example.com"
        }]