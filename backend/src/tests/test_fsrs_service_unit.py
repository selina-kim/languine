"""Unit tests for FsrsService.

Tests the FSRS service logic with mocked database interactions:
- Logging reviews
- Updating card statistics (fail/success counts)
- Rescheduling cards based on FSRS algorithm
- Retrieving user review logs
- Managing optimization settings and parameters
- Error handling for invalid inputs and database errors

Run this test file:
    docker compose exec backend pytest src/tests/test_fsrs_service_unit.py -v

Run with coverage:
    docker compose exec backend pytest src/tests/test_fsrs_service_unit.py --cov=services.fsrs_service
"""

import pytest
import psycopg2
from unittest.mock import MagicMock, patch
from services.fsrs_service import FsrsService, CardNotFoundError, InvalidGradeError, DatabaseError
from services.fsrs.grade import Grade
from services.fsrs.learning_state import LearningState
from services.fsrs.scheduler import DEFAULT_PARAMETERS
from datetime import datetime, timezone

class TestFsrsServiceUnit:
    """Unit tests for FsrsService."""

    # --- get_user_review_logs and get_card_review_logs tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_get_user_review_logs(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        review_date = datetime.now(timezone.utc)

        mock_cursor.fetchall.return_value = [
            {
                "c_id": 123,
                "grade": Grade.Good,
                "review_date": review_date,
                "review_duration": 1000
            }
        ]
        
        logs = FsrsService.get_user_review_logs("user1")
        assert len(logs) == 1
        assert logs[0].card_id == "123"
        assert logs[0].grade == Grade.Good
        assert logs[0].review_datetime == review_date
        assert logs[0].review_duration == 1000

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_user_review_logs_empty(self, mock_get_db_cursor):
        """Test that get_user_review_logs returns an empty list when there are no logs."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        logs = FsrsService.get_user_review_logs("user1")
        assert logs == []
 
    @patch('services.fsrs_service.get_db_cursor')
    def test_get_user_review_logs_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.get_user_review_logs("user1")
    
    @patch('services.fsrs_service.get_db_cursor')
    def test_get_card_review_logs(self, mock_get_db_cursor):
        """Test that get_card_review_logs returns ReviewLog objects for a given card."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        review_date = datetime.now(timezone.utc)
        
        mock_cursor.fetchall.return_value = [
            {"grade": Grade.Good, "review_date": review_date, "review_duration": 500},
            {"grade": Grade.Again, "review_date": review_date, "review_duration": 1200},
        ]

        logs = FsrsService.get_card_review_logs(123)

        assert len(logs) == 2
        assert all(log.card_id == "123" for log in logs)
        assert logs[0].grade == Grade.Good
        assert logs[1].grade == Grade.Again
        assert logs[0].review_datetime == review_date
        assert logs[1].review_datetime == review_date
        assert logs[0].review_duration == 500
        assert logs[1].review_duration == 1200

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_card_review_logs_empty(self, mock_get_db_cursor):
        """Test that get_card_review_logs returns an empty list for an unreviewed card."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        logs = FsrsService.get_card_review_logs(123)
        assert logs == []

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_card_review_logs_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.get_card_review_logs(1)

    # --- log_review tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_log_review_success(self, mock_get_db_cursor):
        """Test logging a review successfully."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        card_id = 123
        grade = Grade.Good
        review_duration = 1000
        review_date = datetime.now(timezone.utc)
        
        expected_log = {
            'rl_id': 1,
            'c_id': card_id,
            'grade': grade,
            'review_date': review_date,
            'review_duration': review_duration
        }
        mock_cursor.fetchone.return_value = expected_log

        result = FsrsService.log_review(card_id, grade, review_duration)

        assert result == expected_log
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO Review_Logs" in args[0]
        # Check args are passed correctly
        assert args[1][0] == card_id
        assert args[1][1] == grade
        assert args[1][2] == review_duration

    def test_log_review_invalid_grade(self):
        """Test logging a review with an invalid grade raises error."""
        with pytest.raises(InvalidGradeError):
            # grade needs to be a valid Grade enum value (1-4)
            FsrsService.log_review(123, 5, 1000)

    @patch('services.fsrs_service.get_db_cursor')
    def test_log_review_db_error_raises_database_error(self, mock_get_db_cursor):
        """Test that a psycopg2.Error during log_review is wrapped in DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("DB failure")

        with pytest.raises(DatabaseError):
            FsrsService.log_review(123, Grade.Good, 1000)
    
    @patch('services.fsrs_service.get_db_cursor')
    def test_log_review_card_not_found(self, mock_get_db_cursor):
        """Test that logging a review for a non-existent card raises CardNotFoundError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        # Simulate FK violation when trying to log a review for a card_id that doesn't exist
        mock_cursor.execute.side_effect = psycopg2.errors.ForeignKeyViolation()

        with pytest.raises(CardNotFoundError):
            FsrsService.log_review(999999, Grade.Good, 1000)
    
    # --- update_deck_last_review_date tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_last_review_date(self, mock_get_db_cursor):
        """Test that update_deck_last_review_date issues the correct UPDATE."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        FsrsService.update_deck_last_review_date(123)

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Decks" in args[0]
        assert "last_reviewed = CURRENT_TIMESTAMP" in args[0]
        assert args[1] == (123,)
    
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_last_review_date_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.update_deck_last_review_date(1)

    # --- update_card_fail_success_count tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_card_fail_success_count_easy(self, mock_get_db_cursor):
        """Test updating success count for easy review."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        FsrsService.update_card_fail_success_count(123, Grade.Easy)
        
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Cards" in args[0]
        assert "successful_reps = successful_reps + 1" in args[0]

    @patch('services.fsrs_service.get_db_cursor')
    def test_update_card_fail_success_count_good(self, mock_get_db_cursor):
        """Test updating success count for good review."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        FsrsService.update_card_fail_success_count(123, Grade.Good)
        
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Cards" in args[0]
        assert "successful_reps = successful_reps + 1" in args[0]

    @patch('services.fsrs_service.get_db_cursor')
    def test_update_card_fail_success_count_hard(self, mock_get_db_cursor):
        """Test updating success count for hard review."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        FsrsService.update_card_fail_success_count(123, Grade.Hard)
        
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Cards" in args[0]
        assert "successful_reps = successful_reps + 1" in args[0]
        
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_card_fail_success_count_again(self, mock_get_db_cursor):
        """Test updating fail count for 'Again' review in Review state."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        FsrsService.update_card_fail_success_count(123, Grade.Again)
        
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Cards" in args[0]
        assert "fail_count = fail_count + 1" in args[0]
        assert "successful_reps = 0" in args[0]
   
    def test_update_card_fail_success_count_invalid_grade(self):
        """Test that update_card_fail_success_count rejects an invalid grade."""
        with pytest.raises(InvalidGradeError):
            # grade needs to be a valid Grade enum value (1-4)
            FsrsService.update_card_fail_success_count(123, 0)

    @patch('services.fsrs_service.get_db_cursor')
    def test_update_card_fail_success_count_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.update_card_fail_success_count(1, Grade.Good)

    # --- review_card tests ---
    @patch('services.fsrs_service.FsrsService.update_deck_due_cards')
    @patch('services.fsrs_service.get_db_cursor')
    @patch('services.fsrs_service.Scheduler')
    @patch('services.fsrs_service.Card')
    def test_review_card(self, mock_card_cls, mock_scheduler_cls, mock_get_db_cursor, mock_update_deck):
        """Test reviewing a card."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            {
                "learning_state": LearningState.Learning,
                "step": 0,
                "difficulty": 5.0,
                "stability": 2.0,
                "due_date": datetime(2030, 1, 1, tzinfo=timezone.utc),
                "last_review": datetime.now(timezone.utc),
                "desired_retention": 0.9,
                "fsrs_parameters": DEFAULT_PARAMETERS,
                "first_reviewed": datetime(2025, 1, 1, tzinfo=timezone.utc),
                "new_cards_per_day": 10,
                "u_id": "test-user-id",
            },
        ]

        # Mock objects
        mock_card_instance = MagicMock()
        mock_card_cls.return_value = mock_card_instance

        mock_scheduler_instance = MagicMock()
        mock_scheduler_cls.return_value = mock_scheduler_instance

        updated_card_mock = MagicMock()
        updated_card_mock.learning_state = LearningState.Review
        updated_card_mock.step = 1
        updated_card_mock.difficulty = 4.0
        updated_card_mock.stability = 3.0
        updated_card_mock.due = datetime.now(timezone.utc)
        updated_card_mock.last_review = datetime.now(timezone.utc)

        mock_scheduler_instance.review_card.return_value = (updated_card_mock, None)

        # Execute
        updated_fields = FsrsService.review_card(123, Grade.Good)

        # Assert: SELECT card info, UPDATE Cards
        assert mock_cursor.execute.call_count == 2
        assert "UPDATE Cards" in mock_cursor.execute.call_args_list[1][0][0]
        mock_update_deck.assert_called_once_with("test-user-id")
        assert updated_fields["learning_state"] == int(updated_card_mock.learning_state)
        assert updated_fields["step"] == updated_card_mock.step
        assert updated_fields["difficulty"] == float(updated_card_mock.difficulty)
        assert updated_fields["stability"] == float(updated_card_mock.stability)
        assert updated_fields["due_date"] == updated_card_mock.due
        assert updated_fields["last_review"] == updated_card_mock.last_review

    def test_review_card_invalid_grade_raises_error(self):
        """Test that review_card rejects an out-of-range grade before hitting the DB."""
        with pytest.raises(InvalidGradeError):
            FsrsService.review_card(123, 99)

    @patch('services.fsrs_service.get_db_cursor')
    def test_review_card_not_found_raises_error(self, mock_get_db_cursor):
        """Test that review_card raises CardNotFoundError when the card does not exist."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with pytest.raises(CardNotFoundError):
            FsrsService.review_card(999999, Grade.Good)

    @patch('services.fsrs_service.get_db_cursor')
    def test_review_card_db_error(self, mock_get_db_cursor):
        """Covers generic DB exception path inside review_card."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.review_card(1, Grade.Good)

    # --- reschedule_all_cards tests ---
    @patch.object(FsrsService, 'get_card_review_logs')
    @patch('services.fsrs_service.Scheduler')
    @patch('services.fsrs_service.get_db_cursor')
    def test_reschedule_all_cards(self, mock_get_db_cursor, mock_scheduler_cls, mock_get_card_review_logs):
        """Test that reschedule_all_cards fetches cards, reschedules each, and bulk-updates the DB."""
        due_date = datetime.now(timezone.utc)

        mock_cursor_1 = MagicMock()
        mock_cursor_1.fetchall.return_value = [{"c_id": 1, "due_date": due_date}]

        mock_cursor_2 = MagicMock()
        mock_cursor_2.fetchone.return_value = {
            "desired_retention": 0.9,
            "fsrs_parameters": list(DEFAULT_PARAMETERS),
        }

        mock_cursor_3 = MagicMock()

        # Helper to create a context manager mock for the DB cursor
        def make_ctx(cursor):
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=cursor)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        mock_get_db_cursor.side_effect = [
            make_ctx(mock_cursor_1),
            make_ctx(mock_cursor_2),
            make_ctx(mock_cursor_3),
        ]

        mock_get_card_review_logs.return_value = [
            MagicMock(
                card_id="1",
                grade=Grade.Good,
                review_datetime=datetime.now(timezone.utc),
                review_duration=1000,
            ), 
            MagicMock(
                card_id="1",
                grade=Grade.Easy,
                review_datetime=datetime.now(timezone.utc),
                review_duration=800,
            )
        ]

        mock_scheduler_instance = MagicMock()
        mock_scheduler_cls.return_value = mock_scheduler_instance
        mock_rescheduled_card = MagicMock()
        mock_scheduler_instance.reschedule_card.return_value = mock_rescheduled_card

        FsrsService.reschedule_all_cards("user1")

        # confirm get_card_review_logs is called exactly once 
        mock_get_card_review_logs.assert_called_once_with(1)
        # confirm reschedule_card is called exactly once for the card
        mock_scheduler_instance.reschedule_card.assert_called_once()
        # confirm executemany is called exactly once to update the card with the new schedule
        mock_cursor_3.executemany.assert_called_once()
        # confirm that the UPDATE statement is executed 
        args, _ = mock_cursor_3.executemany.call_args
        assert "UPDATE Cards" in args[0]

    @patch('services.fsrs_service.get_db_cursor')
    def test_reschedule_all_cards_db_error(self, mock_get_db_cursor):
        """Covers error handling at the top-level try/except in reschedule_all_cards."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.reschedule_all_cards("user1")

    # --- optimize_parameters tests ---
    @patch('services.fsrs_service.Optimizer')
    @patch.object(FsrsService, 'get_user_review_logs')
    def test_optimize_parameters(self, mock_get_logs, mock_optimizer_cls):
        """Test that optimize_parameters fetches logs, runs optimizer, and returns params."""
        mock_logs = [
            MagicMock(
                card_id="1",
                grade=Grade.Good,
                review_datetime=datetime.now(timezone.utc),
                review_duration=1000,
            ), 
            MagicMock(
                card_id="1",
                grade=Grade.Easy,
                review_datetime=datetime.now(timezone.utc),
                review_duration=800,
            ), 
            MagicMock(
                card_id="2",
                grade=Grade.Again,
                review_datetime=datetime.now(timezone.utc),
                review_duration=1500,
                )]
        mock_get_logs.return_value = mock_logs

        mock_optimizer_instance = MagicMock()
        mock_optimizer_cls.return_value = mock_optimizer_instance
        # Return the default set of parameters to confirm they are returned by the service method
        mock_optimizer_instance.compute_optimal_parameters.return_value = list(DEFAULT_PARAMETERS)

        result = FsrsService.optimize_parameters("user1")

        # confirm get_user_review_logs is called exactly once with the user_id
        mock_get_logs.assert_called_once_with("user1")
        # confirm the Optimizer is instantiated with the fetched logs
        mock_optimizer_cls.assert_called_once_with(review_logs=mock_logs)
        mock_optimizer_instance.compute_optimal_parameters.assert_called_once()
        # confirm the result from optimize_parameters is what the optimizer returned (the default parameters in this case)
        assert result == list(DEFAULT_PARAMETERS)

    # --- save_parameters tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_save_parameters(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        params = list(DEFAULT_PARAMETERS)
        FsrsService.save_parameters("user1", params)
        
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        
        # confirm that it runs the UPDATE statement with the new parameters and user_id
        assert "UPDATE Users" in args[0]
        assert "fsrs_parameters = %s" in args[0]
        assert args[1] == (params, "user1")

    @patch('services.fsrs_service.get_db_cursor')
    def test_save_parameters_db_error(self, mock_get_db_cursor):
        """Test that save_parameters wraps psycopg2 errors in DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("write failed")

        with pytest.raises(DatabaseError):
            FsrsService.save_parameters("user1", list(DEFAULT_PARAMETERS))

    # --- increment_review_counts tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_increment_review_counts(self, mock_get_db_cursor):
        """Test that increment_review_counts updates both count columns."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        FsrsService.increment_review_counts("user1", 10)

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Users" in args[0]
        assert "total_reviews = total_reviews + %s" in args[0]
        assert "reviews_since_last_optimize = reviews_since_last_optimize + %s" in args[0]
        assert args[1] == (10, 10, "user1")

    @patch('services.fsrs_service.get_db_cursor')
    def test_increment_review_counts_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.increment_review_counts("user1", 3)

    # --- should_optimize tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_should_optimize(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test that should_optimize returns True when auto_optimize is enabled, and False when disabled
        mock_cursor.fetchone.return_value = {"auto_optimize": True}
        assert FsrsService.should_optimize("user1") is True
        
        mock_cursor.fetchone.return_value = {"auto_optimize": False}
        assert FsrsService.should_optimize("user1") is False

    @patch('services.fsrs_service.get_db_cursor')
    def test_should_optimize_returns_false_when_no_user(self, mock_get_db_cursor):
        """Test that should_optimize returns False when the user row is not found."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = FsrsService.should_optimize("user-doesnt-exist")
        assert result is False

    @patch('services.fsrs_service.get_db_cursor')
    def test_should_optimize_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.should_optimize("user1")

    # --- cards_reviewed_since_last_optmize ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_cards_reviewed_since_last_optimize(self, mock_get_db_cursor):
        """Test that cards_reviewed_since_last_optimize returns the correct count."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"reviews_since_last_optimize": 42}

        result = FsrsService.cards_reviewed_since_last_optimize("user1")

        assert result == 42
        args, _ = mock_cursor.execute.call_args
        assert "reviews_since_last_optimize" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_cards_reviewed_since_last_optimize_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.cards_reviewed_since_last_optimize("user1")

    # --- total_cards_reviewed tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_total_cards_reviewed(self, mock_get_db_cursor):
        """Test that total_cards_reviewed returns the stored count."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"total_reviews": 250}

        result = FsrsService.total_cards_reviewed("user1")

        assert result == 250
        args, _ = mock_cursor.execute.call_args
        assert "total_reviews" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_total_cards_reviewed_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.total_cards_reviewed("user1")

    # --- num_reviews_per_optimize tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_num_reviews_per_optimize(self, mock_get_db_cursor):
        """Test that num_reviews_per_optimize returns the correct threshold."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"num_reviews_per_optimize": 300}

        result = FsrsService.num_reviews_per_optimize("user1")

        assert result == 300
        args, _ = mock_cursor.execute.call_args
        assert "num_reviews_per_optimize" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_num_reviews_per_optimize_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.num_reviews_per_optimize("user1")

    # -- reset_review_counts tests -- 
    @patch('services.fsrs_service.get_db_cursor')
    def test_reset_review_counts(self, mock_get_db_cursor):
        """Test that reset_review_counts sets reviews_since_last_optimize to 0."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        FsrsService.reset_review_counts("user1")

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Users" in args[0]
        assert "reviews_since_last_optimize = 0" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_reset_review_counts_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.reset_review_counts("user1")

    # --- reset_optimization_params tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_reset_optimization_params(self, mock_get_db_cursor):
        """Test that reset_optimization_params nulls out fsrs_parameters."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        FsrsService.reset_optimization_params("user1")

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Users" in args[0]
        assert "fsrs_parameters = NULL" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_reset_optimization_params_db_error(self, mock_get_db_cursor):
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.reset_optimization_params("user1")

    # --- get_due_cards tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_get_due_cards_success(self, mock_get_db_cursor):
        """Test that get_due_cards returns (num_due, cards) with card_id, due_date, and deck_id."""
        due_date = datetime.now(timezone.utc)

        mock_cursor_1 = MagicMock()
        mock_cursor_1.fetchone.return_value = {"new_cards_per_day": 10}

        mock_cursor_2 = MagicMock()
        mock_cursor_2.fetchall.return_value = [
            {"c_id": 1, "due_date": due_date, "d_id": 5},
            {"c_id": 2, "due_date": due_date, "d_id": 5},
        ]

        mock_cursor_3 = MagicMock()

        def make_ctx(cursor):
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=cursor)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        mock_get_db_cursor.side_effect = [
            make_ctx(mock_cursor_1),
            make_ctx(mock_cursor_2),
            make_ctx(mock_cursor_3),
        ]

        num_due, cards = FsrsService.get_due_cards("user1")

        assert num_due == 2
        assert len(cards) == 2
        assert cards[0] == {"card_id": 1, "due_date": due_date, "deck_id": 5}
        assert cards[1] == {"card_id": 2, "due_date": due_date, "deck_id": 5}

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_due_cards_empty(self, mock_get_db_cursor):
        """Test that get_due_cards returns (0, []) when no cards are due."""
        mock_cursor_1 = MagicMock()
        mock_cursor_1.fetchone.return_value = {"new_cards_per_day": 10}

        mock_cursor_2 = MagicMock()
        mock_cursor_2.fetchall.return_value = []

        mock_cursor_3 = MagicMock()

        def make_ctx(cursor):
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=cursor)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        mock_get_db_cursor.side_effect = [
            make_ctx(mock_cursor_1),
            make_ctx(mock_cursor_2),
            make_ctx(mock_cursor_3),
        ]

        num_due, cards = FsrsService.get_due_cards("user1")

        assert num_due == 0
        assert cards == []

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_due_cards_db_error(self, mock_get_db_cursor):
        """Test that get_due_cards wraps psycopg2 errors in DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.get_due_cards("user1")

    # --- get_num_due_cards tests ---
    @patch('services.fsrs_service.get_db_cursor')
    def test_get_num_due_cards_success(self, mock_get_db_cursor):
        """Test that get_num_due_cards returns the stored total_cards_due count."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"total_cards_due": 7}

        result = FsrsService.get_num_due_cards("user1")

        assert result == 7
        args, _ = mock_cursor.execute.call_args
        assert "total_cards_due" in args[0]
        assert args[1] == ("user1",)

    @patch('services.fsrs_service.get_db_cursor')
    def test_get_num_due_cards_db_error(self, mock_get_db_cursor):
        """Test that get_num_due_cards wraps psycopg2 errors in DatabaseError."""
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.get_num_due_cards("user1")

    # --- update_deck_due_cards tests ---

    @patch('services.fsrs_service.DeckService.list_user_decks')
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_due_cards_success(self, mock_get_db_cursor, mock_list_user_decks):
        """Test that update_deck_due_cards runs the correct queries and sums due counts across decks."""
        mock_list_user_decks.return_value = [
            {"d_id": 1, "new_cards_per_day": 10},
            {"d_id": 2, "new_cards_per_day": 5},
        ]
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {"total_due": 3},
            {"total_due": 2},
        ]

        FsrsService.update_deck_due_cards("user1")

        # 2 SELECT (count per deck) + 2 UPDATE Decks + 1 UPDATE Users = 5 execute calls
        assert mock_cursor.execute.call_count == 5
        # Confirm the final UPDATE Users uses the correct total (3 + 2 = 5)
        last_args, _ = mock_cursor.execute.call_args_list[4]
        assert "UPDATE Users" in last_args[0]
        assert "total_cards_due = %s" in last_args[0]
        assert last_args[1] == (5, "user1")

    @patch('services.fsrs_service.DeckService.list_user_decks')
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_due_cards_single_deck(self, mock_get_db_cursor, mock_list_user_decks):
        """Test update_deck_due_cards with a single deck produces the correct UPDATE calls."""
        mock_list_user_decks.return_value = [{"d_id": 7, "new_cards_per_day": 10}]
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"total_due": 4}

        FsrsService.update_deck_due_cards("user1")

        # SELECT count + UPDATE Decks + UPDATE Users = 3 calls
        assert mock_cursor.execute.call_count == 3

        # Second call should update the deck's due_cards to 4
        deck_update_args, _ = mock_cursor.execute.call_args_list[1]
        assert "UPDATE Decks" in deck_update_args[0]
        assert "due_cards = %s" in deck_update_args[0]
        assert deck_update_args[1] == (4, 7)

        # Third call should update the user's total_cards_due to 4
        user_update_args, _ = mock_cursor.execute.call_args_list[2]
        assert "UPDATE Users" in user_update_args[0]
        assert user_update_args[1] == (4, "user1")

    @patch('services.fsrs_service.DeckService.list_user_decks')
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_due_cards_no_decks(self, mock_get_db_cursor, mock_list_user_decks):
        """Test update_deck_due_cards sets total_cards_due to 0 when the user has no decks."""
        mock_list_user_decks.return_value = []
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        FsrsService.update_deck_due_cards("user1")

        # Only the UPDATE Users call (no decks to iterate over)
        assert mock_cursor.execute.call_count == 1
        args, _ = mock_cursor.execute.call_args
        assert "UPDATE Users" in args[0]
        assert args[1] == (0, "user1")

    @patch('services.fsrs_service.DeckService.list_user_decks')
    @patch('services.fsrs_service.get_db_cursor')
    def test_update_deck_due_cards_db_error(self, mock_get_db_cursor, mock_list_user_decks):
        """Test that a psycopg2.Error inside update_deck_due_cards is wrapped in DatabaseError."""
        mock_list_user_decks.return_value = [{"d_id": 1, "new_cards_per_day": 10}]
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.Error("db fail")

        with pytest.raises(DatabaseError):
            FsrsService.update_deck_due_cards("user1")
