from typing import Optional
from datetime import datetime, timezone
from db import get_db_cursor
from services.fsrs.card import Card
from services.fsrs.grade import Grade
from services.fsrs.learning_state import LearningState
from services.fsrs.optimizer import Optimizer
from services.fsrs.review_log import ReviewLog
from services.fsrs.scheduler import Scheduler
import psycopg2


class CardNotFoundError(Exception):
    """Card id does not exist in Cards table."""
    pass


class InvalidGradeError(Exception):
    """Grade value is not one of the allowed values (1–4)."""
    pass


class DatabaseError(Exception):
    """Any other database error."""
    pass


VALID_GRADES = set(Grade)


class FsrsService:
    """Service for FSRS-related database operations."""

    # ---  Helper Functions ---
    @staticmethod
    def get_user_review_logs(user_id: str) -> list[ReviewLog]:
        """
        Fetch all review logs for a given user across all their decks and cards.

        Args:
            user_id: The ID of the user whose review logs to retrieve.

        Returns:
            List of ReviewLog objects ordered by review date ascending.

        Raises:
            DatabaseError: On any database error.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT rl.c_id, rl.grade, rl.review_date, rl.review_duration
                    FROM Review_Logs rl
                    JOIN Cards c ON rl.c_id = c.c_id
                    JOIN Decks d ON c.d_id = d.d_id
                    WHERE d.u_id = %s
                    ORDER BY rl.review_date ASC
                    """,
                    (user_id,),
                )
                rows = cursor.fetchall()

            return [
                ReviewLog(
                    card_id=str(row["c_id"]),
                    grade=Grade(row["grade"]),
                    review_datetime=row["review_date"],
                    review_duration=row["review_duration"],
                )
                for row in rows
            ]
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

    @staticmethod
    def get_card_review_logs(card_id: int) -> list[ReviewLog]:
        """
        Fetch all review logs for a given card.

        Args:
            card_id: The ID of the card whose review logs to retrieve.
        Returns:
            List of ReviewLog objects ordered by review date ascending.
        Raises:
            DatabaseError: On any database error.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT grade, review_date, review_duration
                    FROM Review_Logs
                    WHERE c_id = %s
                    ORDER BY review_date ASC
                    """,
                    (card_id,),
                )
                rows = cursor.fetchall()

            return [
                ReviewLog(
                    card_id=str(card_id),
                    grade=Grade(row["grade"]),
                    review_datetime=row["review_date"],
                    review_duration=row["review_duration"],
                )
                for row in rows
            ]
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

    # --- Core FSRS Functions --

    @staticmethod
    def log_review(card_id: int, grade: int, review_duration: Optional[int] = None) -> dict:
        """
        Insert a review log entry into the Review_Logs table.

        Args:
            card_id:         ID of the card being reviewed.
            grade:           User's self-assessed recall quality (1=Again, 2=Hard, 3=Good, 4=Easy).
            review_duration: Time taken to recall the card in milliseconds.

        Returns:
            dict with the newly created review log row.

        Raises:
            InvalidGradeError: If grade is not in {1, 2, 3, 4}.
            CardNotFoundError: If card_id does not exist.
            DatabaseError:    On any other database error.
        """
        if grade not in VALID_GRADES:
            raise InvalidGradeError(f"Grade must be one of {sorted(VALID_GRADES)}, got {grade}.")
        
        try:
            # no need to insert review_date, as it defaults to CURRENT_TIMESTAMP
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO Review_Logs (c_id, grade, review_duration)
                    VALUES (%s, %s, %s)
                    RETURNING rl_id, c_id, grade, review_date, review_duration
                    """,
                    (card_id, grade, review_duration),
                )
                row = cursor.fetchone()
                return dict(row)

        except psycopg2.errors.ForeignKeyViolation:
            raise CardNotFoundError(f"Card with id {card_id} does not exist.")
        except psycopg2.Error as e:
            raise DatabaseError(str(e))
    
    @staticmethod
    def update_deck_last_review_date(card_id: int):
        """
        Update the last_reviewed of the deck containing the specified card.

        Args:
            card_id: ID of the card whose deck's last review date needs to be updated.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Decks
                    SET last_reviewed = CURRENT_TIMESTAMP
                    WHERE d_id = (
                        SELECT d_id
                        FROM Cards
                        WHERE c_id = %s
                    )
                    """,
                    (card_id,),
                )
        except psycopg2.Error as e:
            raise DatabaseError(str(e))
        
    @staticmethod
    def update_card_fail_success_count(card_id: int, grade: int):
        """
        Update the fail_count and success_count of the specified card based on the latest review log.

        Args:
            card_id: ID of the card whose fail/success counts need to be updated.
            grade:   The grade from the latest review log.
        """
        if grade not in VALID_GRADES:
            raise InvalidGradeError(f"Grade must be one of {sorted(VALID_GRADES)}, got {grade}.")

        try:
            with get_db_cursor(commit=True) as cursor:
                
                # if the grade is again, we consider it a failed recall
                # we increment the fail_count and reset the successful_reps to 0 since it's a failed recall
                if grade == Grade.Again:
                    cursor.execute(
                        """
                        UPDATE Cards
                        SET fail_count = fail_count + 1, 
                            successful_reps = 0 
                        WHERE c_id = %s
                        """,
                        (card_id,),
                    )
                # otherwise, we consider it a successful recall
                else:
                    cursor.execute(
                        """
                        UPDATE Cards
                        SET successful_reps = successful_reps + 1
                        WHERE c_id = %s
                        """,
                        (card_id,),
                    )
                        
        except psycopg2.Error as e:
            raise DatabaseError(str(e))
    
    @staticmethod
    def review_card(card_id: int, grade: int, review_datetime: Optional[datetime] = None) -> dict:
        """
        Update the following fields of the specified card based on the latest review:
            - learning_state
            - step 
            - difficulty 
            - stability
            - due_date 
            - last_review

        Args:
            card_id: ID of the card that was reviewed.
            grade:   The grade from the latest review log.

        Returns:
            dict with the updated card fields.
        """
        if grade not in VALID_GRADES:
            raise InvalidGradeError(f"Grade must be one of {sorted(VALID_GRADES)}, got {grade}.")

        try:
            with get_db_cursor(commit=True) as cursor:
                
                # Fetch the current card state and the owning user's desired retention
                cursor.execute(
                    """
                    SELECT c.learning_state, c.step, c.difficulty, c.stability,
                           c.due_date, c.last_review, c.first_reviewed, 
                           u.desired_retention, u.fsrs_parameters, u.new_cards_per_day
                    FROM Cards c
                    JOIN Decks d ON c.d_id = d.d_id
                    JOIN Users u ON d.u_id = u.u_id
                    WHERE c.c_id = %s
                    """,
                    (card_id,),
                )
                user_card_info = cursor.fetchone()
                if user_card_info is None:
                    raise CardNotFoundError(f"Card with id {card_id} does not exist.")
                
                # check to see if this was a card that was counted towards the user's total_cards_due
                # first check how many cards have been introduced today for the cards deck
                cursor.execute(
                    """
                    SELECT COUNT(*) AS introduced_today
                    FROM Cards c
                    WHERE c.d_id = (
                        SELECT d_id
                        FROM Cards
                        WHERE c_id = %s
                    )
                    AND DATE(c.first_reviewed) = CURRENT_DATE;
                    """,
                    (card_id,),
                )
                introduced_today = cursor.fetchone()["introduced_today"]

                # now that we have the number of cards introduced today for this card's deck, we can determine if this card was counted in total_cards_due by checking if either:
                # - it is a new card that has never been reviewed before (first_reviewed is null) and the number of cards introduced today is less than the user's new_cards_per_day
                # - it is a card that was due for review (due_date <= now()) and has been reviewed before (first_reviewed is not null)
                # if either of those conditions is true, it means this card was counted in total_cards_due, and since the user just reviewed it, we need to decrement total_cards_due by 1.
                if (user_card_info["first_reviewed"] is None and introduced_today < user_card_info["new_cards_per_day"]) or (user_card_info["due_date"] is not None and user_card_info["due_date"] <= datetime.now(timezone.utc) and user_card_info["first_reviewed"] is not None):
                    cursor.execute(
                        """
                        UPDATE Users
                        SET total_cards_due = GREATEST(total_cards_due - 1, 0)
                        WHERE u_id = (
                            SELECT u_id
                            FROM Decks
                            WHERE d_id = (
                                SELECT d_id
                                FROM Cards
                                WHERE c_id = %s
                            )
                        )
                        """,
                        (card_id,),
                    )

                # Build a Card object from the stored state
                # Unreviewed cards may have NULL learning_state/due_date in the DB
                card = Card(
                    card_id=str(card_id),
                    learning_state=LearningState(user_card_info["learning_state"]) if user_card_info["learning_state"] is not None else LearningState.Learning,
                    step=user_card_info["step"],
                    difficulty=user_card_info["difficulty"],
                    stability=user_card_info["stability"],
                    due=user_card_info["due_date"] if user_card_info["due_date"] is not None else datetime.now(timezone.utc),
                    last_review=user_card_info["last_review"],
                )

                # Create the scheduler with the user's desired retention and optimized parameters (if available)
                desired_retention = user_card_info["desired_retention"] if user_card_info["desired_retention"] is not None else 0.9
                stored_params = user_card_info["fsrs_parameters"]
                scheduler = Scheduler(
                    desired_retention=desired_retention,
                    **(dict(parameters=tuple(stored_params)) if stored_params is not None else {}),
                )

                # Apply the review to compute the new card state
                updated_card, _ = scheduler.review_card(card, Grade(grade), review_datetime=review_datetime)

                # store the fields that are updated by the scheduler back to the database
                updated_fields = {
                    "card_id": card_id,
                    "learning_state": int(updated_card.learning_state),
                    "step": updated_card.step,
                    "difficulty": float(updated_card.difficulty),
                    "stability": float(updated_card.stability),
                    "due_date": updated_card.due,
                    "last_review": updated_card.last_review,
                }

                # Persist the updated FSRS fields back to the database
                cursor.execute(
                    """
                    UPDATE Cards
                    SET learning_state = %s,
                        step           = %s,
                        difficulty     = %s,
                        stability      = %s,
                        due_date       = %s,
                        last_review    = %s,
                        first_reviewed = COALESCE(first_reviewed, NOW())
                    WHERE c_id = %s
                    """,
                    (
                        updated_fields["learning_state"],
                        updated_fields["step"],
                        updated_fields["difficulty"],
                        updated_fields["stability"],
                        updated_fields["due_date"],
                        updated_fields["last_review"],
                        updated_fields["card_id"],
                    ),
                )
                return updated_fields

        except psycopg2.Error as e:
            raise DatabaseError(str(e))

    @staticmethod
    def reschedule_all_cards(user_id: str):
        """
        Reschedules all cards for the user based on their current parameters.
        This should be called after optimization to immediately apply the new parameters to all cards.

        Args:
            user_id: The ID of the user whose cards to reschedule.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                # Fetch all cards for the user's decks
                cursor.execute(
                    """
                    SELECT c.c_id, c.due_date
                    FROM Cards c
                    JOIN Decks d ON c.d_id = d.d_id
                    WHERE d.u_id = %s
                    """,
                    (user_id,),
                )
                # store c_ids and c_due in a list to avoid keeping the DB cursor open
                card_info = [(row["c_id"], row["due_date"]) for row in cursor.fetchall()]

            # get the users current optimized parameters and desired_retention
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT desired_retention, fsrs_parameters
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
                desired_retention = result["desired_retention"] if result["desired_retention"] is not None else 0.9
                stored_params = result["fsrs_parameters"]

            scheduler = Scheduler(
                desired_retention=desired_retention,
                parameters=stored_params
            )

            # For each card, call reschedule_card with all review logs to recalculate state based on the new parameters.
            updated_cards = []
            for card_id, due_date in card_info:
                review_logs = FsrsService.get_card_review_logs(card_id)
                card = Card(
                    card_id=str(card_id),
                    due=due_date if due_date is not None else datetime.now(timezone.utc)
                )
                card = scheduler.reschedule_card(card, review_logs)
                updated_cards.append((card, card_id))

            # Persist all updated cards in a single transaction
            with get_db_cursor(commit=True) as cursor:
                cursor.executemany(
                    """
                    UPDATE Cards
                    SET learning_state = %s,
                        step           = %s,
                        stability      = %s,
                        difficulty     = %s,
                        due_date       = %s,
                        last_review    = %s
                    WHERE c_id = %s
                    """,
                    [
                        (card.learning_state, card.step, card.stability, card.difficulty, card.due, card.last_review, card_id)
                        for card, card_id in updated_cards
                    ],
                )

        except psycopg2.Error as e:
            raise DatabaseError(str(e))

    @staticmethod
    def optimize_parameters(user_id: str) -> list[float]:
        """
        Fetch all review logs for a user, run the FSRS optimizer, and persist
        the resulting parameters back to the user's record.

        Args:
            user_id: The ID of the user whose parameters to optimize.

        Returns:
            The newly optimized list of FSRS parameters.
        """
        review_logs = FsrsService.get_user_review_logs(user_id)
        optimizer = Optimizer(review_logs=review_logs)
        optimized_params = optimizer.compute_optimal_parameters()

        return optimized_params
    
    @staticmethod
    def save_parameters(user_id: str, params: list[float]):
        """
        Saves the current optimized parameters to the user's record.
        This is a method that is called after optimization to persist the new parameters.

        Args:
            user_id: The ID of the user whose parameters to save.
            params: The list of optimized parameters to save.
        
        Raises:
            DatabaseError: On any database error during the save operation.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Users
                    SET fsrs_parameters = %s
                    WHERE u_id = %s
                    """,
                    (params, user_id),
                )
        except psycopg2.Error as e:
            raise DatabaseError(str(e))
        
    @staticmethod
    def increment_review_counts(user_id: str, total_cards_reviewed: int):
        """
        Increment the user's total_reviews and reviews_since_last_optimize counts.

        Args:
            user_id: The ID of the user whose counts to increment.
            total_cards_reviewed: The number of cards reviewed in the current session.
        """
        
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Users
                    SET total_reviews = total_reviews + %s,
                        reviews_since_last_optimize = reviews_since_last_optimize + %s
                    WHERE u_id = %s
                    """,
                    (total_cards_reviewed, total_cards_reviewed, user_id),
                )
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

    @staticmethod
    def should_optimize(user_id: str) -> bool:
        """
        Check if the user has automatic optimization enabled.

        Args:
            user_id: The ID of the user to check.
        Returns:
            True if the user has auto_optimize enabled, False otherwise.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    SELECT auto_optimize
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return result["auto_optimize"] if result and "auto_optimize" in result else False

    @staticmethod
    def cards_reviewed_since_last_optimize(user_id: str) -> int:
        """
        Get the number of cards the user has reviewed since their last optimization.

        Args:
            user_id: The ID of the user to check.
        Returns:
            The number of cards reviewed since last optimization.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    SELECT reviews_since_last_optimize
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return result["reviews_since_last_optimize"]
    
    @staticmethod
    def total_cards_reviewed(user_id: str) -> int:
        """
        Get the total number of cards the user has reviewed.

        Args:
            user_id: The ID of the user to check.
        Returns:
            The total number of cards reviewed.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    SELECT total_reviews
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return result["total_reviews"]
    
    @staticmethod
    def num_reviews_per_optimize(user_id: str) -> int:
        """
        Get the number of reviews after which the user's parameters should be optimized.

        Args:
            user_id: The ID of the user to check.
        Returns:
            The number of reviews per optimization for this user.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    SELECT num_reviews_per_optimize
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return result["num_reviews_per_optimize"]
    
    @staticmethod   
    def reset_review_counts(user_id: str):
        """
        Reset the user's review counts after optimization.

        Args:
            user_id: The ID of the user whose counts to reset.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Users
                    SET reviews_since_last_optimize = 0
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
        except psycopg2.Error as e:
            raise DatabaseError(str(e))
    
    @staticmethod
    def reset_optimization_params(user_id: str):
        """
        Resets the user's optimization counters after parameters have been optimized.
        This should be called internally by the service after optimization is performed.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Users
                    SET fsrs_parameters = NULL
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
        except psycopg2.Error as e:            
            raise DatabaseError(str(e))
    
    @staticmethod
    def get_due_cards(user_id: str) -> tuple[int, list[dict]]:
        """
        Retrieve all cards currently due for review for the specified user.

        Args:
            user_id: The ID of the user whose due cards to retrieve.
        Returns:
            A tuple containing:
                1. the total number of cards currently due for review
                2. a list of dictionaries, each containing the card_id, due_date, and deck_id of a card that is currently due for review.
        """
        try:
            # get the new_cards_per_day setting for the user to determine how many new cards to include in the due cards list
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT new_cards_per_day
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
                new_cards_per_day = result["new_cards_per_day"]

            # fetch new_cards_per_day amount of new cards per deck + all due cards that have been reviewed before
            # a card is considered new if last_review is null, since last_review only gets a value after the first time the card is reviewed.
            # to get new_cards_per_day per deck, we assign a row number to each card partitioned by deck and ordered by card id, then we select only the rows where the row number is less than or equal to new_cards_per_day -(number of cards introduced tdy)
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    -- check how many cards have been introduced today for each deck
                    WITH introduced_today AS ( 
                        SELECT c.d_id, COUNT(*) AS cnt
                        FROM Cards c
                        JOIN Decks d ON c.d_id = d.d_id
                        WHERE d.u_id = %s
                        AND DATE(c.first_reviewed) = CURRENT_DATE
                        GROUP BY c.d_id
                    ),
                    -- all the new cards that haven't been reviewed, rn will order them so we can select only (new_cards_per_day -  number of new cards intrduced today) per deck
                    new_cards AS ( 
                        SELECT c.c_id, c.due_date, c.d_id,
                            ROW_NUMBER() OVER (PARTITION BY c.d_id ORDER BY c.c_id) AS rn,
                            COALESCE(it.cnt, 0) AS introduced_today -- a deck with no cards introduced today will have 0 instead of null
                        FROM Cards c
                        JOIN Decks d ON c.d_id = d.d_id
                        LEFT JOIN introduced_today it ON c.d_id = it.d_id
                        WHERE d.u_id = %s
                        AND c.first_reviewed IS NULL
                    ),
                    -- all the cards that have been reviewed before and are currently due
                    review_cards AS (
                        SELECT c.c_id, c.due_date, c.d_id
                        FROM Cards c
                        JOIN Decks d ON c.d_id = d.d_id
                        WHERE d.u_id = %s
                        AND c.due_date <= NOW()
                        AND c.first_reviewed IS NOT NULL
                    )
                    SELECT c_id, due_date, d_id FROM new_cards
                    -- if the user has already been introduced to some new cards today, we reduce the number of new cards we show them by the number they've already been introduced to, but we never show them less than 0 new cards
                    WHERE rn <= GREATEST(%s - introduced_today, 0) 
                    UNION ALL
                    SELECT c_id, due_date, d_id FROM review_cards
                    """,
                    (user_id, user_id, user_id, new_cards_per_day),
                )
                results = cursor.fetchall()
            
            num_due_cards = len(results)

            # update the user's total_cards_due field in the Users table to reflect the number of cards that are currently due for review
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE Users
                    SET total_cards_due = %s
                    WHERE u_id = %s
                    """,
                    (num_due_cards, user_id),
                )
            
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return (num_due_cards, [{"card_id": row["c_id"], "due_date": row["due_date"], "deck_id": row["d_id"]} for row in results])
    
    @staticmethod
    def get_num_due_cards(user_id: str) -> int:
        """
        Get the total number of cards currently due for review for the specified user.

        Args:
            user_id: The ID of the user whose due card count to retrieve.
        Returns:
            The total number of cards currently due for review.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT total_cards_due
                    FROM Users
                    WHERE u_id = %s
                    """,
                    (user_id,),
                )
                result = cursor.fetchone()
                total_cards_due = result["total_cards_due"] if result and "total_cards_due" in result else 0
        except psycopg2.Error as e:
            raise DatabaseError(str(e))

        return total_cards_due