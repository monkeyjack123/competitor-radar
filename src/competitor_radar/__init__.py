"""competitor-radar package."""

from .change_detector import (
    ChangeRecord,
    ChangeSummary,
    PresenceDelta,
    SnapshotDiagnostics,
    OverlapStats,
    FieldCoverage,
    analyze_snapshot,
    calculate_field_coverage,
    calculate_overlap_stats,
    count_competitor_overlap,
    detect_changes,
    detect_presence_changes,
    summarize_changes,
)

__all__ = [
    "analyze_snapshot",
    "calculate_field_coverage",
    "calculate_overlap_stats",
    "count_competitor_overlap",
    "detect_changes",
    "detect_presence_changes",
    "summarize_changes",
    "ChangeRecord",
    "ChangeSummary",
    "PresenceDelta",
    "SnapshotDiagnostics",
    "OverlapStats",
    "FieldCoverage",
]
