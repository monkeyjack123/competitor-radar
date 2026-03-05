"""competitor-radar package."""

from .change_detector import ChangeRecord, ChangeSummary, detect_changes, summarize_changes

__all__ = ["detect_changes", "summarize_changes", "ChangeRecord", "ChangeSummary"]
