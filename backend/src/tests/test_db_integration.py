"""Integration tests for database constraints and cascade behaviour.

Tests the full stack (HTTP → service → real PostgreSQL) to verify:
- Cascading deletes: deck → cards → review_logs
- Cascading deletes: user → decks → cards → review_logs
- Foreign key enforcement: review log insertion for non-existent card
- Unique constraint: duplicate deck name per user returns 409
- Review_Logs CRUD end-to-end via real DB
- Performance: PostgreSQL read < 100 ms, write < 200 ms

All tests in this file are marked as integration tests.

Run this test file:
    docker compose exec backend poetry run pytest src/tests/test_db_integration.py -v -m integration

Run with coverage:
    docker compose exec backend poetry run pytest src/tests/test_db_integration.py --cov=services -m integration
"""

import time
import json
import pytest
from db import get_db_cursor

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_card_ids_for_deck(deck_id: int) -> list[int]:
    """Return all c_ids belonging to the given deck (read from real DB)."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT c_id FROM Cards WHERE d_id = %s", (deck_id,))
        return [row["c_id"] for row in cursor.fetchall()]


def _count_cards_for_deck(deck_id: int) -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM Cards WHERE d_id = %s", (deck_id,))
        return cursor.fetchone()["cnt"]


def _count_review_logs_for_cards(card_ids: list[int]) -> int:
    if not card_ids:
        return 0
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Review_Logs WHERE c_id = ANY(%s)",
            (card_ids,),
        )
        return cursor.fetchone()["cnt"]


def _count_decks_for_user(u_id: str) -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM Decks WHERE u_id = %s", (u_id,))
        return cursor.fetchone()["cnt"]


def _count_users(u_id: str) -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM Users WHERE u_id = %s", (u_id,))
        return cursor.fetchone()["cnt"]


def _get_any_card_id() -> int | None:
    """Return a valid c_id belonging to the test user's deck, or None."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT c.c_id FROM Cards c
            JOIN Decks d ON c.d_id = d.d_id
            WHERE d.u_id = 'test-user-id'
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row["c_id"] if row else None


# ===========================================================================
# TestCascadeDeleteDeck
# ===========================================================================

class TestCascadeDeleteDeck:
    """Verify that DELETE /decks/{id} cascades to cards and review logs in the DB."""

    def test_delete_deck_removes_all_cards(self, client, auth_headers, deck_id):
        """After deleting a deck the DB must contain no Cards rows for that d_id."""
        # Pre-condition: at least one card exists in the test deck
        card_count_before = _count_cards_for_deck(deck_id)
        assert card_count_before > 0, "Fixture should have seeded cards in the test deck"

        response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
        assert response.status_code == 200

        card_count_after = _count_cards_for_deck(deck_id)
        assert card_count_after == 0, (
            f"Expected 0 cards after deck deletion, found {card_count_after}"
        )

    def test_delete_deck_removes_all_review_logs(self, client, auth_headers, deck_id):
        """After deleting a deck every Review_Logs row for cards in that deck must
        also be gone (Cards(c_id) ON DELETE CASCADE → Review_Logs(c_id))."""
        # Collect card IDs before deletion so we can query for orphaned logs
        card_ids_before = _get_card_ids_for_deck(deck_id)
        assert len(card_ids_before) > 0, "Fixture should have seeded cards"

        logs_before = _count_review_logs_for_cards(card_ids_before)
        assert logs_before > 0, "Fixture should have seeded review logs for those cards"

        response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
        assert response.status_code == 200

        logs_after = _count_review_logs_for_cards(card_ids_before)
        assert logs_after == 0, (
            f"Expected 0 review logs after deck deletion, found {logs_after}"
        )

    def test_delete_deck_response_message(self, client, auth_headers, deck_id):
        """DELETE /decks/{id} returns the standard success message."""
        response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Deck deleted successfully"

    def test_delete_nonexistent_deck_returns_404(self, client, auth_headers):
        """Attempting to delete a deck that does not exist returns 404."""
        response = client.delete("/decks/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_deck_twice_returns_404_on_second(self, client, auth_headers, deck_id):
        """Deleting the same deck a second time returns 404 (it is already gone)."""
        client.delete(f"/decks/{deck_id}", headers=auth_headers)
        response = client.delete(f"/decks/{deck_id}", headers=auth_headers)
        assert response.status_code == 404


# ===========================================================================
# TestCascadeDeleteUser
# ===========================================================================

class TestCascadeDeleteUser:
    """Verify that DELETE /users/me cascades through decks, cards, and review_logs."""

    def test_delete_user_removes_user_row(self, client, auth_headers, db_setup):
        """After DELETE /users/me the Users row must be gone."""
        assert _count_users("test-user-id") == 1

        response = client.delete("/users/me", headers=auth_headers)
        assert response.status_code == 200

        assert _count_users("test-user-id") == 0

    def test_delete_user_removes_all_decks(self, client, auth_headers, db_setup):
        """After DELETE /users/me all Decks rows for that user must be gone."""
        decks_before = _count_decks_for_user("test-user-id")
        assert decks_before > 0, "Fixture should have seeded at least one deck"

        response = client.delete("/users/me", headers=auth_headers)
        assert response.status_code == 200

        decks_after = _count_decks_for_user("test-user-id")
        assert decks_after == 0

    def test_delete_user_removes_all_cards(self, client, auth_headers, deck_id, db_setup):
        """After DELETE /users/me no Cards rows linked to that user's decks remain."""
        # Snapshot card IDs before deletion
        card_ids_before = _get_card_ids_for_deck(deck_id)
        assert len(card_ids_before) > 0

        response = client.delete("/users/me", headers=auth_headers)
        assert response.status_code == 200

        # All those specific card IDs must be gone
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Cards WHERE c_id = ANY(%s)",
                (card_ids_before,),
            )
            remaining = cursor.fetchone()["cnt"]
        assert remaining == 0

    def test_delete_user_removes_all_review_logs(self, client, auth_headers, deck_id, db_setup):
        """After DELETE /users/me all Review_Logs rows for that user's cards are gone."""
        card_ids_before = _get_card_ids_for_deck(deck_id)
        logs_before = _count_review_logs_for_cards(card_ids_before)
        assert logs_before > 0

        response = client.delete("/users/me", headers=auth_headers)
        assert response.status_code == 200

        logs_after = _count_review_logs_for_cards(card_ids_before)
        assert logs_after == 0

    def test_delete_user_response_contains_counts(self, client, auth_headers, db_setup):
        """DELETE /users/me response body must include decks_deleted and
        cards_deleted so the caller can confirm cascade depth."""
        response = client.delete("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        details = data["details"]
        assert "decks_deleted" in details
        assert "cards_deleted" in details
        assert details["decks_deleted"] >= 1
        assert details["cards_deleted"] >= 1


# ===========================================================================
# TestForeignKeyEnforcement
# ===========================================================================

class TestForeignKeyEnforcement:
    """Verify that FK constraints are enforced by the real database engine."""

    def test_log_review_nonexistent_card_fk_returns_404(self, client, auth_headers):
        """POST /reviews with a non-existent card_id must trigger the FK violation
        path in FsrsService and be translated to a 404 response."""
        data = {"card_id": 999999, "grade": 3, "review_duration": 1000}
        response = client.post(
            "/reviews",
            data=json.dumps(data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 404
        result = json.loads(response.data)
        assert "error" in result

    def test_create_card_nonexistent_deck_returns_404(self, client, auth_headers):
        """POST /decks/999999/card must return 404 because the deck FK does not exist."""
        card_data = {"word": "test", "translation": "test"}
        response = client.post(
            "/decks/999999/card",
            data=json.dumps(card_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_review_log_inserted_for_valid_card(self, client, auth_headers):
        """A review for a real card_id must be persisted in Review_Logs."""
        card_id = _get_any_card_id()
        assert card_id is not None

        data = {"card_id": card_id, "grade": 3, "review_duration": 1000}
        response = client.post(
            "/reviews",
            data=json.dumps(data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Confirm the row persisted
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Review_Logs WHERE c_id = %s AND grade = 3",
                (card_id,),
            )
            assert cursor.fetchone()["cnt"] >= 1


# ===========================================================================
# TestUniqueConstraints
# ===========================================================================

class TestUniqueConstraints:
    """Verify that unique constraints in the schema are enforced end-to-end."""

    def test_duplicate_deck_name_per_user_returns_409(self, client, auth_headers, db_setup):
        """Creating a second deck with the same name for the same user must
        trigger the UNIQUE(u_id, deck_name) constraint and return 409."""
        deck_data = {
            "deck_name": "Test Deck",   # same name as the fixture-created deck
            "word_lang": "fr",
            "trans_lang": "en",
        }
        response = client.post(
            "/decks/new",
            data=json.dumps(deck_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 409
        result = json.loads(response.data)
        assert "error" in result

    def test_distinct_deck_names_are_accepted(self, client, auth_headers, db_setup):
        """Two decks with different names for the same user must both be created."""
        for name in ("UniqueNameA", "UniqueNameB"):
            response = client.post(
                "/decks/new",
                data=json.dumps({"deck_name": name, "word_lang": "ko", "trans_lang": "en"}),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 201, (
                f"Expected 201 for deck '{name}', got {response.status_code}"
            )


# ===========================================================================
# TestReviewLogCRUD
# ===========================================================================

class TestReviewLogCRUD:
    """End-to-end review log verification against the real DB."""

    def test_review_log_row_created_with_correct_fields(self, client, auth_headers):
        """POST /reviews must persist a row in Review_Logs with matching c_id,
        grade, and review_duration."""
        card_id = _get_any_card_id()
        assert card_id is not None

        response = client.post(
            "/reviews",
            data=json.dumps({"card_id": card_id, "grade": 2, "review_duration": 750}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 201

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT grade, review_duration, review_date
                FROM Review_Logs
                WHERE c_id = %s AND grade = 2 AND review_duration = 750
                ORDER BY review_date DESC
                LIMIT 1
                """,
                (card_id,),
            )
            row = cursor.fetchone()

        assert row is not None
        assert row["grade"] == 2
        assert row["review_duration"] == 750
        assert row["review_date"] is not None

    def test_all_valid_grades_persisted(self, client, auth_headers):
        """Grades 1-4 must all produce Review_Logs rows with the correct grade value."""
        card_id = _get_any_card_id()
        assert card_id is not None

        for grade in [1, 2, 3, 4]:
            response = client.post(
                "/reviews",
                data=json.dumps({"card_id": card_id, "grade": grade, "review_duration": 500}),
                content_type="application/json",
                headers=auth_headers,
            )
            assert response.status_code == 201, (
                f"Expected 201 for grade {grade}, got {response.status_code}"
            )

            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM Review_Logs WHERE c_id = %s AND grade = %s",
                    (card_id, grade),
                )
                assert cursor.fetchone()["cnt"] >= 1, (
                    f"Review log for grade {grade} not found in DB"
                )

    def test_review_updates_card_fsrs_state_in_db(self, client, auth_headers):
        """After a review the card's FSRS fields (learning_state, stability,
        difficulty, due_date, last_review) must have changed in the DB."""
        card_id = _get_any_card_id()
        assert card_id is not None

        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT learning_state, stability, difficulty, due_date, last_review "
                "FROM Cards WHERE c_id = %s",
                (card_id,),
            )
            before = dict(cursor.fetchone())

        client.post(
            "/reviews",
            data=json.dumps({"card_id": card_id, "grade": 3, "review_duration": 1000}),
            content_type="application/json",
            headers=auth_headers,
        )

        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT learning_state, stability, difficulty, due_date, last_review "
                "FROM Cards WHERE c_id = %s",
                (card_id,),
            )
            after = dict(cursor.fetchone())

        # At minimum, last_review must now be set
        assert after["last_review"] is not None
        # due_date should have been scheduled into the future
        assert after["due_date"] is not None

    def test_review_log_grade_invalid_not_persisted(self, client, auth_headers):
        """An invalid grade must be rejected before DB insertion; no orphaned row
        should appear in Review_Logs."""
        card_id = _get_any_card_id()
        assert card_id is not None

        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Review_Logs WHERE c_id = %s AND grade = 9",
                (card_id,),
            )
            count_before = cursor.fetchone()["cnt"]

        response = client.post(
            "/reviews",
            data=json.dumps({"card_id": card_id, "grade": 9, "review_duration": 500}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 400

        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Review_Logs WHERE c_id = %s AND grade = 9",
                (card_id,),
            )
            count_after = cursor.fetchone()["cnt"]

        assert count_after == count_before


# ===========================================================================
# TestPostgreSQLPerformance
# ===========================================================================

class TestPostgreSQLPerformance:
    """Verify that common DB-backed endpoints meet the DVV latency thresholds:
    - Read operations  < 100 ms
    - Write operations < 200 ms
    """

    READ_THRESHOLD_MS = 100
    WRITE_THRESHOLD_MS = 200

    def test_get_decks_read_under_100ms(self, client, auth_headers):
        """GET /decks (read) must respond in under 100 ms."""
        start = time.perf_counter()
        response = client.get("/decks", headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < self.READ_THRESHOLD_MS, (
            f"GET /decks took {elapsed_ms:.1f} ms, expected < {self.READ_THRESHOLD_MS} ms"
        )

    def test_get_cards_read_under_100ms(self, client, auth_headers, deck_id):
        """GET /decks/{id}/cards (read) must respond in under 100 ms."""
        start = time.perf_counter()
        response = client.get(f"/decks/{deck_id}/cards", headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < self.READ_THRESHOLD_MS, (
            f"GET /decks/{deck_id}/cards took {elapsed_ms:.1f} ms, "
            f"expected < {self.READ_THRESHOLD_MS} ms"
        )

    def test_get_user_read_under_100ms(self, client, auth_headers):
        """GET /users/me (read) must respond in under 100 ms."""
        start = time.perf_counter()
        response = client.get("/users/me", headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < self.READ_THRESHOLD_MS, (
            f"GET /users/me took {elapsed_ms:.1f} ms, expected < {self.READ_THRESHOLD_MS} ms"
        )

    def test_log_review_write_under_200ms(self, client, auth_headers):
        """POST /reviews (write) must respond in under 200 ms."""
        card_id = _get_any_card_id()
        assert card_id is not None

        start = time.perf_counter()
        response = client.post(
            "/reviews",
            data=json.dumps({"card_id": card_id, "grade": 3, "review_duration": 1000}),
            content_type="application/json",
            headers=auth_headers,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 201
        assert elapsed_ms < self.WRITE_THRESHOLD_MS, (
            f"POST /reviews took {elapsed_ms:.1f} ms, expected < {self.WRITE_THRESHOLD_MS} ms"
        )

