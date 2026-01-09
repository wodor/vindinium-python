"""Game status enum."""

from enum import Enum


class Status(str, Enum):
    """Game status states."""
    CREATED = "Created"
    STARTED = "Started"
    ALL_CRASHED = "AllCrashed"
    TURN_MAX = "TurnMax"

    def is_finished(self) -> bool:
        """Check if game is finished."""
        return self in (Status.ALL_CRASHED, Status.TURN_MAX)
