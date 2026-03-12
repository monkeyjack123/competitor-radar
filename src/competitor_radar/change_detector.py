from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ChangeRecord:
    competitor: str
    field: str
    previous: str
    current: str


@dataclass(frozen=True)
class ChangeSummary:
    competitor: str
    changed_fields: tuple[str, ...]
    change_count: int


@dataclass(frozen=True)
class PresenceDelta:
    added: tuple[str, ...]
    removed: tuple[str, ...]


@dataclass(frozen=True)
class SnapshotDiagnostics:
    duplicate_competitors: tuple[str, ...]
    missing_competitor_rows: int


@dataclass(frozen=True)
class OverlapStats:
    previous_count: int
    current_count: int
    overlap_count: int
    overlap_ratio_previous: float
    overlap_ratio_current: float


@dataclass(frozen=True)
class FieldCoverage:
    field: str
    previous_non_empty: int
    previous_total: int
    previous_ratio: float
    current_non_empty: int
    current_total: int
    current_ratio: float


def _normalized(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized_competitor_key(value: object) -> str:
    return _normalized(value).casefold()


def _index_by_competitor(snapshot: Sequence[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    """Index snapshot rows by case-insensitive competitor key.

    If duplicate competitor names differ only by case/whitespace, the last record wins.
    """

    index: dict[str, Mapping[str, object]] = {}
    for item in snapshot:
        key = _normalized_competitor_key(item.get("competitor"))
        if not key:
            continue
        index[key] = item
    return index


def _display_name(item: Mapping[str, object]) -> str:
    return _normalized(item.get("competitor"))


def detect_presence_changes(
    previous_snapshot: Sequence[Mapping[str, object]],
    current_snapshot: Sequence[Mapping[str, object]],
) -> PresenceDelta:
    """Detect added/removed competitors between snapshots."""

    previous_index = _index_by_competitor(previous_snapshot)
    current_index = _index_by_competitor(current_snapshot)

    added = tuple(sorted(_display_name(current_index[key]) for key in (set(current_index) - set(previous_index))))
    removed = tuple(sorted(_display_name(previous_index[key]) for key in (set(previous_index) - set(current_index))))
    return PresenceDelta(added=added, removed=removed)


def analyze_snapshot(snapshot: Sequence[Mapping[str, object]]) -> SnapshotDiagnostics:
    """Return duplicate/missing competitor diagnostics for one snapshot."""

    names: list[str] = []
    missing = 0
    for item in snapshot:
        name = _normalized(item.get("competitor"))
        if not name:
            missing += 1
            continue
        names.append(name)

    counts = Counter(name.casefold() for name in names)
    first_display: dict[str, str] = {}
    for name in names:
        first_display.setdefault(name.casefold(), name)

    duplicates = tuple(sorted(first_display[key] for key, count in counts.items() if count > 1))
    return SnapshotDiagnostics(duplicate_competitors=duplicates, missing_competitor_rows=missing)


def count_competitor_overlap(
    previous_snapshot: Sequence[Mapping[str, object]],
    current_snapshot: Sequence[Mapping[str, object]],
) -> int:
    """Count competitor keys present in both snapshots (case-insensitive)."""

    previous_index = _index_by_competitor(previous_snapshot)
    current_index = _index_by_competitor(current_snapshot)
    return len(set(previous_index) & set(current_index))


def calculate_overlap_stats(
    previous_snapshot: Sequence[Mapping[str, object]],
    current_snapshot: Sequence[Mapping[str, object]],
) -> OverlapStats:
    """Calculate overlap counts/ratios between snapshots."""

    previous_index = _index_by_competitor(previous_snapshot)
    current_index = _index_by_competitor(current_snapshot)
    overlap_count = len(set(previous_index) & set(current_index))
    previous_count = len(previous_index)
    current_count = len(current_index)

    ratio_previous = overlap_count / previous_count if previous_count else 0.0
    ratio_current = overlap_count / current_count if current_count else 0.0

    return OverlapStats(
        previous_count=previous_count,
        current_count=current_count,
        overlap_count=overlap_count,
        overlap_ratio_previous=ratio_previous,
        overlap_ratio_current=ratio_current,
    )


def calculate_field_coverage(
    previous_snapshot: Sequence[Mapping[str, object]],
    current_snapshot: Sequence[Mapping[str, object]],
    tracked_fields: Iterable[str] | None = None,
) -> list[FieldCoverage]:
    """Calculate non-empty value coverage for tracked fields in previous/current snapshots."""

    fields = tuple(tracked_fields or ("positioning", "pricing", "feature_highlight"))
    previous_index = _index_by_competitor(previous_snapshot)
    current_index = _index_by_competitor(current_snapshot)

    previous_rows = tuple(previous_index.values())
    current_rows = tuple(current_index.values())
    previous_total = len(previous_rows)
    current_total = len(current_rows)

    rows: list[FieldCoverage] = []
    for field in fields:
        previous_non_empty = sum(1 for item in previous_rows if _normalized(item.get(field)) != "")
        current_non_empty = sum(1 for item in current_rows if _normalized(item.get(field)) != "")

        rows.append(
            FieldCoverage(
                field=field,
                previous_non_empty=previous_non_empty,
                previous_total=previous_total,
                previous_ratio=(previous_non_empty / previous_total if previous_total else 0.0),
                current_non_empty=current_non_empty,
                current_total=current_total,
                current_ratio=(current_non_empty / current_total if current_total else 0.0),
            )
        )

    return rows


def detect_changes(
    previous_snapshot: Sequence[Mapping[str, object]],
    current_snapshot: Sequence[Mapping[str, object]],
    tracked_fields: Iterable[str] | None = None,
) -> list[ChangeRecord]:
    """Detect per-field competitor changes between two snapshots.

    Input snapshots are arrays of dict-like records with a required `competitor` key.
    `tracked_fields` defaults to (`positioning`, `pricing`, `feature_highlight`).
    """

    fields = tuple(tracked_fields or ("positioning", "pricing", "feature_highlight"))
    previous_index = _index_by_competitor(previous_snapshot)
    current_index = _index_by_competitor(current_snapshot)

    changes: list[ChangeRecord] = []
    for competitor_key in sorted(set(previous_index) & set(current_index)):
        prev = previous_index[competitor_key]
        curr = current_index[competitor_key]
        competitor_name = _display_name(curr) or _display_name(prev)

        for field in fields:
            old = _normalized(prev.get(field))
            new = _normalized(curr.get(field))
            if old != new:
                changes.append(
                    ChangeRecord(
                        competitor=competitor_name,
                        field=field,
                        previous=old,
                        current=new,
                    )
                )

    return changes


def summarize_changes(changes: Sequence[ChangeRecord]) -> list[ChangeSummary]:
    """Group field-level changes into per-competitor summaries."""

    by_competitor: dict[str, list[str]] = {}
    for change in changes:
        by_competitor.setdefault(change.competitor, []).append(change.field)

    summaries: list[ChangeSummary] = []
    for competitor in sorted(by_competitor):
        fields = tuple(sorted(by_competitor[competitor]))
        summaries.append(
            ChangeSummary(
                competitor=competitor,
                changed_fields=fields,
                change_count=len(fields),
            )
        )

    return summaries
