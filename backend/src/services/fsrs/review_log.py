"""
services.fsrs.card

Module that defines the ReviewLog class.

Ref: https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/review_log.py
"""

from services.fsrs.grade import Grade
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ReviewLog(BaseModel):
    """
    Represents a log for a single card review.

    Attributes:
        card_id: str                # The id of the card being reviewed.
        grade: int                  # The grade given to the card during the review.
        review_datetime: datetime   # The datetime object of when the review took place.
        review_duration: int        # The number of milliseconds it took to review the card. None if unspecified.
    """
    card_id: str
    grade: Grade
    review_datetime: datetime
    review_duration: Optional[int] = None

    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat(),
        },
    }


    def __str__(self) -> str:
        return self.__repr__()