from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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


def _normalized_name(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().casefold()


def _filter_snapshot_by_competitors(
    snapshot: list[dict[str, Any]],
    competitors: list[str] | None,
) -> list[dict[str, Any]]:
    if not competitors:
        return snapshot

    allowed = {_normalized_name(name) for name in competitors if _normalized_name(name)}
    if not allowed:
        return snapshot

    return [
        record
        for record in snapshot
        if _normalized_name(record.get("competitor")) in allowed
    ]


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


def _diagnostics_to_dict(record: SnapshotDiagnostics) -> dict[str, object]:
    return {
        "duplicate_competitors": list(record.duplicate_competitors),
        "missing_competitor_rows": record.missing_competitor_rows,
    }


def run_change_report(
    path: Path,
    tracked_fields: list[str] | None = None,
    include_summary: bool = False,
    include_presence: bool = False,
    include_diagnostics: bool = False,
    competitors: list[str] | None = None,
) -> list[dict[str, str]] | dict[str, object]:
    payload = _load_payload(path)
    previous_snapshot = _filter_snapshot_by_competitors(payload["previous"], competitors)
    current_snapshot = _filter_snapshot_by_competitors(payload["current"], competitors)

    changes = detect_changes(
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
        tracked_fields=tracked_fields,
    )
    change_rows = [_to_dict(item) for item in changes]

    if not include_summary and not include_presence and not include_diagnostics:
        return change_rows

    response: dict[str, object] = {"changes": change_rows}

    if include_summary:
        summary_rows = [_summary_to_dict(item) for item in summarize_changes(changes)]
        response["summary"] = summary_rows

    if include_presence:
        presence = detect_presence_changes(previous_snapshot, current_snapshot)
        response["presence"] = _presence_to_dict(presence)

    if include_diagnostics:
        response["diagnostics"] = {
            "previous": _diagnostics_to_dict(analyze_snapshot(previous_snapshot)),
            "current": _diagnostics_to_dict(analyze_snapshot(current_snapshot)),
        }

    return response


def _change_count(report: list[dict[str, str]] | dict[str, object]) -> int:
    if isinstance(report, list):
        return len(report)

    changes = report.get("changes")
    if isinstance(changes, list):
        return len(changes)
    return 0


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
        "--competitor",
        action="append",
        default=None,
        help="Restrict report to one or more competitor names (case-insensitive, repeatable)",
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
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Include duplicate/missing competitor diagnostics for each snapshot",
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit with status 1 when one or more changes are detected (for CI checks)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the JSON report artifact",
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
            include_diagnostics=args.diagnostics,
            competitors=args.competitor,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    report_json = json.dumps(report, indent=2)
    print(report_json)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_json + "\n", encoding="utf-8")

    if args.fail_on_change and _change_count(report) > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
