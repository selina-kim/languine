"""
SQL injection integration tests.

End-to-end checks against real PostgreSQL confirming that:
- Injection strings are stored literally, not executed.
- No extra rows are inserted after injection attempts.
- No tables are dropped.
- HTTP error responses do not expose SQL/psycopg2 internals.
"""

import pytest

pytestmark = pytest.mark.integration

SQL_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE Users; --",
    "' UNION SELECT * FROM Users --",
    "admin'--",
    "1; SELECT 1--",
]


class TestSQLInjectionIntegration:
    """End-to-end injection tests against real PostgreSQL."""

    # ── PUT /users/me ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_update_user_payload_stored_literally(self, client, auth_headers, db_setup, payload):
        """Injection payload in display_name is persisted and returned verbatim."""
        resp = client.put(
            "/users/me",
            json={"display_name": payload},
            headers=auth_headers,
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["user"]["display_name"] == payload

    def test_update_user_email_field_not_applied(self, client, auth_headers, db_setup):
        """
        The 'email' key is not in the update allowlist — it must be discarded
        and the stored email must remain unchanged.
        """
        original_email = client.get(
            "/users/me", headers=auth_headers
        ).get_json()["email"]

        resp = client.put(
            "/users/me",
            json={"display_name": "Legit Name", "email": "hacked@evil.com"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["user"]["email"] == original_email

    # ── POST /decks/new ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_create_deck_name_stored_literally(self, client, auth_headers, db_setup, payload):
        """Injection payload in deck_name is stored and returned as a literal string."""
        resp = client.post(
            "/decks/new",
            json={"deck_name": payload, "word_lang": "EN", "trans_lang": "ES"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["deck"]["deck_name"] == payload

    def test_tautology_in_deck_name_returns_only_that_deck(self, client, auth_headers, db_setup):
        """
        A tautology payload in deck_name must not cause the GET endpoint to
        return more rows than expected.
        """
        payload = "' OR '1'='1"
        create_resp = client.post(
            "/decks/new",
            json={"deck_name": payload, "word_lang": "EN", "trans_lang": "ES"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert create_resp.status_code == 201
        new_id = create_resp.get_json()["deck"]["d_id"]

        fetch_resp = client.get(f"/decks/{new_id}", headers=auth_headers)
        assert fetch_resp.status_code == 200
        assert fetch_resp.get_json()["deck"]["deck_name"] == payload

    # ── POST /decks/<id>/card ────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_create_card_word_stored_literally(self, client, auth_headers, deck_id, payload):
        """Injection payload in 'word' is stored and returned as a literal string."""
        resp = client.post(
            f"/decks/{deck_id}/card",
            json={"word": payload, "translation": "test"},
            headers=auth_headers,
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["card"]["word"] == payload

    # ── Row-count integrity ──────────────────────────────────────────────────

    def test_injection_does_not_insert_extra_user_rows(self, client, auth_headers, db_setup):
        """
        Multiple injection attempts via PUT /users/me must never create extra
        rows in the Users table.
        """
        from db import get_db_cursor

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Users WHERE u_id = 'test-user-id'")
            before = cur.fetchone()["cnt"]
        assert before == 1

        for payload in SQL_PAYLOADS:
            client.put(
                "/users/me",
                json={"display_name": payload},
                headers=auth_headers,
                content_type="application/json",
            )

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Users WHERE u_id = 'test-user-id'")
            after = cur.fetchone()["cnt"]

        assert after == before, (
            f"Expected {before} row(s), found {after} after injection attempts"
        )

    def test_delete_user_does_not_drop_tables(self, client, auth_headers, db_setup):
        """
        DELETE /users/me must delete the user account row only — the Users
        table itself must still exist and be query-able afterwards.
        """
        from db import get_db_cursor

        resp = client.delete("/users/me", headers=auth_headers)
        assert resp.status_code == 200

        # Table must still exist
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM Users")
            result = cur.fetchone()
        assert result is not None, "Users table must still exist after DELETE /users/me"

        # The specific user row must be gone
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM Users WHERE u_id = 'test-user-id'"
            )
            assert cur.fetchone()["cnt"] == 0

    # ── Error response opacity ───────────────────────────────────────────────

    def test_error_response_does_not_expose_sql_details(self, client, auth_headers, db_setup):
        """
        A database-level error (here: duplicate deck name) must not leak
        psycopg2 error text, SQL fragments, or constraint names in the HTTP
        response body.
        """
        body = {
            "deck_name": "SQL Leak Test Deck",
            "word_lang": "EN",
            "trans_lang": "ES",
        }
        r1 = client.post(
            "/decks/new", json=body, headers=auth_headers, content_type="application/json"
        )
        assert r1.status_code == 201

        r2 = client.post(
            "/decks/new", json=body, headers=auth_headers, content_type="application/json"
        )
        assert r2.status_code == 409

        raw = r2.get_data(as_text=True).lower()
        forbidden_fragments = [
            "psycopg",
            "unique_violation",
            "sqlstate",
            "detail:",
            "pg_class",
            "duplicate key",
            "constraint",
        ]
        for fragment in forbidden_fragments:
            assert fragment not in raw, (
                f"Response leaks SQL/DB detail '{fragment}' in: {raw[:300]}"
            )

    def test_update_and_retrieve_injection_round_trip(self, client, auth_headers, db_setup):
        """
        Store an injection payload then retrieve it — must survive a DB
        round-trip without corruption or unintended side effects.
        """
        original_email = client.get("/users/me", headers=auth_headers).get_json()["email"]

        payload = "'; UPDATE Users SET x=1--"

        put_resp = client.put(
            "/users/me",
            json={"display_name": payload},
            headers=auth_headers,
            content_type="application/json",
        )
        assert put_resp.status_code == 200

        get_resp = client.get("/users/me", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.get_json()
        # Stored value must be the literal payload string
        assert data["display_name"] == payload
        # Email must be unchanged
        assert data["email"] == original_email
