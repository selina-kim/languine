from services.fsrs.scheduler import Scheduler, STABILITY_MIN, DEFAULT_PARAMETERS, DIFFICULTY_MAX, DIFFICULTY_MIN
from services.fsrs.card import Card
from services.fsrs.learning_state import LearningState
from services.fsrs.review_log import ReviewLog
from services.fsrs.grade import Grade

from datetime import datetime, timedelta, timezone
import json
import pytest
import random
from copy import deepcopy
import sys
import re
import time

TEST_RATINGS_1 = (
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Again,
    Grade.Again,
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Good,
    Grade.Good,
)


class TestPyFSRS:
    def test_review_card(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)

        ivl_history = []
        for grade in TEST_RATINGS_1:
            card, _ = scheduler.review_card(card=card, grade=grade, review_datetime=review_datetime)

            ivl = (card.due - card.last_review).days
            ivl_history.append(ivl)

            review_datetime = card.due

        assert ivl_history == [0, 2, 11, 46, 163, 498, 0, 0, 2, 4, 7, 12, 21]

    def test_repeated_correct_reviews(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()
        review_datetimes = [
            datetime(2022, 11, 29, 12, 30, 0, i, timezone.utc) for i in range(10)
        ]

        for review_datetime in review_datetimes:
            card, _ = scheduler.review_card(
                card=card, grade=Grade.Easy, review_datetime=review_datetime
            )

        assert card.difficulty == 1.0

    def test_memo_state(self):
        scheduler = Scheduler()

        ratings = (
            Grade.Again,
            Grade.Good,
            Grade.Good,
            Grade.Good,
            Grade.Good,
            Grade.Good,
        )
        ivl_history = [0, 0, 1, 3, 8, 21]

        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)

        for grade, ivl in zip(ratings, ivl_history):
            review_datetime += timedelta(days=ivl)
            card, _ = scheduler.review_card(
                card=card, grade=grade, review_datetime=review_datetime
            )

        assert card.stability == pytest.approx(53.62691, abs=1e-4)
        assert card.difficulty == pytest.approx(6.3574867, abs=1e-4)

    def test_repeat_default_arg(self):
        scheduler = Scheduler()

        card = Card()

        grade = Grade.Good

        card, _ = scheduler.review_card(
            card=card,
            grade=grade,
        )

        due = card.due

        time_delta = due - datetime.now(timezone.utc)

        assert time_delta.seconds > 500  # due in approx. 8-10 minutes

    def test_datetime(self):
        scheduler = Scheduler()
        card = Card()

        # new cards should be due immediately after creation
        assert datetime.now(timezone.utc) >= card.due

        # comparing timezone aware cards with deprecated datetime.utcnow() should raise a TypeError
        with pytest.raises(TypeError):
            datetime.now() >= card.due

        # repeating a card with a non-utc, non-timezone-aware datetime object should raise a Value Error
        with pytest.raises(ValueError):
            scheduler.review_card(
                card=card,
                grade=Grade.Good,
                review_datetime=datetime(2022, 11, 29, 12, 30, 0, 0),
            )

        # review a card with grade good before next tests
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )

        # card object's due and last_review attributes must be timezone aware and UTC
        assert card.due.tzinfo == timezone.utc
        assert card.last_review.tzinfo == timezone.utc
        # card object's due datetime should be later than its last review
        assert card.due >= card.last_review

    def test_Card_dict_serialize(self):
        scheduler = Scheduler()

        # create card object the normal way
        card = Card()

        # we can reconstruct a copy of the card object equivalent to the original
        card_dict = card.model_dump()
        copied_card = Card.model_validate(card_dict)

        assert vars(card) == vars(copied_card)
        assert card.model_dump() == copied_card.model_dump()

        # (x2) perform the above tests once more with a repeated card
        reviewed_card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )

        reviewed_card_dict = reviewed_card.model_dump()
        copied_reviewed_card = Card.model_validate(reviewed_card_dict)

        assert vars(reviewed_card) == vars(copied_reviewed_card)
        assert reviewed_card.model_dump() == copied_reviewed_card.model_dump()

        # original card and repeated card are different
        assert vars(card) != vars(reviewed_card)
        assert card.model_dump() != reviewed_card.model_dump()

    def test_Card_json_serialize(self):
        scheduler = Scheduler()

        # create card object the normal way
        card = Card()

        # we can reconstruct a copy of the card object equivalent to the original
        card_json = card.model_dump_json(indent=2)
        copied_card = Card.model_validate_json(card_json)

        assert card == copied_card
        assert card.model_dump_json(indent=2) == copied_card.model_dump_json(indent=2)

        # (x2) perform the above tests once more with a repeated card
        reviewed_card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )

        reviewed_card_json = reviewed_card.model_dump_json(indent=2)
        copied_reviewed_card = Card.model_validate_json(reviewed_card_json)

        assert reviewed_card == copied_reviewed_card
        assert reviewed_card.model_dump_json(indent=2) == copied_reviewed_card.model_dump_json(indent=2)

        # original card and repeated card are different
        assert card != reviewed_card
        assert card.model_dump_json(indent=2) != reviewed_card.model_dump_json(indent=2)

    def test_ReviewLog_dict_serialize(self):
        scheduler = Scheduler()

        card = Card()

        # review a card to get the review_log
        card, review_log = scheduler.review_card(card=card, grade=Grade.Again)

        # we can reconstruct a copy of the review_log object equivalent to the original
        review_log_dict = review_log.model_dump()
        copied_review_log = ReviewLog.model_validate(review_log_dict)
        assert review_log.model_dump() == copied_review_log.model_dump()

        # (x2) perform the above tests once more with a review_log from a reviewed card
        grade = Grade.Good
        card, next_review_log = scheduler.review_card(
            card=card, grade=grade, review_datetime=datetime.now(timezone.utc)
        )

        next_review_log_dict = next_review_log.model_dump()
        copied_next_review_log = ReviewLog.model_validate(next_review_log_dict)

        assert next_review_log.model_dump() == copied_next_review_log.model_dump()

        # original review log and next review log are different
        assert review_log.model_dump() != next_review_log.model_dump()

    def test_ReviewLog_json_serialize(self):
        scheduler = Scheduler()

        card = Card()

        card, review_log = scheduler.review_card(card=card, grade=Grade.Again)

        # we can reconstruct a copy of the ReviewLog object equivalent to the original
        review_log_json = review_log.model_dump_json(indent=2)
        copied_review_log = ReviewLog.model_validate_json(review_log_json)

        assert review_log == copied_review_log
        assert review_log.model_dump_json(indent=2) == copied_review_log.model_dump_json(indent=2)

        # (x2) perform the above tests one more with a review_log from a reviewed card
        grade = Grade.Good
        _, next_review_log = scheduler.review_card(
            card=card, grade=grade, review_datetime=datetime.now(timezone.utc)
        )

        next_review_log_json = next_review_log.model_dump_json(indent=2)
        copied_next_review_log = ReviewLog.model_validate_json(next_review_log_json)

        assert next_review_log == copied_next_review_log
        assert next_review_log.model_dump_json(indent=2) == copied_next_review_log.model_dump_json(indent=2)

        # original review log and next review lot are different
        assert review_log != next_review_log
        assert review_log.model_dump_json(indent=2) != next_review_log.model_dump_json(indent=2)

    def test_Scheduler_dict_serialize(self):
        scheduler = Scheduler()

        # scheduler can be serialized and de-serialized while remaining the same
        scheduler_dict = scheduler.model_dump()
        copied_scheduler = Scheduler.model_validate(scheduler_dict)
        assert vars(scheduler) == vars(copied_scheduler)
        assert scheduler.model_dump() == copied_scheduler.model_dump()

    def test_Scheduler_json_serialize(self):
        scheduler = Scheduler()

        # Scheduler objects are json-serializable through its .model_dump_json(indent=2) method
        assert type(json.dumps(scheduler.model_dump_json(indent=2))) is str

        # scheduler can be serialized and de-serialized while remaining the same
        scheduler_json = scheduler.model_dump_json(indent=2)
        copied_scheduler = Scheduler.model_validate_json(scheduler_json)
        assert scheduler == copied_scheduler
        assert scheduler.model_dump_json(indent=2) == copied_scheduler.model_dump_json(indent=2)

    def test_custom_scheduler_args(self):
        scheduler = Scheduler(
            desired_retention=0.9,
            maximum_interval=36500,
            enable_fuzzing=False,
        )
        card = Card()
        now = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)

        ivl_history = []

        for grade in TEST_RATINGS_1:
            card, _ = scheduler.review_card(card, grade, now)
            ivl = (card.due - card.last_review).days
            ivl_history.append(ivl)
            now = card.due

        assert ivl_history == [0, 2, 11, 46, 163, 498, 0, 0, 2, 4, 7, 12, 21]

        # initialize another scheduler and verify parameters are properly set
        parameters2 = (
            0.1456,
            0.4186,
            1.1104,
            4.1315,
            5.2417,
            1.3098,
            0.8975,
            0.0010,
            1.5674,
            0.0567,
            0.9661,
            2.0275,
            0.1592,
            0.2446,
            1.5071,
            0.2272,
            2.8755,
            1.234,
            0.56789,
            0.1437,
            0.2,
        )
        desired_retention2 = 0.85
        maximum_interval2 = 3650
        scheduler2 = Scheduler(
            parameters=parameters2,
            desired_retention=desired_retention2,
            maximum_interval=maximum_interval2,
        )

        assert scheduler2.parameters == parameters2
        assert scheduler2.desired_retention == desired_retention2
        assert scheduler2.maximum_interval == maximum_interval2

    def test_retrievability(self):
        scheduler = Scheduler()

        card = Card()

        # retrievabiliy of New card
        assert card.learning_state == LearningState.Learning
        retrievability = scheduler.get_card_retrievability(card=card)
        assert retrievability == 0

        # retrievabiliy of Learning card
        card, _ = scheduler.review_card(card, Grade.Good)
        assert card.learning_state == LearningState.Learning
        retrievability = scheduler.get_card_retrievability(card=card)
        assert 0 <= retrievability <= 1

        # retrievabiliy of Review card
        card, _ = scheduler.review_card(card, Grade.Good)
        assert card.learning_state == LearningState.Review
        retrievability = scheduler.get_card_retrievability(card=card)
        assert 0 <= retrievability <= 1

        # retrievabiliy of Relearning card
        card, _ = scheduler.review_card(card, Grade.Again)
        assert card.learning_state == LearningState.Relearning
        retrievability = scheduler.get_card_retrievability(card=card)
        assert 0 <= retrievability <= 1

    def test_good_learning_steps(self):
        scheduler = Scheduler()

        created_at = datetime.now(timezone.utc)
        card = Card()

        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Learning
        assert card.step == 1
        assert (
            round((card.due - created_at).total_seconds() / 100) == 6
        )  # card is due in approx. 10 minutes (600 seconds)

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review
        assert card.step is None
        assert (
            round((card.due - created_at).total_seconds() / 3600) >= 24
        )  # card is due in over a day

    def test_again_learning_steps(self):
        scheduler = Scheduler()

        created_at = datetime.now(timezone.utc)
        card = Card()

        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        grade = Grade.Again
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Learning
        assert card.step == 0
        assert (
            round((card.due - created_at).total_seconds() / 10) == 6
        )  # card is due in approx. 1 minute (60 seconds)

    def test_hard_learning_steps(self):
        scheduler = Scheduler()

        created_at = datetime.now(timezone.utc)
        card = Card()

        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        grade = Grade.Hard
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Learning
        assert card.step == 0
        assert (
            round((card.due - created_at).total_seconds() / 10) == 33
        )  # card is due in approx. 5.5 minutes (330 seconds)

    def test_easy_learning_steps(self):
        scheduler = Scheduler()

        created_at = datetime.now(timezone.utc)
        card = Card()

        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        grade = Grade.Easy
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review
        assert card.step is None
        assert (
            round((card.due - created_at).total_seconds() / 86400) >= 1
        )  # card is due in at least 1 full day

    def test_review_state(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review
        assert card.step is None

        prev_due = card.due
        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review
        assert (
            round((card.due - prev_due).total_seconds() / 3600) >= 24
        )  # card is due in at least 1 full day

        # rate the card again
        prev_due = card.due
        grade = Grade.Again
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert (
            round((card.due - prev_due).total_seconds() / 60) == 10
        )  # card is due in 10 minutes

    def test_relearning(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        prev_due = card.due
        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        # rate the card again
        prev_due = card.due
        grade = Grade.Again
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0
        assert (
            round((card.due - prev_due).total_seconds() / 60) == 10
        )  # card is due in 10 minutes

        prev_due = card.due
        grade = Grade.Again
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0
        assert (
            round((card.due - prev_due).total_seconds() / 60) == 10
        )  # card is due in 10 minutes

        prev_due = card.due
        grade = Grade.Good
        card, _ = scheduler.review_card(
            card=card, grade=grade, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review
        assert card.step is None
        assert (
            round((card.due - prev_due).total_seconds() / 3600) >= 24
        )  # card is due in at least 1 full day

    def test_fuzz(self):
        scheduler = Scheduler()

        # seed 1
        random.seed(42)

        card = Card()
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        prev_due = card.due
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        interval = card.due - prev_due

        assert interval.days == 12

        # seed 2
        random.seed(12345)

        card = Card()
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        prev_due = card.due
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        interval = card.due - prev_due

        assert interval.days == 11

    def test_no_learning_steps(self):
        scheduler = Scheduler(learning_steps=())

        assert len(scheduler.learning_steps) == 0

        card = Card()
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Again, review_datetime=datetime.now(timezone.utc)
        )

        assert card.learning_state == LearningState.Review
        interval = (card.due - card.last_review).days
        assert interval >= 1

    def test_no_relearning_steps(self):
        scheduler = Scheduler(relearning_steps=())

        assert len(scheduler.relearning_steps) == 0

        card = Card()
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Learning
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Again, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review

        interval = (card.due - card.last_review).days
        assert interval >= 1

    def test_one_card_multiple_schedulers(self):
        scheduler_with_two_learning_steps = Scheduler(
            learning_steps=(timedelta(minutes=1), timedelta(minutes=10))
        )
        scheduler_with_one_learning_step = Scheduler(
            learning_steps=(timedelta(minutes=1),)
        )
        scheduler_with_no_learning_steps = Scheduler(learning_steps=())

        scheduler_with_two_relearning_steps = Scheduler(
            relearning_steps=(
                timedelta(minutes=1),
                timedelta(minutes=10),
            )
        )
        scheduler_with_one_relearning_step = Scheduler(
            relearning_steps=(timedelta(minutes=1),)
        )
        scheduler_with_no_relearning_steps = Scheduler(relearning_steps=())

        card = Card()

        # learning-learning_state tests
        assert len(scheduler_with_two_learning_steps.learning_steps) == 2
        card, _ = scheduler_with_two_learning_steps.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Learning
        assert card.step == 1

        assert len(scheduler_with_one_learning_step.learning_steps) == 1
        card, _ = scheduler_with_one_learning_step.review_card(
            card=card, grade=Grade.Again, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        assert len(scheduler_with_no_learning_steps.learning_steps) == 0
        card, _ = scheduler_with_no_learning_steps.review_card(
            card=card, grade=Grade.Hard, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Review
        assert card.step is None

        # relearning-learning_state tests
        assert len(scheduler_with_two_relearning_steps.relearning_steps) == 2
        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Again, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Good, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Relearning
        assert card.step == 1

        assert len(scheduler_with_one_relearning_step.relearning_steps) == 1
        card, _ = scheduler_with_one_relearning_step.review_card(
            card=card, grade=Grade.Again, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        assert len(scheduler_with_no_relearning_steps.relearning_steps) == 0
        card, _ = scheduler_with_no_relearning_steps.review_card(
            card=card, grade=Grade.Hard, review_datetime=datetime.now(timezone.utc)
        )
        assert card.learning_state == LearningState.Review
        assert card.step is None

    def test_maximum_interval(self):
        maximum_interval = 100
        scheduler = Scheduler(maximum_interval=maximum_interval)

        card = Card()

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Easy, review_datetime=card.due
        )
        assert (card.due - card.last_review).days <= scheduler.maximum_interval

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert (card.due - card.last_review).days <= scheduler.maximum_interval

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Easy, review_datetime=card.due
        )
        assert (card.due - card.last_review).days <= scheduler.maximum_interval

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert (card.due - card.last_review).days <= scheduler.maximum_interval

    def test_class_repr(self):
        card = Card()

        assert str(card) == repr(card)

        scheduler = Scheduler()

        assert str(scheduler) == repr(scheduler)

        card, review_log = scheduler.review_card(card=card, grade=Grade.Good)

        assert str(review_log) == repr(review_log)

    def test_unique_card_ids(self):
        card_ids = []
        for i in range(1000):
            card = Card()
            card_id = card.card_id
            card_ids.append(card_id)

        assert len(card_ids) == len(set(card_ids))

    def test_stability_lower_bound(self):
        """
        Ensure that a Card object's stability is always >= STABILITY_MIN
        """

        scheduler = Scheduler()

        card = Card()

        for _ in range(1000):
            card, _ = scheduler.review_card(
                card=card,
                grade=Grade.Again,
                review_datetime=card.due + timedelta(days=1),
            )
            assert card.stability >= STABILITY_MIN

    def test_scheduler_parameter_validation(self):
        # initializing a Scheduler object with valid parameters works
        good_parameters = DEFAULT_PARAMETERS
        assert type(Scheduler(parameters=good_parameters)) is Scheduler

        parameters_one_too_high = list(DEFAULT_PARAMETERS)
        parameters_one_too_high[6] = 100
        with pytest.raises(ValueError):
            Scheduler(parameters=parameters_one_too_high)

        parameters_one_too_low = list(DEFAULT_PARAMETERS)
        parameters_one_too_low[10] = -42
        with pytest.raises(ValueError):
            Scheduler(parameters=parameters_one_too_low)

        parameters_two_bad = list(DEFAULT_PARAMETERS)
        parameters_two_bad[0] = 0
        parameters_two_bad[3] = 101
        with pytest.raises(ValueError):
            Scheduler(parameters=parameters_two_bad)

        zero_parameters = []
        with pytest.raises(ValueError):
            Scheduler(parameters=zero_parameters)

        one_too_few_parameters = DEFAULT_PARAMETERS[:-1]
        with pytest.raises(ValueError):
            Scheduler(parameters=one_too_few_parameters)

        too_many_parameters = DEFAULT_PARAMETERS + (1, 2, 3)
        with pytest.raises(ValueError):
            Scheduler(parameters=too_many_parameters)

    def test_class___eq___methods(self):
        scheduler1 = Scheduler()
        scheduler2 = Scheduler(desired_retention=0.91)
        scheduler1_copy = deepcopy(scheduler1)

        assert scheduler1 != scheduler2
        assert scheduler1 == scheduler1_copy

        card_orig = Card()
        card_orig_copy = deepcopy(card_orig)

        assert card_orig == card_orig_copy

        card_review_1, review_log_review_1 = scheduler1.review_card(
            card=card_orig, grade=Grade.Good
        )

        review_log_review_1_copy = deepcopy(review_log_review_1)

        assert card_orig != card_review_1
        assert review_log_review_1 == review_log_review_1_copy

        _, review_log_review_2 = scheduler1.review_card(
            card=card_review_1, grade=Grade.Good
        )

        assert review_log_review_1 != review_log_review_2

    def test_learning_card_rate_hard_one_learning_step(self):
        first_learning_step = timedelta(minutes=10)

        scheduler_with_one_learning_step = Scheduler(
            learning_steps=(first_learning_step,)
        )

        card = Card()

        initial_due_datetime = card.due

        card, _ = scheduler_with_one_learning_step.review_card(
            card=card, grade=Grade.Hard, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Learning

        new_due_datetime = card.due

        interval_length = new_due_datetime - initial_due_datetime

        expected_interval_length = first_learning_step * 1.5

        tolerance = timedelta(seconds=1)

        assert abs(interval_length - expected_interval_length) <= tolerance

    def test_learning_card_rate_hard_second_learning_step(self):
        first_learning_step = timedelta(minutes=1)
        second_learning_step = timedelta(minutes=10)

        scheduler_with_two_learning_steps = Scheduler(
            learning_steps=(first_learning_step, second_learning_step)
        )

        card = Card()

        assert card.learning_state == LearningState.Learning
        assert card.step == 0

        card, _ = scheduler_with_two_learning_steps.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Learning
        assert card.step == 1

        due_datetime_after_first_review = card.due

        card, _ = scheduler_with_two_learning_steps.review_card(
            card=card,
            grade=Grade.Hard,
            review_datetime=due_datetime_after_first_review,
        )

        due_datetime_after_second_review = card.due

        assert card.learning_state == LearningState.Learning
        assert card.step == 1

        interval_length = (
            due_datetime_after_second_review - due_datetime_after_first_review
        )

        expected_interval_length = second_learning_step

        tolerance = timedelta(seconds=1)

        assert abs(interval_length - expected_interval_length) <= tolerance

    def test_long_term_stability_learning_state(self):
        # NOTE: currently, this test is mostly to make sure that
        # the unit tests cover the case when a card in the relearning learning_state
        # is not reviewed on the same day to run the non-same-day stability calculations

        scheduler = Scheduler()

        card = Card()

        assert card.learning_state == LearningState.Learning

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Easy, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review

        card, _ = scheduler.review_card(
            card=card, grade=Grade.Again, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning

        relearning_card_due_datetime = card.due

        # a full day after its next due date
        next_review_datetime_one_day_late = relearning_card_due_datetime + timedelta(
            days=1
        )

        card, _ = scheduler.review_card(
            card=card,
            grade=Grade.Good,
            review_datetime=next_review_datetime_one_day_late,
        )

        assert card.learning_state == LearningState.Review

    def test_relearning_card_rate_hard_one_relearning_step(self):
        first_relearning_step = timedelta(minutes=10)

        scheduler_with_one_relearning_step = Scheduler(
            relearning_steps=(first_relearning_step,)
        )

        card = Card()

        card, _ = scheduler_with_one_relearning_step.review_card(
            card=card, grade=Grade.Easy, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review

        card, _ = scheduler_with_one_relearning_step.review_card(
            card=card, grade=Grade.Again, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        prev_due_datetime = card.due

        card, _ = scheduler_with_one_relearning_step.review_card(
            card=card, grade=Grade.Hard, review_datetime=prev_due_datetime
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        new_due_datetime = card.due

        interval_length = new_due_datetime - prev_due_datetime

        expected_interval_length = first_relearning_step * 1.5

        tolerance = timedelta(seconds=1)

        assert abs(interval_length - expected_interval_length) <= tolerance

    def test_relearning_card_rate_hard_two_relearning_steps(self):
        first_relearning_step = timedelta(minutes=1)
        second_relearning_step = timedelta(minutes=10)

        scheduler_with_two_relearning_steps = Scheduler(
            relearning_steps=(first_relearning_step, second_relearning_step)
        )

        card = Card()

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Easy, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Review

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Again, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        prev_due_datetime = card.due

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Hard, review_datetime=prev_due_datetime
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 0

        new_due_datetime = card.due

        interval_length = new_due_datetime - prev_due_datetime

        expected_interval_length = (
            first_relearning_step + second_relearning_step
        ) / 2.0

        tolerance = timedelta(seconds=1)

        assert abs(interval_length - expected_interval_length) <= tolerance

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )

        assert card.learning_state == LearningState.Relearning
        assert card.step == 1

        prev_due_datetime = card.due

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Hard, review_datetime=prev_due_datetime
        )

        new_due_datetime = card.due

        assert card.learning_state == LearningState.Relearning
        assert card.step == 1

        interval_length = new_due_datetime - prev_due_datetime

        expected_interval_length = second_relearning_step

        tolerance = timedelta(seconds=1)

        assert abs(interval_length - expected_interval_length) <= tolerance

        card, _ = scheduler_with_two_relearning_steps.review_card(
            card=card, grade=Grade.Easy, review_datetime=prev_due_datetime
        )

        assert card.learning_state == LearningState.Review
        assert card.step is None

    def test_reschedule_card_same_scheduler(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        review_logs = []

        start = time.time()
        for grade in TEST_RATINGS_1:
            card, review_log = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )
            review_logs.append(review_log)

        end = time.time()
        print(start-end)

        rescheduled_card = scheduler.reschedule_card(card=card, review_logs=review_logs)

        assert card is not rescheduled_card
        assert card == rescheduled_card

    def test_reschedule_card_different_parameters(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        review_logs = []
        for grade in TEST_RATINGS_1:
            card, review_log = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )
            review_logs.append(review_log)

        DIFFERENT_PARAMETERS = [
            0.12340357383516173,
            1.2931,
            2.397673571899466,
            8.2956,
            6.686820427099132,
            0.45021679958387956,
            3.077875127553957,
            0.053520395733247045,
            1.6539992229052127,
            0.1466206769107436,
            0.6300772488850335,
            1.611965002575047,
            0.012840136810798864,
            0.34853762746216305,
            1.8878958285806287,
            0.8546376191171063,
            1.8729,
            0.6748536823468675,
            0.20451266082721842,
            0.22622814695113844,
            0.46030603398979064,
        ]
        assert scheduler.parameters != DIFFERENT_PARAMETERS
        scheduler_with_different_parameters = Scheduler(parameters=DIFFERENT_PARAMETERS)
        rescheduled_card = scheduler_with_different_parameters.reschedule_card(
            card=card, review_logs=review_logs
        )

        assert card.card_id == rescheduled_card.card_id
        assert card.learning_state == rescheduled_card.learning_state
        assert card.step == rescheduled_card.step
        assert card.stability != rescheduled_card.stability
        assert card.difficulty != rescheduled_card.difficulty
        assert card.last_review == rescheduled_card.last_review
        assert card.due != rescheduled_card.due

    def test_reschedule_card_different_desired_retention(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        review_logs = []
        for grade in TEST_RATINGS_1:
            card, review_log = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )
            review_logs.append(review_log)

        DIFFERENT_DESIRED_RETENTION = 0.8
        assert scheduler.desired_retention != DIFFERENT_DESIRED_RETENTION
        scheduler_with_different_retention = Scheduler(
            desired_retention=DIFFERENT_DESIRED_RETENTION
        )
        rescheduled_card = scheduler_with_different_retention.reschedule_card(
            card=card, review_logs=review_logs
        )

        assert card.card_id == rescheduled_card.card_id
        assert card.learning_state == rescheduled_card.learning_state
        assert card.step == rescheduled_card.step
        assert card.stability == rescheduled_card.stability
        assert card.difficulty == rescheduled_card.difficulty
        assert card.last_review == rescheduled_card.last_review
        assert card.due < rescheduled_card.due

    def test_reschedule_card_different_learning_steps(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        review_logs = []
        for grade in TEST_RATINGS_1:
            card, review_log = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )
            review_logs.append(review_log)

        DIFFERENT_LEARNING_STEPS = [timedelta(minutes=1)] * len(review_logs)
        assert scheduler.learning_steps != DIFFERENT_LEARNING_STEPS
        scheduler_with_different_retention = Scheduler(
            learning_steps=DIFFERENT_LEARNING_STEPS
        )
        rescheduled_card = scheduler_with_different_retention.reschedule_card(
            card=card, review_logs=review_logs
        )

        assert card.card_id == rescheduled_card.card_id
        assert card.learning_state != rescheduled_card.learning_state
        assert card.step != rescheduled_card.step
        assert card.stability == rescheduled_card.stability
        assert card.difficulty == rescheduled_card.difficulty
        assert card.last_review == rescheduled_card.last_review
        assert card.due > rescheduled_card.due

    def test_reschedule_card_wrong_review_logs(self):
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()

        review_logs = []
        for grade in TEST_RATINGS_1:
            card, review_log = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )
            review_logs.append(review_log)

        DIFFERENT_CARD_ID = 123
        assert card.card_id != DIFFERENT_CARD_ID
        review_logs[0].card_id = DIFFERENT_CARD_ID

        EXPECTED_ERROR_MESSAGE = f"ReviewLog card_id {DIFFERENT_CARD_ID} does not match Card card_id {card.card_id}"
        with pytest.raises(ValueError, match=re.escape(EXPECTED_ERROR_MESSAGE)):
            _ = scheduler.reschedule_card(card=card, review_logs=review_logs)

    def test_review_card_does_not_mutate_original(self):
        """
        review_card() should not mutate the original Card object passed to it.
        """
        scheduler = Scheduler(enable_fuzzing=False)
        card = Card()
        original_card = deepcopy(card)

        _, _ = scheduler.review_card(
            card=card,
            grade=Grade.Good,
            review_datetime=datetime.now(timezone.utc),
        )

        assert card == original_card

    def test_card_initial_state(self):
        """
        A freshly constructed Card should have the expected default field values.
        """
        card = Card()

        assert isinstance(card.card_id, str)
        assert card.learning_state == LearningState.Learning
        assert card.step == 0
        assert card.stability is None
        assert card.difficulty is None
        assert card.last_review is None
        assert card.due <= datetime.now(timezone.utc)

    def test_difficulty_bounds(self):
        """
        Card difficulty should always stay within [DIFFICULTY_MIN, DIFFICULTY_MAX]
        after any sequence of reviews.
        """
        scheduler = Scheduler()
        card = Card()

        grades = [Grade.Again, Grade.Hard, Grade.Good, Grade.Easy] * 50
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)

        for grade in grades:
            card, _ = scheduler.review_card(
                card=card, grade=grade, review_datetime=review_datetime
            )
            review_datetime = card.due + timedelta(days=1)
            if card.difficulty is not None:
                assert DIFFICULTY_MIN <= card.difficulty <= DIFFICULTY_MAX

    def test_difficulty_direction(self):
        """
        In Review state, grading Again should increase difficulty
        and grading Easy should decrease it.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        # advance card to Review state
        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=review_datetime
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review

        # grading Easy should decrease difficulty
        card_easy = deepcopy(card)
        difficulty_before = card_easy.difficulty
        card_easy, _ = scheduler.review_card(
            card=card_easy,
            grade=Grade.Easy,
            review_datetime=card_easy.due + timedelta(days=1),
        )
        assert card_easy.difficulty < difficulty_before

        # grading Again should increase difficulty
        card_again = deepcopy(card)
        difficulty_before = card_again.difficulty
        card_again, _ = scheduler.review_card(
            card=card_again,
            grade=Grade.Again,
            review_datetime=card_again.due + timedelta(days=1),
        )
        assert card_again.difficulty > difficulty_before

    def test_stability_increases_after_successful_review(self):
        """
        In Review state, Hard/Good/Easy grades should increase stability;
        Again should decrease it.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        # advance card to Review state
        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=review_datetime
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review

        stability_before = card.stability

        # Hard, Good, and Easy should each increase stability
        for grade in (Grade.Hard, Grade.Good, Grade.Easy):
            card_copy = deepcopy(card)
            card_copy, _ = scheduler.review_card(
                card=card_copy,
                grade=grade,
                review_datetime=card_copy.due + timedelta(days=1),
            )
            assert card_copy.stability > stability_before, (
                f"Expected stability to increase after {grade}, but it didn't"
            )

        # Again should decrease stability
        card_again = deepcopy(card)
        card_again, _ = scheduler.review_card(
            card=card_again,
            grade=Grade.Again,
            review_datetime=card_again.due + timedelta(days=1),
        )
        assert card_again.stability < stability_before

    def test_retrievability_decreases_over_time(self):
        """
        Retrievability should strictly decrease as more time passes since the last review.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=review_datetime
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review

        base_datetime = card.last_review
        r_t0 = scheduler.get_card_retrievability(
            card=card, current_datetime=base_datetime + timedelta(days=1)
        )
        r_t1 = scheduler.get_card_retrievability(
            card=card, current_datetime=base_datetime + timedelta(days=10)
        )
        r_t2 = scheduler.get_card_retrievability(
            card=card, current_datetime=base_datetime + timedelta(days=30)
        )

        assert r_t0 > r_t1 > r_t2

    def test_get_card_retrievability_at_due_date(self):
        """
        At exactly the card's due date (fuzzing disabled), retrievability should
        approximately equal the scheduler's desired_retention.
        """
        desired_retention = 0.9
        scheduler = Scheduler(enable_fuzzing=False, desired_retention=desired_retention)

        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=review_datetime
        )
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=card.due
        )
        assert card.learning_state == LearningState.Review

        retrievability_at_due = scheduler.get_card_retrievability(
            card=card, current_datetime=card.due
        )

        assert retrievability_at_due == pytest.approx(desired_retention, abs=0.05)

    def test_short_term_stability_good_easy_cannot_decrease(self):
        """
        Same-day reviews with Good or Easy grades must not decrease stability.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()
        review_datetime = datetime(2022, 11, 29, 12, 30, 0, 0, timezone.utc)
        card, _ = scheduler.review_card(
            card=card, grade=Grade.Good, review_datetime=review_datetime
        )
        stability_after_first = card.stability

        same_day_datetime = review_datetime + timedelta(minutes=30)

        # same-day Good review should not decrease stability
        card_good = deepcopy(card)
        card_good, _ = scheduler.review_card(
            card=card_good, grade=Grade.Good, review_datetime=same_day_datetime
        )
        assert card_good.stability >= stability_after_first

        # same-day Easy review should not decrease stability
        card_easy = deepcopy(card)
        card_easy, _ = scheduler.review_card(
            card=card_easy, grade=Grade.Easy, review_datetime=same_day_datetime
        )
        assert card_easy.stability >= stability_after_first

    def test_review_card_review_duration_in_log(self):
        """
        review_duration passed to review_card should appear in the returned ReviewLog.
        """
        scheduler = Scheduler()
        card = Card()
        review_datetime = datetime.now(timezone.utc)

        review_duration_ms = 3500
        _, review_log = scheduler.review_card(
            card=card,
            grade=Grade.Good,
            review_datetime=review_datetime,
            review_duration=review_duration_ms,
        )
        assert review_log.review_duration == review_duration_ms

        # None review_duration should also be preserved
        _, review_log_no_duration = scheduler.review_card(
            card=card,
            grade=Grade.Good,
            review_datetime=review_datetime,
            review_duration=None,
        )
        assert review_log_no_duration.review_duration is None

    def test_reschedule_card_empty_review_logs(self):
        """
        reschedule_card with an empty review_logs list should return a card
        with the same card_id but no review history.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        card = Card()
        for grade in TEST_RATINGS_1:
            card, _ = scheduler.review_card(
                card=card, grade=grade, review_datetime=card.due
            )

        rescheduled_card = scheduler.reschedule_card(card=card, review_logs=[])

        assert rescheduled_card.card_id == card.card_id
        assert rescheduled_card.learning_state == LearningState.Learning
        assert rescheduled_card.step == 0
        assert rescheduled_card.stability is None
        assert rescheduled_card.difficulty is None
        assert rescheduled_card.last_review is None

    def test_fuzz_range_bounds(self):
        """
        _get_fuzz_range should always return min_ivl >= 2, max_ivl <= maximum_interval,
        and min_ivl <= max_ivl for a variety of interval lengths.
        """
        scheduler = Scheduler()

        for interval_days in [2, 5, 10, 20, 50, 100, 365, 36500]:
            min_ivl, max_ivl = scheduler._get_fuzz_range(interval_days)
            assert min_ivl >= 2, (
                f"min_ivl {min_ivl} < 2 for interval_days={interval_days}"
            )
            assert max_ivl <= scheduler.maximum_interval, (
                f"max_ivl {max_ivl} > maximum_interval for interval_days={interval_days}"
            )
            assert min_ivl <= max_ivl, (
                f"min_ivl {min_ivl} > max_ivl {max_ivl} for interval_days={interval_days}"
            )

    def test_performance_single_card_review(self):
        """
        A single review_card call should complete in under 10ms.
        """
        scheduler = Scheduler()
        card = Card()

        start = time.perf_counter()
        card, _ = scheduler.review_card(
            card=card,
            grade=Grade.Good,
            review_datetime=datetime.now(timezone.utc),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"review_card took {elapsed_ms:.2f}ms, expected < 10ms"

    def test_performance_reschedule_10000_cards(self):
        """
        Rescheduling 10,000 cards should complete in under 3 seconds.

        Each card is given the same review history (TEST_RATINGS_1) so they all
        have a realistic set of review logs. Only the rescheduling pass is timed.
        """
        scheduler = Scheduler(enable_fuzzing=False)

        num_cards = 10_000
        cards_and_logs = []

        # build review history for each card (not timed)
        for _ in range(num_cards):
            card = Card()
            review_logs = []
            for grade in TEST_RATINGS_1:
                card, review_log = scheduler.review_card(
                    card=card, grade=grade, review_datetime=card.due
                )
                review_logs.append(review_log)
            cards_and_logs.append((card, review_logs))

        start = time.perf_counter()
        for card, review_logs in cards_and_logs:
            scheduler.reschedule_card(card=card, review_logs=review_logs)
        elapsed_s = time.perf_counter() - start

        assert elapsed_s < 3.0, (
            f"Rescheduling 10,000 cards took {elapsed_s:.3f}s, expected < 3s"
        )