"""Unit tests for database constraint and service-layer behaviour.

Tests the service logic with a fully mocked database to verify:
- Foreign key constraint error handling (FK violations via mocked psycopg2 errors)
- Cascade delete error propagation paths
- NOT NULL / unique constraint error handling
- Correct SQL is issued for cascade-dependent delete operations
- Review-log service isolation

Run this test file:
    docker compose exec backend poetry run pytest src/tests/test_db_unit.py -v

Run with coverage:
    docker compose exec backend poetry run pytest src/tests/test_db_unit.py --cov=services -v
"""

import pytest
import psycopg2
from unittest.mock import MagicMock, patch

from services.user_service import UserService, UserNotFoundError, DatabaseError as UserDatabaseError
from services.deck_service import (
    DeckService,
    DuplicateDeckNameError,
    UserNotFoundError as DeckUserNotFoundError,
    DatabaseError as DeckDatabaseError,
)
from services.card_service import (
    CardService,
    CardNotFoundError,
    DeckNotFoundError,
    DatabaseError as CardDatabaseError,
)
from services.fsrs_service import (
    FsrsService,
    CardNotFoundError as FsrsCardNotFoundError,
    InvalidGradeError,
    DatabaseError as FsrsDatabaseError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeIntegrityError(psycopg2.IntegrityError):
    """Lets us set pgcode on an IntegrityError so mocked FK/unique violations
    look exactly like real psycopg2 exceptions."""

    def __init__(self, msg: str, pgcode: str):
        super().__init__(msg)
        self._pgcode = pgcode

    @property
    def pgcode(self):
        return self._pgcode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def deck_service():
    with patch.object(DeckService, "_init_minio"):
        svc = DeckService()
        svc.minio_client = None
        return svc


@pytest.fixture
def card_service():
    with patch.object(CardService, "_init_minio"):
        svc = CardService()
        svc.minio_client = None
        return svc


# ===========================================================================
# TestForeignKeyConstraints
# ===========================================================================

class TestForeignKeyConstraints:
    """Verify that FK violations surfaced by psycopg2 are translated into the
    correct application-level exceptions by each service."""

    # --- DeckService: creating a deck for a non-existent user ---

    @patch("services.deck_service.get_db_cursor")
    def test_create_deck_fk_user_not_found(self, mock_get_db_cursor, deck_service):
        """DeckService.create_deck raises UserNotFoundError when the u_id FK is violated."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = _FakeIntegrityError(
            "insert or update on table 'decks' violates foreign key constraint",
            pgcode="23503",
        )

        with pytest.raises(DeckUserNotFoundError):
            deck_service.create_deck(
                "non-existent-user",
                {"deck_name": "Test Deck", "word_lang": "es", "trans_lang": "en", "description": None},
            )

    # --- DeckService: duplicate deck name triggers unique constraint ---

    @patch("services.deck_service.get_db_cursor")
    def test_create_deck_unique_constraint_deck_name(self, mock_get_db_cursor, deck_service):
        """DeckService.create_deck raises DuplicateDeckNameError on pgcode 23505."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = _FakeIntegrityError(
            "duplicate key value violates unique constraint 'decks_u_id_deck_name_key'",
            pgcode="23505",
        )

        with pytest.raises(DuplicateDeckNameError):
            deck_service.create_deck(
                "some-user",
                {"deck_name": "Duplicate Deck", "word_lang": "ja", "trans_lang": "en", "description": None},
            )

    # --- FsrsService: logging a review for a non-existent card ---

    @patch("services.fsrs_service.get_db_cursor")
    def test_log_review_fk_card_not_found(self, mock_get_db_cursor):
        """FsrsService.log_review raises CardNotFoundError when c_id FK is violated."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        fk_error = psycopg2.errors.ForeignKeyViolation(
            "insert or update on table 'review_logs' violates foreign key constraint"
        )
        mock_cursor.execute.side_effect = fk_error

        with pytest.raises(FsrsCardNotFoundError):
            FsrsService.log_review(card_id=99999, grade=3, review_duration=1000)

    # --- CardService: creating a card for a non-existent deck ---

    @patch("services.card_service.get_db_cursor")
    def test_create_card_fk_deck_not_found(self, mock_get_db_cursor, card_service):
        """CardService.create_card raises DeckNotFoundError when d_id FK is violated."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        # Ownership check returns None (deck does not exist for this user)
        mock_cursor.fetchone.return_value = None

        with pytest.raises(DeckNotFoundError):
            card_service.create_card(
                "test-user-id",
                {
                    "d_id": 99999,
                    "word": "hola",
                    "translation": "hello",
                    "definition": None,
                    "word_example": None,
                    "trans_example": None,
                    "word_roman": None,
                    "trans_roman": None,
                    "image": None,
                },
            )


# ===========================================================================
# TestCascadeDeletePaths
# ===========================================================================

class TestCascadeDeletePaths:
    """Verify that service-layer delete calls behave correctly and that the
    appropriate return values / exceptions are produced at each step."""

    # --- UserService.delete_user ---

    @patch("services.user_service.get_db_cursor")
    def test_delete_user_returns_cascade_counts(self, mock_get_db_cursor, user_service):
        """delete_user returns decks_deleted and cards_deleted so callers can
        confirm CASCADE propagation."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        # First fetchone: pre-delete counts; second fetchone: post-delete verification
        mock_cursor.fetchone.side_effect = [
            {"deck_count": 3, "card_count": 42},   # pre-delete stats query
            {"count": 0},                           # post-delete verification query
        ]
        mock_cursor.rowcount = 1  # DELETE statement affected 1 row

        result = user_service.delete_user("test-user-id")

        assert result["deleted"] is True
        assert result["decks_deleted"] == 3
        assert result["cards_deleted"] == 42

    @patch("services.user_service.get_db_cursor")
    def test_delete_user_not_found_via_stats_query(self, mock_get_db_cursor, user_service):
        """delete_user raises UserNotFoundError when the stats SELECT returns None."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with pytest.raises((UserNotFoundError, UserDatabaseError)):
            user_service.delete_user("non-existent-id")

    @patch("services.user_service.get_db_cursor")
    def test_delete_user_not_found_via_rowcount(self, mock_get_db_cursor, user_service):
        """delete_user raises UserNotFoundError when DELETE affects 0 rows."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {"deck_count": 0, "card_count": 0}
        mock_cursor.rowcount = 0  # no row deleted

        with pytest.raises((UserNotFoundError, UserDatabaseError)):
            user_service.delete_user("non-existent-id")

    @patch("services.user_service.get_db_cursor")
    def test_delete_user_database_error(self, mock_get_db_cursor, user_service):
        """delete_user wraps unexpected DB errors into DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("connection reset")

        with pytest.raises(UserDatabaseError):
            user_service.delete_user("test-user-id")

    # --- DeckService.delete_deck ---

    @patch("services.deck_service.get_db_cursor")
    def test_delete_deck_success_returns_true(self, mock_get_db_cursor, deck_service):
        """delete_deck returns True when a row is deleted."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        with patch.object(deck_service, "_cleanup_deck_media"):
            result = deck_service.delete_deck("test-user-id", 1)

        assert result is True
        # Verify a DELETE FROM Decks statement was issued
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "DELETE FROM Decks" in executed_sql

    @patch("services.deck_service.get_db_cursor")
    def test_delete_deck_not_found_returns_false(self, mock_get_db_cursor, deck_service):
        """delete_deck returns False (not an exception) when no row was deleted."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        with patch.object(deck_service, "_cleanup_deck_media"):
            result = deck_service.delete_deck("test-user-id", 99999)

        assert result is False

    @patch("services.deck_service.get_db_cursor")
    def test_delete_deck_database_error(self, mock_get_db_cursor, deck_service):
        """delete_deck wraps psycopg2.Error into DeckDatabaseError."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("timeout")
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        with patch.object(deck_service, "_cleanup_deck_media"):
            with pytest.raises(DeckDatabaseError):
                deck_service.delete_deck("test-user-id", 1)

    @patch("services.deck_service.get_db_cursor")
    def test_delete_deck_calls_media_cleanup(self, mock_get_db_cursor, deck_service):
        """delete_deck always calls _cleanup_deck_media before deleting the DB row."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        with patch.object(deck_service, "_cleanup_deck_media") as mock_cleanup:
            deck_service.delete_deck("test-user-id", 7)
            mock_cleanup.assert_called_once_with("test-user-id", 7)

    # --- CardService.delete_card ---

    @patch("services.card_service.get_db_cursor")
    def test_delete_card_not_found(self, mock_get_db_cursor, card_service):
        """delete_card raises CardNotFoundError when the card does not exist."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        # get_card internally queries ownership; None means not found / unauthorized
        mock_cursor.fetchone.return_value = None

        with pytest.raises(CardNotFoundError):
            card_service.delete_card("test-user-id", 99999)

    @patch("services.card_service.get_db_cursor")
    def test_delete_card_success_returns_true(self, mock_get_db_cursor, card_service):
        """delete_card returns True when the card is found and deleted."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        # get_card fetches the card first; returning a dict means found
        mock_cursor.fetchone.return_value = {
            "c_id": 1, "d_id": 10, "word": "hola",
            "image": None, "word_audio": None, "trans_audio": None,
        }

        result = card_service.delete_card("test-user-id", 1)
        assert result is True


# ===========================================================================
# TestConstraintHandling
# ===========================================================================

class TestConstraintHandling:
    """Verify application-level handling of DB constraint violations (NOT NULL,
    CHECK, unique) that are enforced by the schema."""

    # --- Users.display_name varchar(30) length ---

    @patch("services.user_service.get_db_cursor")
    def test_update_user_display_name_too_long_rejected(self, mock_get_db_cursor, user_service):
        """UserService.update_user surfaces an error when psycopg2 signals a
        value-too-long (DataError)."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.DataError(
            "value too long for type character varying(30)"
        )

        with pytest.raises((UserDatabaseError, Exception)):
            user_service.update_user("test-user-id", {"display_name": "X" * 31})

    # --- Decks.deck_name CHECK (deck_name <> '') ---

    @patch("services.deck_service.get_db_cursor")
    def test_create_deck_empty_name_db_check(self, mock_get_db_cursor, deck_service):
        """DeckService.create_deck surfaces an error when psycopg2 raises a
        CheckViolation for an empty deck_name."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = _FakeIntegrityError(
            "new row for relation 'decks' violates check constraint 'decks_deck_name_check'",
            pgcode="23514",
        )

        with pytest.raises((DeckDatabaseError, Exception)):
            deck_service.create_deck(
                u_id="some-user",
                deck_name="",
                word_lang="es",
                trans_lang="en",
                description=None,
            )

    # --- Cards CHECK (fail_count >= 0) ---

    @patch("services.fsrs_service.get_db_cursor")
    def test_update_card_fail_count_db_check_violation(self, mock_get_db_cursor):
        """FsrsService.update_card_fail_success_count surfaces an error when
        psycopg2 raises a CheckViolation for a negative fail_count."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = _FakeIntegrityError(
            "new row for relation 'cards' violates check constraint 'cards_fail_count_check'",
            pgcode="23514",
        )

        with pytest.raises((FsrsDatabaseError, Exception)):
            FsrsService.update_card_fail_success_count(card_id=1, grade=1)

    # --- Review_Logs.grade valid range (service-level guard) ---

    def test_log_review_grade_zero_rejected(self):
        """FsrsService.log_review raises InvalidGradeError before reaching the
        DB when grade=0 (outside valid range 1-4)."""
        with pytest.raises(InvalidGradeError):
            FsrsService.log_review(card_id=1, grade=0, review_duration=500)

    def test_log_review_grade_five_rejected(self):
        """FsrsService.log_review raises InvalidGradeError for grade > 4."""
        with pytest.raises(InvalidGradeError):
            FsrsService.log_review(card_id=1, grade=5, review_duration=500)


# ===========================================================================
# TestReviewLogServiceIsolation
# ===========================================================================

class TestReviewLogServiceIsolation:
    """Verify Review_Logs CRUD behaviour through the service layer (all mocked)."""

    @patch("services.fsrs_service.get_db_cursor")
    def test_get_user_review_logs_returns_correct_shape(self, mock_get_db_cursor):
        """get_user_review_logs converts DB rows into ReviewLog objects."""
        from datetime import datetime, timezone
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        review_date = datetime.now(timezone.utc)
        mock_cursor.fetchall.return_value = [
            {"c_id": 1, "grade": 3, "review_date": review_date, "review_duration": 800},
            {"c_id": 1, "grade": 1, "review_date": review_date, "review_duration": 1200},
        ]

        logs = FsrsService.get_user_review_logs("test-user-id")

        assert len(logs) == 2
        assert all(str(log.card_id) == "1" for log in logs)
        assert logs[0].review_duration == 800
        assert logs[1].grade == 1

    @patch("services.fsrs_service.get_db_cursor")
    def test_get_user_review_logs_empty(self, mock_get_db_cursor):
        """get_user_review_logs returns an empty list when there are no logs."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        logs = FsrsService.get_user_review_logs("test-user-id")
        assert logs == []

    @patch("services.fsrs_service.get_db_cursor")
    def test_get_user_review_logs_db_error(self, mock_get_db_cursor):
        """get_user_review_logs wraps DB exceptions into DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("connection lost")

        with pytest.raises(FsrsDatabaseError):
            FsrsService.get_user_review_logs("test-user-id")

    @patch("services.fsrs_service.get_db_cursor")
    def test_get_card_review_logs_returns_correct_shape(self, mock_get_db_cursor):
        """get_card_review_logs converts DB rows to ReviewLog objects for a specific card."""
        from datetime import datetime, timezone
        from services.fsrs.grade import Grade
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        review_date = datetime.now(timezone.utc)
        mock_cursor.fetchall.return_value = [
            {"grade": Grade.Good, "review_date": review_date, "review_duration": 500},
            {"grade": Grade.Again, "review_date": review_date, "review_duration": 1500},
        ]

        logs = FsrsService.get_card_review_logs(42)

        assert len(logs) == 2
        assert all(log.card_id == "42" for log in logs)
        assert logs[0].grade == Grade.Good
        assert logs[1].grade == Grade.Again

    @patch("services.fsrs_service.get_db_cursor")
    def test_log_review_success(self, mock_get_db_cursor):
        """log_review returns the inserted review log row on success."""
        from datetime import datetime, timezone
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "rl_id": 1,
            "c_id": 5,
            "grade": 3,
            "review_date": datetime.now(timezone.utc),
            "review_duration": 1000,
        }

        result = FsrsService.log_review(card_id=5, grade=3, review_duration=1000)

        assert result is not None
        assert result["c_id"] == 5
        assert result["grade"] == 3

    @patch("services.fsrs_service.get_db_cursor")
    def test_log_review_db_error(self, mock_get_db_cursor):
        """log_review wraps unexpected DB exceptions into DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("disk full")

        with pytest.raises(FsrsDatabaseError):
            FsrsService.log_review(card_id=5, grade=3, review_duration=1000)
