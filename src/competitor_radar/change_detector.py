from __future__ import annotations

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


def _normalized(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
    previous_index = {_normalized(item.get("competitor")): item for item in previous_snapshot}
    current_index = {_normalized(item.get("competitor")): item for item in current_snapshot}

    changes: list[ChangeRecord] = []
    for competitor in sorted(set(previous_index) & set(current_index)):
        if not competitor:
            continue
        prev = previous_index[competitor]
        curr = current_index[competitor]

        for field in fields:
            old = _normalized(prev.get(field))
            new = _normalized(curr.get(field))
            if old != new:
                changes.append(
                    ChangeRecord(
                        competitor=competitor,
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
