"""
services.fsrs.learning_state

Module that defines the LearningState class.

Ref: https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/state.py
"""

from enum import IntEnum

class LearningState(IntEnum):
    """
    Enum representing the learning state of a Card object.
    """
    Learning, Review, Relearning = 1, 2, 3