"""Integration tests for FSRS routes.

Tests the review logging and session management endpoints with actual HTTP requests and responses.
These tests verify the complete request/response cycle including:
- Logging single card reviews (POST /reviews)
- Ending review sessions (POST /end-review)
- Input validation (types, range check for grades)
- Error handling (missing fields, invalid IDs)
- Authentication/Authorization checks
- Database interactions for logging and updates

All tests in this file are marked as integration tests.

Run this test file:
    docker compose exec backend pytest src/tests/test_fsrs_routes_integration.py -v -m integration

Run with coverage:
    docker compose exec backend pytest src/tests/test_fsrs_routes_integration.py --cov=routes.fsrs -m integration
"""

import pytest
import json
from db import get_db_cursor
from services.fsrs.grade import Grade
from services.fsrs_service import FsrsService

pytestmark = pytest.mark.integration

def get_any_card_id():
    """Helper to get a valid card ID from the test database."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT c_id FROM Cards LIMIT 1")
        row = cursor.fetchone()
        return row['c_id'] if row else None

# ==================== Log Review Route Tests ====================

def test_log_review_success(client, auth_headers):
    """Test successful review logging."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"
    
    data = {
        "card_id": card_id,
        "grade": 3,
        "review_duration": 1000
    }
    
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    if response.status_code != 201:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.get_data(as_text=True)}")

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['c_id'] == card_id
    assert result['grade'] == 3
    assert result['review_duration'] == 1000

def test_log_review_all_valid_grades(client, auth_headers):
    """Test that all valid grades (1-4) are accepted by the review endpoint."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    for grade in [1, 2, 3, 4]:
        data = {"card_id": card_id, "grade": grade, "review_duration": 1000}
        response = client.post(
            "/reviews",
            data=json.dumps(data),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code == 201, (
            f"Grade {grade} was unexpectedly rejected: {response.get_data(as_text=True)}"
        )
        result = json.loads(response.data)
        assert result["grade"] == grade

def test_log_review_updates_card_fsrs_state(client, auth_headers):
    """Test that POST /reviews updates the card's FSRS fields in the database."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    data = {"card_id": card_id, "grade": 3, "review_duration": 750}

    # check initial FSRS state before the review
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT learning_state, stability, difficulty, due_date, last_review FROM Cards WHERE c_id = %s",
            (card_id,)
        )
        init_card_state = cursor.fetchone()

    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT learning_state, stability, difficulty, due_date, last_review FROM Cards WHERE c_id = %s",
            (card_id,)
        )
        updated = cursor.fetchone()

    assert updated["learning_state"] is not None
    assert updated["stability"] is not None
    assert updated["difficulty"] is not None
    assert updated["due_date"] is not None
    assert updated["last_review"] is not None

    assert updated["last_review"] > init_card_state["last_review"] if init_card_state["last_review"] else True
    assert updated["due_date"] > init_card_state["due_date"] if init_card_state["due_date"] else True
    assert updated["stability"] != init_card_state["stability"] 
    assert updated["difficulty"] != init_card_state["difficulty"] 
    assert updated["learning_state"] != init_card_state["learning_state"]

def test_log_review_updates_deck_last_reviewed(client, auth_headers):
    """Test that POST /reviews updates the deck's last_reviewed timestamp."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    data = {"card_id": card_id, "grade": 3, "review_duration": 500}

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT d.last_reviewed
            FROM Decks d
            JOIN Cards c ON c.d_id = d.d_id
            WHERE c.c_id = %s
            """,
            (card_id,)
        )
        init_deck_last_reviewed = cursor.fetchone()

    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT d.last_reviewed
            FROM Decks d
            JOIN Cards c ON c.d_id = d.d_id
            WHERE c.c_id = %s
            """,
            (card_id,)
        )
        result = cursor.fetchone()

    assert result["last_reviewed"] is not None
    assert result["last_reviewed"] > init_deck_last_reviewed["last_reviewed"] if init_deck_last_reviewed["last_reviewed"] else True

def test_log_review_again_increments_fail_count(client, auth_headers):
    """Test that grading Again (1) increments the card's fail_count."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"
    with get_db_cursor() as cursor:
        cursor.execute("SELECT fail_count FROM Cards WHERE c_id = %s", (card_id,))
        before_fail_count = cursor.fetchone()["fail_count"]

    data = {"card_id": card_id, "grade": Grade.Again, "review_duration": 2000}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    after = {}
    with get_db_cursor() as cursor:
        cursor.execute("SELECT fail_count, successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        row = cursor.fetchone()
        after["fail_count"] = row["fail_count"]
        after["successful_reps"] = row["successful_reps"]

    assert after["fail_count"] == before_fail_count + 1
    assert after["successful_reps"] == 0

def test_log_review_easy_increments_success_count(client, auth_headers):
    """Test that grading Easy (4) increments the card's successful_reps."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        before = cursor.fetchone()["successful_reps"]

    data = {"card_id": card_id, "grade": Grade.Easy, "review_duration": 800}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        after = cursor.fetchone()["successful_reps"]

    assert after == before + 1

def test_log_review_good_increments_success_count(client, auth_headers):
    """Test that grading Good (3) increments the card's successful_reps."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        before = cursor.fetchone()["successful_reps"]

    data = {"card_id": card_id, "grade": Grade.Good, "review_duration": 800}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        after = cursor.fetchone()["successful_reps"]

    assert after == before + 1

def test_log_review_hard_increments_success_count(client, auth_headers):
    """Test that grading Hard (2) increments the card's successful_reps."""
    card_id = get_any_card_id()
    assert card_id is not None, "No cards available for testing"

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        before = cursor.fetchone()["successful_reps"]

    data = {"card_id": card_id, "grade": Grade.Hard, "review_duration": 800}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 201

    with get_db_cursor() as cursor:
        cursor.execute("SELECT successful_reps FROM Cards WHERE c_id = %s", (card_id,))
        after = cursor.fetchone()["successful_reps"]

    assert after == before + 1

def test_log_review_no_auth(client):
    """Test logging review without authentication."""
    data = {
        "card_id": 1,
        "grade": 3,
        "review_duration": 1000
    }
    
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 401

def test_log_review_no_json_body(client, auth_headers):
    """Test that POST /reviews with a non-JSON body returns 400."""
    response = client.post(
        "/reviews",
        data="not json",
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result

def test_log_review_missing_card_id(client, auth_headers):
    """Test that POST /reviews without a card_id field returns 400."""
    data = {"grade": 3, "review_duration": 1000}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "card_id is required" in result["error"]

def test_log_review_missing_grade(client, auth_headers):
    """Test that POST /reviews without a grade field returns 400."""
    card_id = get_any_card_id()
    data = {"card_id": card_id, "review_duration": 1000}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "grade is required" in result["error"]

def test_log_review_missing_review_duration(client, auth_headers):
    """Test that POST /reviews without a review_duration field returns 400."""
    card_id = get_any_card_id()
    data = {"card_id": card_id, "grade": 3}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "review_duration is required" in result["error"]

def test_log_review_card_not_found(client, auth_headers):
    """Test logging review for non-existent card."""
    data = {
        "card_id": 99999999, # Assuming this doesn't exist
        "grade": 3,
        "review_duration": 1000
    }
    
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_log_review_card_id_not_int(client, auth_headers):
    """Test logging review with invalid card_id type."""
    data = {
        "card_id": "not-an-int",
        "grade": Grade.Good,
        "review_duration": 1000
    }
    
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result

def test_log_review_invalid_grade(client, auth_headers):
    """Test logging review with invalid grade value."""
    card_id = get_any_card_id()
    data = {
        "card_id": card_id,
        "grade": 5, # Invalid, must be 1-4
        "review_duration": 1000
    }
    
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400

def test_log_review_grade_not_integer(client, auth_headers):
    """Test that POST /reviews with a non-integer grade returns 400."""
    card_id = get_any_card_id()
    data = {"card_id": card_id, "grade": "hard", "review_duration": 1000}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "grade must be an integer" in result["error"]

def test_log_review_duration_not_integer(client, auth_headers):
    """Test that POST /reviews with a non-integer review_duration returns 400."""
    card_id = get_any_card_id()
    data = {"card_id": card_id, "grade": 3, "review_duration": "fast"}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "review_duration must be an integer" in result["error"]

def test_log_review_database_error(client, auth_headers, monkeypatch):
    """Test that a DatabaseError raised by the service returns HTTP 500."""
    from routes.fsrs import fsrs_service
    from services.fsrs_service import DatabaseError

    def raise_db_error(*args, **kwargs):
        raise DatabaseError("simulated db failure")

    monkeypatch.setattr(fsrs_service, 'log_review', raise_db_error)

    card_id = get_any_card_id()
    data = {"card_id": card_id, "grade": 3, "review_duration": 1000}
    response = client.post(
        "/reviews",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 500
    result = json.loads(response.data)
    assert "Database error" in result["error"]

# ==================== End Review Session Route Tests ====================

def test_end_review_success(client, auth_headers):
    """Test ending review session successfully."""
    data = {
        "total_cards_reviewed": 10
    }
    
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "message" in result

def test_end_review_missing_data(client, auth_headers):
    """Test ending review session with empty data."""
    response = client.post(
        "/end-review",
        data=json.dumps({}), # Empty
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400

def test_end_review_invalid_type(client, auth_headers):
    """Test ending review session with invalid data type."""
    data = {
        "total_cards_reviewed": "ten"
    }
    
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 400

def test_end_review_no_auth(client):
    """Test ending review session without authentication."""
    data = {"total_cards_reviewed": 5}

    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json'
    )

    assert response.status_code == 401

def test_end_review_increments_total_reviews(client, auth_headers, monkeypatch):
    """Test that POST /end-review increments the user's total_reviews count"""
    from routes.fsrs import fsrs_service

    # The first POST must trigger optimization (so reviews_since_last_optimize resets to 0);
    # the second must not (so the counter increments normally to 7).
    # An iterator gives True once then False, regardless of DB state.
    should_optimize_seq = iter([True, False])
    monkeypatch.setattr(fsrs_service, 'update_deck_due_cards', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'should_optimize', lambda *a, **kw: next(should_optimize_seq))
    monkeypatch.setattr(fsrs_service, 'cards_reviewed_since_last_optimize', lambda *a, **kw: 9999)
    monkeypatch.setattr(fsrs_service, 'num_reviews_per_optimize', lambda *a, **kw: 100)
    monkeypatch.setattr(fsrs_service, 'total_cards_reviewed', lambda *a, **kw: 9999)
    monkeypatch.setattr(fsrs_service, 'optimize_parameters', lambda *a, **kw: [0.1] * 21)
    monkeypatch.setattr(fsrs_service, 'save_parameters', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'reschedule_all_cards', lambda *a, **kw: None)
    # increment_review_counts and reset_review_counts stay real so DB changes are verified below

    with get_db_cursor() as cursor:
        cursor.execute("SELECT total_reviews, reviews_since_last_optimize FROM Users WHERE u_id = 'test-user-id'")
        before = cursor.fetchone()

    data = {"total_cards_reviewed": 7}
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 200

    with get_db_cursor() as cursor:
        cursor.execute("SELECT total_reviews, reviews_since_last_optimize FROM Users WHERE u_id = 'test-user-id'")
        after = cursor.fetchone()

    assert after['total_reviews'] == before['total_reviews'] + 7
    assert after['reviews_since_last_optimize'] != before['reviews_since_last_optimize']
    # optimization was triggered → reset_review_counts set it back to 0
    assert after['reviews_since_last_optimize'] == 0

    # now if we review 7 more cards, it should increment reviews_since_last_optimize to 7 again
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 200
    with get_db_cursor() as cursor:
        cursor.execute("SELECT total_reviews, reviews_since_last_optimize FROM Users WHERE u_id = 'test-user-id'")
        after_second = cursor.fetchone()
    assert after_second['total_reviews'] == after['total_reviews'] + 7
    assert after_second['reviews_since_last_optimize'] == after['reviews_since_last_optimize'] + 7

def test_end_review_response_contains_optimized_flag(client, auth_headers):
    """Test that the end-review response always includes the parameters_optimized flag."""
    data = {"total_cards_reviewed": 1}
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 200
    result = json.loads(response.data)
    assert "parameters_optimized" in result
    assert isinstance(result["parameters_optimized"], bool)

def test_end_review_no_json_body(client, auth_headers):
    """Test that POST /end-review with a non-JSON body returns 400."""
    response = client.post(
        "/end-review",
        data="not json",
        headers=auth_headers
    )
    assert response.status_code == 400
    result = json.loads(response.data)
    assert "error" in result

def test_end_review_database_error(client, auth_headers, monkeypatch):
    """Test that a DatabaseError raised by the service returns HTTP 500 on /end-review."""
    from routes.fsrs import fsrs_service
    from services.fsrs_service import DatabaseError

    def raise_db_error(*args, **kwargs):
        raise DatabaseError("simulated db failure")

    monkeypatch.setattr(fsrs_service, 'update_deck_due_cards', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'increment_review_counts', raise_db_error)

    data = {"total_cards_reviewed": 5}
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 500
    result = json.loads(response.data)
    assert "Database error" in result["error"]

def test_end_review_triggers_optimization(client, auth_headers, monkeypatch):
    """Test that optimization runs, parameters_optimized is True, and new params are saved to DB."""
    from routes.fsrs import fsrs_service

    monkeypatch.setattr(fsrs_service, 'update_deck_due_cards', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'increment_review_counts', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'should_optimize', lambda *a, **kw: True)
    monkeypatch.setattr(fsrs_service, 'cards_reviewed_since_last_optimize', lambda *a, **kw: 9999)
    monkeypatch.setattr(fsrs_service, 'num_reviews_per_optimize', lambda *a, **kw: 100)
    monkeypatch.setattr(fsrs_service, 'total_cards_reviewed', lambda *a, **kw: 9999)
    # optimize_parameters and save_parameters stay real to verify the DB write
    monkeypatch.setattr(fsrs_service, 'reset_review_counts', lambda *a, **kw: None)
    monkeypatch.setattr(fsrs_service, 'reschedule_all_cards', lambda *a, **kw: None)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT fsrs_parameters FROM Users WHERE u_id = 'test-user-id'")
        params_before = cursor.fetchone()['fsrs_parameters']

    data = {"total_cards_reviewed": 10}
    response = client.post(
        "/end-review",
        data=json.dumps(data),
        content_type='application/json',
        headers=auth_headers
    )
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["parameters_optimized"] is True

    with get_db_cursor() as cursor:
        cursor.execute("SELECT fsrs_parameters FROM Users WHERE u_id = 'test-user-id'")
        params_after = cursor.fetchone()['fsrs_parameters']

    assert params_after is not None
    assert params_after != params_before

# ==================== Get Due Cards Route Tests ====================

def get_card_id_for_test_user():
    """Helper to get a valid card ID owned by the test user."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT c.c_id FROM Cards c
            JOIN Decks d ON c.d_id = d.d_id
            WHERE d.u_id = 'test-user-id'
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return row['c_id'] if row else None

def set_all_test_user_cards_not_due():
    """Set all test user cards as previously reviewed with a future due_date so none are treated as new or overdue."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE Cards
            SET first_reviewed = NOW() - INTERVAL '7 days',
                due_date       = NOW() + INTERVAL '1 day'
            WHERE d_id IN (SELECT d_id FROM Decks WHERE u_id = 'test-user-id')
            """
        )

def set_card_due_in_past(card_id):
    """Set a card's due_date to one day in the past."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE Cards SET due_date = NOW() - INTERVAL '1 day' WHERE c_id = %s",
            (card_id,)
        )

def set_card_as_reviewed(card_id):
    """Mark a card as previously reviewed by setting first_reviewed, so it is treated as a review card (not a new card)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE Cards SET first_reviewed = NOW() - INTERVAL '7 days' WHERE c_id = %s",
            (card_id,)
        )

def reset_card_first_review(card_id):
    """Clear first_reviewed so a card is treated as new again."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE Cards SET first_reviewed = NULL WHERE c_id = %s",
            (card_id,)
        )

# ==================== Update Deck Due Cards Service Tests ====================
# update_deck_due_cards is an internal service method (not a dedicated HTTP
# route) so these tests call it directly against the real database.

_USER_ID = "test-user-id"


def _get_deck_due_cards(deck_id: int) -> int:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT due_cards_count FROM Decks WHERE d_id = %s", (deck_id,))
        return cursor.fetchone()["due_cards_count"]


def _get_user_total_due_cards_count() -> int:
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT total_due_cards_count FROM Users WHERE u_id = %s", (_USER_ID,)
        )
        return cursor.fetchone()["total_due_cards_count"]


def test_update_deck_due_cards_overdue_review_cards(db_setup):
    """Overdue review cards increment due_cards_count and total_due_cards_count."""
    deck_id = db_setup
    set_all_test_user_cards_not_due()

    card_id = get_card_id_for_test_user()
    assert card_id is not None
    set_card_due_in_past(card_id)

    FsrsService.update_deck_due_cards(_USER_ID)

    assert _get_deck_due_cards(deck_id) >= 1
    assert _get_user_total_due_cards_count() >= 1


def test_update_deck_due_cards_no_due_cards(db_setup):
    """When no cards are due, due_cards_count and total_due_cards_count are both set to 0."""
    deck_id = db_setup
    set_all_test_user_cards_not_due()

    FsrsService.update_deck_due_cards(_USER_ID)

    assert _get_deck_due_cards(deck_id) == 0
    assert _get_user_total_due_cards_count() == 0


def test_update_deck_due_cards_new_cards_capped_at_limit(db_setup):
    """New cards (first_reviewed IS NULL) are counted but capped at new_cards_per_day."""
    deck_id = db_setup
    NEW_LIMIT = 2

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE Users SET new_cards_per_day = %s WHERE u_id = %s",
            (NEW_LIMIT, _USER_ID),
        )
        cursor.execute(
            "UPDATE Cards SET first_reviewed = NULL WHERE d_id = %s", (deck_id,)
        )

    try:
        FsrsService.update_deck_due_cards(_USER_ID)

        deck_due = _get_deck_due_cards(deck_id)
        assert deck_due <= NEW_LIMIT, (
            f"Expected due_cards_count to be capped at {NEW_LIMIT}, got {deck_due}"
        )
        assert _get_user_total_due_cards_count() == deck_due
    finally:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE Users SET new_cards_per_day = 10 WHERE u_id = %s", (_USER_ID,)
            )


def test_update_deck_due_cards_total_is_sum_across_decks(db_setup):
    """total_due_cards_count equals the sum of due_cards_count across all of the user's decks."""
    deck1_id = db_setup
    set_all_test_user_cards_not_due()

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO Decks (u_id, deck_name, word_lang, trans_lang)
            VALUES (%s, 'Test Deck 2', 'fr', 'en')
            RETURNING d_id
            """,
            (_USER_ID,),
        )
        deck2_id = cursor.fetchone()["d_id"]
        cursor.execute(
            """
            INSERT INTO Cards (d_id, word, translation, first_reviewed, due_date)
            VALUES (%s, 'bonjour', 'hello',
                    NOW() - INTERVAL '7 days', NOW() - INTERVAL '1 day')
            """,
            (deck2_id,),
        )

    try:
        FsrsService.update_deck_due_cards(_USER_ID)

        deck1_due = _get_deck_due_cards(deck1_id)
        deck2_due = _get_deck_due_cards(deck2_id)
        total = _get_user_total_due_cards_count()

        assert deck2_due >= 1, "Overdue card in deck 2 should be counted"
        assert total == deck1_due + deck2_due, (
            f"total_due_cards_count ({total}) should equal deck1 ({deck1_due}) + deck2 ({deck2_due})"
        )
    finally:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM Decks WHERE d_id = %s", (deck2_id,))


def test_update_deck_due_cards_updates_are_persisted(db_setup):
    """Verify that the due_cards_count and total_due_cards_count writes are committed to the database."""
    deck_id = db_setup
    set_all_test_user_cards_not_due()

    # Seed sentinel values so we can confirm they are overwritten
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE Decks SET due_cards_count = 999 WHERE d_id = %s", (deck_id,))
        cursor.execute("UPDATE Users SET total_due_cards_count = 999 WHERE u_id = %s", (_USER_ID,))

    FsrsService.update_deck_due_cards(_USER_ID)

    assert _get_deck_due_cards(deck_id) != 999
    assert _get_user_total_due_cards_count() != 999


