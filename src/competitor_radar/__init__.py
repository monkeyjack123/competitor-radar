"""competitor-radar package."""

from .change_detector import (
    ChangeRecord,
    ChangeSummary,
    PresenceDelta,
    detect_changes,
    detect_presence_changes,
    summarize_changes,
)

__all__ = [
    "detect_changes",
    "detect_presence_changes",
    "summarize_changes",
    "ChangeRecord",
    "ChangeSummary",
    "PresenceDelta",
]
