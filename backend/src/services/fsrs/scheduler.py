"""
services.fsrs.card

Module that defines the Card class.

Ref: https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/scheduler.py
"""

import math
import torch
from random import random
from copy import copy
from numbers import Real
from services.fsrs.grade import Grade
from services.fsrs.learning_state import LearningState
from services.fsrs.card import Card
from services.fsrs.review_log import ReviewLog
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, Any

# --- CONSTANTS ---
FSRS_DEFAULT_DECAY = 0.1542
DEFAULT_PARAMETERS = (0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, FSRS_DEFAULT_DECAY)

STABILITY_MIN = 0.001
LOWER_BOUNDS_PARAMETERS = (STABILITY_MIN, STABILITY_MIN, STABILITY_MIN, STABILITY_MIN, 1.0, 0.001, 0.001, 0.001, 0.0, 0.0, 0.001, 0.001, 0.001, 0.001, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.1)

INITIAL_STABILITY_MAX = 100.0
UPPER_BOUNDS_PARAMETERS = (INITIAL_STABILITY_MAX, INITIAL_STABILITY_MAX, INITIAL_STABILITY_MAX, INITIAL_STABILITY_MAX, 10.0, 4.0, 4.0, 0.75, 4.5, 0.8, 3.5, 5.0, 0.25, 0.9, 4.0, 1.0, 6.0, 2.0, 2.0, 0.8, 0.8)

DIFFICULTY_MIN = 1.0
DIFFICULTY_MAX = 10.0

FUZZ_RANGES = [{"start": 2.5, "end": 7.0, "factor": 0.15}, {"start": 7.0, "end": 20.0, "factor": 0.1}, {"start": 20.0, "end": math.inf, "factor": 0.05}]


class Scheduler(BaseModel):
    """
    Enables the reviewing and future scheduling of cards according to the FSRS algorithm.

    Attributes:
        parameters:         The model weights of the FSRS scheduler.  Can be tuple of floats or torch.Tensor during optimization.
        desired_retention:  The desired retention rate of cards scheduled with the scheduler. NOTE this value should come from the variable stored in the user table.
        learning_steps:     Small time intervals that schedule cards in the Learning state.
        relearning_steps:   Small time intervals that schedule cards in the Relearning state.
        maximum_interval:   The maximum number of days a Review-state card can be scheduled into the future.
        enable_fuzzing:     Whether to apply a small amount of random 'fuzz' to calculated intervals.
    """
    parameters: Any = Field(default_factory=lambda: DEFAULT_PARAMETERS)
    desired_retention: float = Field(default=0.9, ge=0.0, le=1.0)
    learning_steps: tuple[timedelta, ...] = Field(default_factory=lambda: (timedelta(minutes=1), timedelta(minutes=10)))
    relearning_steps: tuple[timedelta, ...] = Field(default_factory=lambda: (timedelta(minutes=10),))
    maximum_interval: int = Field(default=36500, gt=0)
    enable_fuzzing: bool = True
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __str__(self):
        """Return same representation as repr() for consistency."""
        return repr(self)

    @model_validator(mode="after")
    def validate_parameters(self) -> "Scheduler":
        parameters = self.parameters
        
        # Convert list to tuple (happens when deserializing from JSON)
        if isinstance(parameters, list):
            self.parameters = tuple(parameters)
            parameters = self.parameters
        
        # If parameters is a tensor, skip validation (used during optimization)
        if isinstance(parameters, torch.Tensor):
            self._DECAY = -self.parameters[20]
            self._FACTOR = 0.9 ** (1 / self._DECAY) - 1
            return self

        if len(parameters) != len(LOWER_BOUNDS_PARAMETERS):
            raise ValueError(
                f"Expected {len(LOWER_BOUNDS_PARAMETERS)} parameters, "
                f"got {len(parameters)}."
            )

        error_messages: list[str] = []
        for index, (parameter, lower_bound, upper_bound) in enumerate(zip(parameters, LOWER_BOUNDS_PARAMETERS, UPPER_BOUNDS_PARAMETERS)):
            if not lower_bound <= parameter <= upper_bound:
                error_messages.append(
                    f"parameters[{index}] = {parameter} is out of bounds: "
                    f"({lower_bound}, {upper_bound})"
                )

        if error_messages:
            raise ValueError("One or more parameters are out of bounds:\n" + "\n".join(error_messages))
        

        # define _DECAY and _FACTOR after parameters are validated, rather than in a post_model_init()
        self._DECAY = -self.parameters[20]
        self._FACTOR = 0.9 ** (1 / self._DECAY) - 1

        return self


    def get_card_retrievability(self, card: Card, current_datetime: Optional[datetime] = None) -> Any:
        """
        Calculates a Card object's current retrievability for a given date and time.

        The retrievability of a card is the predicted probability that the card is correctly recalled at the provided datetime.

        Args:
            card:               The card whose retrievability is to be calculated
            current_datetime:   The current date and time

        Returns:
            float: The retrievability of the Card object.
        """

        if card.last_review is None or card.stability is None:
            return 0

        if current_datetime is None:
            current_datetime = datetime.now(timezone.utc)

        elapsed_days = max(0, (current_datetime - card.last_review).days)

        return (1 + self._FACTOR * elapsed_days / card.stability) ** self._DECAY


    def _move_to_review_state(self, card: Card) -> timedelta:
        """
        Helper function for review_card() that performs the necessary steps to send a card into the Review Learning State and update the interval.

        Args:
            card: the card that is being reviewed

        Returns:
            timedelta: the next interval (in days).
        """
        assert card.stability is not None

        card.learning_state = LearningState.Review
        card.step = None

        next_interval_days = self._next_interval(stability=card.stability)
        return timedelta(days=next_interval_days)
    
    
    def review_card(self, card: Card, grade: Grade, review_datetime: Optional[datetime] = None, review_duration: Optional[int] = None) -> tuple[Card, ReviewLog]:
        """
        Updates a card's state after a user review.

        It computes the new stability and difficulty, determines the next interval before the card should be reviewed again, 
        and generates a ReviewLog entry for that review.

        Args:
            card:               The card being reviewed.
            grade:              The chosen grade for the card being reviewed.
            review_datetime:    The date and time of the review.
            review_duration:    The number of miliseconds it took to review the card or None if unspecified.

        Returns:
            tuple[Card, ReviewLog]: A tuple containing the updated, reviewed card and its corresponding review log.

        Raises:
            ValueError: If the `review_datetime` argument is not timezone-aware and set to UTC.
        """

        if review_datetime is not None and ((review_datetime.tzinfo is None) or (review_datetime.tzinfo != timezone.utc)):
            raise ValueError("datetime must be timezone-aware and set to UTC")

        card = copy(card)

        if review_datetime is None:
        # make sure each call gets slightly incremented timestamp
            review_datetime = datetime.now(timezone.utc)
            if hasattr(self, "_last_review_dt") and review_datetime <= self._last_review_dt:
                review_datetime = self._last_review_dt + timedelta(microseconds=1)
            self._last_review_dt = review_datetime

        days_since_last_review = ((review_datetime - card.last_review).days if card.last_review else None)

        match card.learning_state:
            case LearningState.Learning:
                assert card.step is not None

                # update the card's stability and difficulty
                if card.stability is None or card.difficulty is None:
                    card.stability = self._initial_stability(grade)
                    card.difficulty = self._initial_difficulty(grade, True)
                    
                elif days_since_last_review is not None and days_since_last_review < 1:
                    card.stability = self._short_term_stability(card.stability, grade)
                    card.difficulty = self._next_difficulty(card.difficulty, grade)

                else:
                    card.stability = self._next_stability(card.difficulty, card.stability, self.get_card_retrievability(card, current_datetime=review_datetime), grade)
                    card.difficulty = self._next_difficulty(card.difficulty, grade)

                # calculate the card's next interval
                # first if-clause handles edge case where the Card in the Learning state was previously scheduled with a Scheduler with more learning_steps than the current Scheduler
                if len(self.learning_steps) == 0 or (card.step >= len(self.learning_steps) and grade in (Grade.Hard, Grade.Good, Grade.Easy)):
                    next_interval = self._move_to_review_state(card)

                else:
                    match grade:
                        case Grade.Again:
                            card.step = 0
                            next_interval = self.learning_steps[card.step]

                        case Grade.Hard:
                            # card step stays the same

                            if card.step == 0 and len(self.learning_steps) == 1:
                                next_interval = self.learning_steps[0] * 1.5
                            elif card.step == 0 and len(self.learning_steps) >= 2:
                                next_interval = (self.learning_steps[0] + self.learning_steps[1]) / 2.0
                            else:
                                next_interval = self.learning_steps[card.step]

                        case Grade.Good:
                            if card.step + 1 == len(self.learning_steps):  # the last step
                                next_interval = self._move_to_review_state(card)


                            else:
                                card.step += 1
                                next_interval = self.learning_steps[card.step]

                        case Grade.Easy:
                            next_interval = self._move_to_review_state(card)

            case LearningState.Review:
                assert card.stability is not None
                assert card.difficulty is not None

                # update the card's stability and difficulty
                if days_since_last_review is not None and days_since_last_review < 1:
                    card.stability = self._short_term_stability(card.stability, grade)
                else:
                    card.stability = self._next_stability(card.difficulty, card.stability, self.get_card_retrievability(card,current_datetime=review_datetime), grade)

                card.difficulty = self._next_difficulty(card.difficulty, grade)

                # calculate the card's next interval
                match grade:
                    case Grade.Again:
                        # if there are no relearning steps (they were left blank)
                        if len(self.relearning_steps) == 0:
                            next_interval_days = self._next_interval(stability=card.stability)
                            next_interval = timedelta(days=next_interval_days)

                        else:
                            card.learning_state = LearningState.Relearning
                            card.step = 0

                            next_interval = self.relearning_steps[card.step]

                    case Grade.Hard | Grade.Good | Grade.Easy:
                        next_interval_days = self._next_interval(stability=card.stability)
                        next_interval = timedelta(days=next_interval_days)

            case LearningState.Relearning:
                assert card.stability is not None
                assert card.difficulty is not None
                assert card.step is not None

                # update the card's stability and difficulty
                if days_since_last_review is not None and days_since_last_review < 1:
                    card.stability = self._short_term_stability(card.stability, grade)
                    card.difficulty = self._next_difficulty(card.difficulty, grade)

                else:
                    card.stability = self._next_stability(card.difficulty, card.stability,self.get_card_retrievability(card, current_datetime=review_datetime), grade)
                    card.difficulty = self._next_difficulty(card.difficulty, grade)

                # calculate the card's next interval
                ## first if-clause handles edge case where the Card in the Relearning state was previously
                ## scheduled with a Scheduler with more relearning_steps than the current Scheduler
                if len(self.relearning_steps) == 0 or (card.step >= len(self.relearning_steps) and grade in (Grade.Hard, Grade.Good, Grade.Easy)):
                    card.learning_state = LearningState.Review
                    card.step = None

                    next_interval_days = self._next_interval(stability=card.stability)
                    next_interval = timedelta(days=next_interval_days)

                else:
                    match grade:
                        case Grade.Again:
                            card.step = 0
                            next_interval = self.relearning_steps[card.step]

                        case Grade.Hard:
                            # card step stays the same

                            if card.step == 0 and len(self.relearning_steps) == 1:
                                next_interval = self.relearning_steps[0] * 1.5
                            elif card.step == 0 and len(self.relearning_steps) >= 2:
                                next_interval = (
                                    self.relearning_steps[0] + self.relearning_steps[1]
                                ) / 2.0
                            else:
                                next_interval = self.relearning_steps[card.step]

                        case Grade.Good:
                            if card.step + 1 == len(self.relearning_steps):  # the last step
                                next_interval = self._move_to_review_state(card)

                            else:
                                card.step += 1
                                next_interval = self.relearning_steps[card.step]

                        case Grade.Easy:
                            next_interval = self._move_to_review_state(card)

        if self.enable_fuzzing and card.learning_state == LearningState.Review:
            next_interval = self._get_fuzzed_interval(interval=next_interval)

        card.due = review_datetime + next_interval
        card.last_review = review_datetime

        review_log = ReviewLog(card_id=card.card_id, grade=grade, review_datetime=review_datetime, review_duration=review_duration)

        return card, review_log


    def reschedule_card(self, card: Card, review_logs: list[ReviewLog]) -> Card:
        """
        Reschedules/updates the given card with the current scheduler provided that card's review logs.

        If the current card was previously scheduled with a different scheduler, you may want to reschedule/update
        it as if it had always been scheduled with this current scheduler. For example, you may want to reschedule
        each of your cards with a new scheduler after computing the optimal parameters with the Optimizer.

        Args:
            card:           The card to be rescheduled/updated.
            review_logs:    A list of that card's review logs (order doesn't matter).

        Returns:
            Card: A new card that has been rescheduled/updated with this current scheduler.

        Raises:
            ValueError: If any of the review logs are for a card other than the one specified, this will raise an error.
        """
        for review_log in review_logs:
            if review_log.card_id != card.card_id:
                raise ValueError(f"ReviewLog card_id {review_log.card_id} does not match Card card_id {card.card_id}")

        review_logs = sorted(review_logs, key=lambda log: log.review_datetime)

        rescheduled_card = Card(card_id=card.card_id, due=card.due)

        for review_log in review_logs:
            rescheduled_card, _ = self.review_card(rescheduled_card, review_log.grade, review_log.review_datetime)

        return rescheduled_card


    def _clamp_difficulty_min_max(self, difficulty: float) -> float:
        """
        Clamps the difficulty so it stays in the bounds of DIFFICULTY_MIN and DIFFICULTY_MAX.

        Args:
            difficulty: The unclamped difficulty.
        
        Returns:
            float: the clamped difficulty.
        """
        if isinstance(difficulty, Real):
            difficulty = min(max(difficulty, DIFFICULTY_MIN), DIFFICULTY_MAX)
        else:  # type(difficulty) is torch.Tensor
            difficulty = difficulty.clamp(min=DIFFICULTY_MIN, max=DIFFICULTY_MAX)

        return difficulty


    def _clamp_stability_min(self, stability: float) -> float:
        """
        Obtains the stability so it doesn't go below STABILITY_MIN

        Args:
            stability: the unclamped stability.

        Returns:
            float: the clamped stability.
        """
        if isinstance(stability, Real):
            stability = max(stability, STABILITY_MIN)
        else:  # type(stability) is torch.Tensor
            stability = stability.clamp(min=STABILITY_MIN)

        return stability
    

    def _initial_stability(self, grade: Grade) -> float:
        """
        Obtains the initial stability value given the grade.

        The first 4 parameters are the initial stability values (one for each grade)

        Args:
            grade: The grade associated with the returned initial stability.

        Returns:
            float: the initial stability for the given grade.
        """
        initial_stability = self.parameters[grade - 1]
        initial_stability = self._clamp_stability_min(initial_stability)

        return initial_stability


    def _initial_difficulty(self, grade: Grade, clamp: bool = True) -> float:
        """
        Returns the initial difficulty value given the grade.

        Args:
            grade: the grade associated with the returned initial difficulty. 
            clamp: True if the difficulty should be clamped, False otherwise.

        Returns:
            float: the initial difficulty for the given grade.
        """
        initial_difficulty = (self.parameters[4] - (math.e ** (self.parameters[5] * (grade - 1))) + 1)

        if clamp:
            initial_difficulty = self._clamp_difficulty_min_max(initial_difficulty)

        return initial_difficulty


    def _next_interval(self, stability: float) -> int:
        """
        Calculates the next interval (in full days) given a stability value.

        Args:
            stability: the estimated time in days that is required for the probability of recalling to fall below the desired retention.

        Returns:
            int: the next interval (in full days).
        """
        next_interval = (stability / self._FACTOR) * ((self.desired_retention ** (1 / self._DECAY)) - 1)

        if not isinstance(next_interval, Real):  # type(next_interval) is torch.Tensor
            next_interval = (next_interval.detach().item())

        next_interval = round(next_interval)  # intervals are full days

        # must be at least 1 day long
        next_interval = max(next_interval, 1)

        # can not be longer than the maximum interval
        next_interval = min(next_interval, self.maximum_interval)

        return next_interval


    def _short_term_stability(self, stability: float, grade: Grade) -> float:
        """
        Calcualtes the short term stability for same day reviews given the current stability and grade.

        Args:
            stability: the current stability of the card. The estimated time in days that is required for the probability of recalling to fall below the desired retention.
            grade: the grade assigned to the card during the review.

        Returns:
            float: the clamped short term stability.
        """
        short_term_stability_increase = (math.e ** (self.parameters[17] * (grade - 3 + self.parameters[18]))) * (stability ** -self.parameters[19])

        if grade in (Grade.Good, Grade.Easy):  # Good and Easy grades cannot decrease stability
            if isinstance(short_term_stability_increase, Real):
                short_term_stability_increase = max(short_term_stability_increase, 1.0)
            else:  # type(short_term_stability_increase) is torch.Tensor
                short_term_stability_increase = short_term_stability_increase.clamp(min=1.0)

        short_term_stability = stability * short_term_stability_increase
        short_term_stability = self._clamp_stability_min(short_term_stability)

        return short_term_stability


    def _next_difficulty(self, difficulty: float, grade: Grade) -> float:
        """
        Calculates the next difficulty given the current difficulty and grade.

        Args:
            difficulty: the current difficulty of the card. A value between 0 and 10.
            grade:      the grade assigned to the card during the review.

        Returns:
            float: the next difficulty, after clamping.
        """
        def _linear_damping(delta_difficulty: float, difficulty: float) -> float:
            return (10.0 - difficulty) * delta_difficulty / 9.0

        def _mean_reversion(arg_1: float, arg_2: float) -> float:
            return self.parameters[7] * arg_1 + (1 - self.parameters[7]) * arg_2

        arg_1 = self._initial_difficulty(grade=Grade.Easy, clamp=False)

        delta_difficulty = -(self.parameters[6] * (grade - 3))
        arg_2 = difficulty + _linear_damping(delta_difficulty, difficulty)

        next_difficulty = _mean_reversion(arg_1, arg_2)

        next_difficulty = self._clamp_difficulty_min_max(next_difficulty)

        return next_difficulty


    def _next_stability(self, difficulty: float, stability: float, retrievability: float, grade: Grade) -> float:
        """
        Calculates the next stability given the current difficulty, current stability, retrievability, and grade.

        The stability increases if the recall is successful: Easy, Good, or Hard
        The stability decreases if the recall is unsuccessful: Again

        Args:
            difficulty:     the current difficulty of the card. A value between 0 and 10.
            stability:      the current stability of the card. The estimated time in days that is required for the probability of recalling to fall below the desired retention.
            retrievability: the current retrievability of the card. The estimated probability of successful recall at the moment the review occurred. A value between 0 and 1.
            grade:          the grade assigned to the card during the review.

        Returns:
            float: the next stability.
        """
        if grade == Grade.Again:
            next_stability = self._next_forget_stability(difficulty, stability, retrievability)

        elif grade in (Grade.Hard, Grade.Good, Grade.Easy):
            next_stability = self._next_recall_stability(difficulty, stability, retrievability, grade)

        next_stability = self._clamp_stability_min(next_stability)

        return next_stability


    def _next_forget_stability(self, difficulty: float, stability: float, retrievability: float) -> float:
        """
        Calculates the next stability of a forgotten word (Grade: Again). The stability will decrease.

        Args:
            difficulty:     the current difficulty of the card. A value between 0 and 10.
            stability:      the current stability of the card. The estimated time in days that is required for the probability of recalling to fall below the desired retention.
            retrievability: the current retrievability of the card. The estimated probability of successful recall at the moment the review occurred. A value between 0 and 1.

        Returns:
            float: the next stability.
        """
        next_forget_stability_long_term_params = (
            self.parameters[11]
            * (difficulty ** -self.parameters[12])
            * (((stability + 1) ** (self.parameters[13])) - 1)
            * (math.e ** ((1 - retrievability) * self.parameters[14]))
        )

        next_forget_stability_short_term_params = stability / (math.e ** (self.parameters[17] * self.parameters[18]))

        return min(next_forget_stability_long_term_params, next_forget_stability_short_term_params)


    def _next_recall_stability(self, difficulty: float, stability: float, retrievability: float, grade: Grade) -> float:
        """
        Calculates the next stability of a recalled word (Grade: Easy, Good, Hard). The stability will increase.

        Args:
            difficulty:     the current difficulty of the card. A value between 0 and 10.
            stability:      the current stability of the card. The estimated time in days that is required for the probability of recalling to fall below the desired retention.
            retrievability: the current retrievability of the card. The estimated probability of successful recall at the moment the review occurred. A value between 0 and 1.

        Returns:
            float: the next stability.
        """
        hard_penalty = self.parameters[15] if grade == Grade.Hard else 1
        easy_bonus = self.parameters[16] if grade == Grade.Easy else 1

        return stability * (
            1
            + (math.e ** (self.parameters[8]))
            * (11 - difficulty)
            * (stability ** -self.parameters[9])
            * ((math.e ** ((1 - retrievability) * self.parameters[10])) - 1)
            * hard_penalty
            * easy_bonus
        )


    def _get_fuzz_range(self, interval_days: int) -> tuple[int, int]:
        """
        Helper function for _get_fuzzed_interval() that computes the possible upper and lower bounds of the interval after fuzzing.

        Args:
            interval_days: the days of the current calculated next interval.

        Returns:
            tuple[int, int]: the minimal interval value and maximum interval value (in days).
        """

        delta = 1.0
        for fuzz_range in FUZZ_RANGES:
            delta += fuzz_range["factor"] * max(
                min(interval_days, fuzz_range["end"]) - fuzz_range["start"], 0.0
            )

        min_ivl = int(round(interval_days - delta))
        max_ivl = int(round(interval_days + delta))

        # make sure the min_ivl and max_ivl fall into a valid range
        min_ivl = max(2, min_ivl)
        max_ivl = min(max_ivl, self.maximum_interval)
        min_ivl = min(min_ivl, max_ivl)

        return min_ivl, max_ivl


    def _get_fuzzed_interval(self, interval: timedelta) -> timedelta:
        """
        Takes the current calculated interval and adds a small amount of random fuzz to it.
        For example, a card that would've been due in 50 days, after fuzzing, might be due in 49, or 51 days.

        Args:
            interval: The calculated next interval, before fuzzing.

        Returns:
            timedelta: The new interval, after fuzzing.
        """

        interval_days = interval.days

        if interval_days < 2.5:  # fuzz is not applied to intervals less than 2.5
            return interval

        min_ivl, max_ivl = self._get_fuzz_range(interval_days)

        fuzzed_interval_days = (random() * (max_ivl - min_ivl + 1)) + min_ivl  # the next interval is a random value between min_ivl and max_ivl

        fuzzed_interval_days = min(round(fuzzed_interval_days), self.maximum_interval) # clamp the fuzzed interval

        fuzzed_interval = timedelta(days=fuzzed_interval_days)

        return fuzzed_interval
    

    def __str__(self) -> str:
        return self.__repr__()