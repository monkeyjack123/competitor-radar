"""competitor-radar package."""

from .change_detector import (
    ChangeRecord,
    ChangeSummary,
    PresenceDelta,
    SnapshotDiagnostics,
    analyze_snapshot,
    detect_changes,
    detect_presence_changes,
    summarize_changes,
)

__all__ = [
    "analyze_snapshot",
    "detect_changes",
    "detect_presence_changes",
    "summarize_changes",
    "ChangeRecord",
    "ChangeSummary",
    "PresenceDelta",
    "SnapshotDiagnostics",
]
