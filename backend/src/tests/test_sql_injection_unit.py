"""
SQL injection unit tests.

Verifies injection safety at the service layer using mocked cursors:
- Payloads are bound as parameters, never interpolated into SQL strings.
- Field allowlists discard unrecognised keys before any DB call.
- Dynamic UPDATE queries are built with psycopg2.sql.Composable objects.
"""

import pytest
from unittest.mock import MagicMock, patch

SQL_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE Users; --",
    "' UNION SELECT * FROM Users --",
    "admin'--",
    "1; SELECT * FROM Users WHERE '1'='1",
]


class TestSQLInjectionUnit:
    """Verify injection safety at the service layer using mocked cursors."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _make_cursor(self, return_row=None):
        """Return a context-manager cursor mock whose fetchone() yields *return_row*."""
        m = MagicMock()
        m.__enter__ = MagicMock(return_value=m)
        m.__exit__ = MagicMock(return_value=False)
        m.fetchone.return_value = return_row
        return m

    def _fake_user_row(self, display_name="ok"):
        return {
            "u_id": "u1",
            "email": "a@b.com",
            "display_name": display_name,
            "timezone": "UTC",
            "new_cards_per_day": 20,
            "desired_retention": 0.9,
            "auto_optimize": False,
            "num_reviews_per_optimize": 100,
            "total_reviews": 0,
            "reviews_since_last_optimize": 0,
        }

    # ── UserService.update_user ──────────────────────────────────────────────

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_update_user_payload_bound_as_parameter(self, payload):
        """
        Injection payload in display_name must appear only as a bound value
        in cursor.execute(), never embedded directly in the query string.
        """
        from services.user_service import UserService

        cursor = self._make_cursor(self._fake_user_row(display_name=payload))

        with patch("services.user_service.get_db_cursor", return_value=cursor):
            UserService().update_user("u1", {"display_name": payload})

        cursor.execute.assert_called_once()
        args = cursor.execute.call_args[0]   # positional args: (query, params)
        params = list(args[1])
        assert payload in params, (
            f"Payload must be a bound parameter; got params={params}"
        )

    def test_update_user_allowlist_blocks_email_field(self):
        """
        'email' is not in allowed_fields so it must be silently discarded —
        the UPDATE param list must contain only the allowed field value plus
        the WHERE user_id.
        """
        from services.user_service import UserService

        cursor = self._make_cursor(self._fake_user_row())

        with patch("services.user_service.get_db_cursor", return_value=cursor):
            UserService().update_user(
                "u1",
                {"display_name": "safe", "email": "hacked@evil.com", "u_id": "injected"},
            )

        args = cursor.execute.call_args[0]
        params = list(args[1])
        # 1 allowed field value ("safe") + user_id for WHERE = 2 params total
        assert len(params) == 2, f"Expected 2 params, got {len(params)}: {params}"
        assert "hacked@evil.com" not in params
        assert "injected" not in params

    def test_update_user_all_unlisted_keys_raises_valueerror(self):
        """
        Sending only non-allowlisted keys must raise ValueError before any
        DB call is made.
        """
        from services.user_service import UserService

        cursor = self._make_cursor(None)

        with patch("services.user_service.get_db_cursor", return_value=cursor):
            with pytest.raises(ValueError, match="No valid fields"):
                UserService().update_user("u1", {"email": "x@x.com", "u_id": "injected"})

        cursor.execute.assert_not_called()

    def test_update_user_query_uses_sql_composable(self):
        """
        The UPDATE query object passed to cursor.execute must be a
        psycopg2.sql.Composable (built via psycopg2.sql.SQL / Identifier),
        not a plain str produced by an f-string.
        """
        from psycopg2 import sql as pgsql
        from services.user_service import UserService

        cursor = self._make_cursor(self._fake_user_row())

        with patch("services.user_service.get_db_cursor", return_value=cursor):
            UserService().update_user("u1", {"display_name": "ok"})

        query_arg = cursor.execute.call_args[0][0]
        assert isinstance(query_arg, pgsql.Composable), (
            "UPDATE query must be a psycopg2.sql.Composable object, not a plain string. "
            f"Got: {type(query_arg)}"
        )

    def test_update_user_multiple_allowed_fields_correct_param_count(self):
        """Each allowed field produces exactly one bound parameter plus the WHERE user_id."""
        from services.user_service import UserService

        cursor = self._make_cursor(self._fake_user_row())

        with patch("services.user_service.get_db_cursor", return_value=cursor):
            UserService().update_user(
                "u1",
                {
                    "display_name": "Alice",
                    "timezone": "America/Toronto",
                    "new_cards_per_day": 30,
                },
            )

        args = cursor.execute.call_args[0]
        params = list(args[1])
        # 3 field values + 1 WHERE user_id = 4 params
        assert len(params) == 4
