"""
services.fsrs.grade

Module that defines the Grade class.

Ref: https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/rating.py
"""

from enum import IntEnum

class Grade(IntEnum):
    """
    Enum representing the four possible grades when reviewing a Card object.
    """
    Again, Hard, Good, Easy = 1, 2, 3, 4