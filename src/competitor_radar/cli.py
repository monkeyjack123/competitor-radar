from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .change_detector import (
    ChangeRecord,
    ChangeSummary,
    PresenceDelta,
    detect_changes,
    detect_presence_changes,
    summarize_changes,
)


def _load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object with 'previous' and 'current' keys")

    previous = payload.get("previous")
    current = payload.get("current")
    if not isinstance(previous, list) or not isinstance(current, list):
        raise ValueError("Input JSON must include array fields: 'previous' and 'current'")

    return payload


def _to_dict(record: ChangeRecord) -> dict[str, str]:
    return {
        "competitor": record.competitor,
        "field": record.field,
        "previous": record.previous,
        "current": record.current,
    }


def _summary_to_dict(record: ChangeSummary) -> dict[str, object]:
    return {
        "competitor": record.competitor,
        "changed_fields": list(record.changed_fields),
        "change_count": record.change_count,
    }


def _presence_to_dict(record: PresenceDelta) -> dict[str, list[str]]:
    return {
        "added": list(record.added),
        "removed": list(record.removed),
    }


def run_change_report(
    path: Path,
    tracked_fields: list[str] | None = None,
    include_summary: bool = False,
    include_presence: bool = False,
) -> list[dict[str, str]] | dict[str, object]:
    payload = _load_payload(path)
    previous_snapshot = payload["previous"]
    current_snapshot = payload["current"]

    changes = detect_changes(
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
        tracked_fields=tracked_fields,
    )
    change_rows = [_to_dict(item) for item in changes]

    if not include_summary and not include_presence:
        return change_rows

    response: dict[str, object] = {"changes": change_rows}

    if include_summary:
        summary_rows = [_summary_to_dict(item) for item in summarize_changes(changes)]
        response["summary"] = summary_rows

    if include_presence:
        presence = detect_presence_changes(previous_snapshot, current_snapshot)
        response["presence"] = _presence_to_dict(presence)

    return response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="competitor-radar",
        description="Generate field-level competitor change reports from snapshot JSON",
    )
    parser.add_argument("snapshot_file", help="Path to snapshot JSON containing previous/current arrays")
    parser.add_argument(
        "--field",
        action="append",
        default=None,
        help="Field to track (repeat for multiple fields)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Include per-competitor summary with change_count and changed_fields",
    )
    parser.add_argument(
        "--presence",
        action="store_true",
        help="Include added/removed competitor presence changes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = run_change_report(
            Path(args.snapshot_file),
            tracked_fields=args.field,
            include_summary=args.summary,
            include_presence=args.presence,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
