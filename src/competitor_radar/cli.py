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


def _overlap_to_dict(record: OverlapStats) -> dict[str, object]:
    return {
        "previous_count": record.previous_count,
        "current_count": record.current_count,
        "overlap_count": record.overlap_count,
        "overlap_ratio_previous": record.overlap_ratio_previous,
        "overlap_ratio_current": record.overlap_ratio_current,
    }


def _coverage_to_dict(record: FieldCoverage) -> dict[str, object]:
    return {
        "field": record.field,
        "previous_non_empty": record.previous_non_empty,
        "previous_total": record.previous_total,
        "previous_ratio": record.previous_ratio,
        "current_non_empty": record.current_non_empty,
        "current_total": record.current_total,
        "current_ratio": record.current_ratio,
    }


def run_change_report(
    path: Path,
    tracked_fields: list[str] | None = None,
    include_summary: bool = False,
    include_presence: bool = False,
    include_diagnostics: bool = False,
    include_overlap: bool = False,
    include_coverage: bool = False,
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

    if not include_summary and not include_presence and not include_diagnostics and not include_overlap and not include_coverage:
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

    if include_overlap:
        response["overlap"] = _overlap_to_dict(calculate_overlap_stats(previous_snapshot, current_snapshot))

    if include_coverage:
        coverage_rows = [
            _coverage_to_dict(item)
            for item in calculate_field_coverage(previous_snapshot, current_snapshot, tracked_fields=tracked_fields)
        ]
        response["coverage"] = coverage_rows

    return response


def _change_count(report: list[dict[str, str]] | dict[str, object]) -> int:
    if isinstance(report, list):
        return len(report)

    changes = report.get("changes")
    if isinstance(changes, list):
        return len(changes)
    return 0


def _presence_change_count(report: list[dict[str, str]] | dict[str, object]) -> int:
    if isinstance(report, list):
        return 0

    presence = report.get("presence")
    if not isinstance(presence, dict):
        return 0

    added = presence.get("added")
    removed = presence.get("removed")
    added_count = len(added) if isinstance(added, list) else 0
    removed_count = len(removed) if isinstance(removed, list) else 0
    return added_count + removed_count


def _diagnostic_issue_count(report: list[dict[str, str]] | dict[str, object]) -> tuple[int, int]:
    if isinstance(report, list):
        return (0, 0)

    diagnostics = report.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return (0, 0)

    duplicate_count = 0
    missing_count = 0
    for snapshot_key in ("previous", "current"):
        snapshot_diag = diagnostics.get(snapshot_key)
        if not isinstance(snapshot_diag, dict):
            continue

        duplicates = snapshot_diag.get("duplicate_competitors")
        if isinstance(duplicates, list):
            duplicate_count += len(duplicates)

        missing = snapshot_diag.get("missing_competitor_rows")
        if isinstance(missing, int):
            missing_count += max(missing, 0)

    return (duplicate_count, missing_count)


def _overlap_min_ratio(report: list[dict[str, str]] | dict[str, object]) -> float | None:
    if isinstance(report, list):
        return None

    overlap = report.get("overlap")
    if not isinstance(overlap, dict):
        return None

    prev_ratio = overlap.get("overlap_ratio_previous")
    curr_ratio = overlap.get("overlap_ratio_current")
    if not isinstance(prev_ratio, (int, float)) or not isinstance(curr_ratio, (int, float)):
        return None

    return float(min(prev_ratio, curr_ratio))


def _coverage_min_current_ratio(report: list[dict[str, str]] | dict[str, object]) -> float | None:
    if isinstance(report, list):
        return None

    coverage = report.get("coverage")
    if not isinstance(coverage, list) or not coverage:
        return None

    ratios: list[float] = []
    for row in coverage:
        if not isinstance(row, dict):
            continue
        ratio = row.get("current_ratio")
        if isinstance(ratio, (int, float)):
            ratios.append(float(ratio))

    if not ratios:
        return None

    return min(ratios)


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
        "--overlap",
        action="store_true",
        help="Include overlap counts/ratios for previous vs current snapshots",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Include tracked-field non-empty coverage for previous/current snapshots",
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit with status 1 when one or more field-level changes are detected (for CI checks)",
    )
    parser.add_argument(
        "--fail-on-presence",
        action="store_true",
        help="Exit with status 1 when competitors are added/removed between snapshots",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit with status 1 when duplicate competitor names exist in either snapshot",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with status 1 when rows are missing `competitor` in either snapshot",
    )
    parser.add_argument(
        "--fail-on-no-overlap",
        action="store_true",
        help="Exit with status 1 when previous/current snapshots have zero overlapping competitors",
    )
    parser.add_argument(
        "--fail-on-overlap-below",
        type=float,
        default=None,
        help="Exit with status 1 when min(previous_overlap_ratio,current_overlap_ratio) is below threshold (0.0-1.0)",
    )
    parser.add_argument(
        "--fail-on-coverage-below",
        type=float,
        default=None,
        help="Exit with status 1 when min(current_ratio) across coverage fields is below threshold (0.0-1.0)",
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

    if args.fail_on_overlap_below is not None and not (0.0 <= args.fail_on_overlap_below <= 1.0):
        parser.exit(2, "error: --fail-on-overlap-below must be between 0.0 and 1.0\n")

    if args.fail_on_coverage_below is not None and not (0.0 <= args.fail_on_coverage_below <= 1.0):
        parser.exit(2, "error: --fail-on-coverage-below must be between 0.0 and 1.0\n")

    try:
        report = run_change_report(
            Path(args.snapshot_file),
            tracked_fields=args.field,
            include_summary=args.summary,
            include_presence=(args.presence or args.fail_on_presence),
            include_diagnostics=(args.diagnostics or args.fail_on_duplicates or args.fail_on_missing),
            include_overlap=(args.overlap or args.fail_on_no_overlap or args.fail_on_overlap_below is not None),
            include_coverage=(args.coverage or args.fail_on_coverage_below is not None),
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

    if args.fail_on_presence and _presence_change_count(report) > 0:
        return 1

    duplicate_count, missing_count = _diagnostic_issue_count(report)
    if args.fail_on_duplicates and duplicate_count > 0:
        return 1

    if args.fail_on_missing and missing_count > 0:
        return 1

    if args.fail_on_no_overlap:
        payload = _load_payload(Path(args.snapshot_file))
        previous_snapshot = _filter_snapshot_by_competitors(payload["previous"], args.competitor)
        current_snapshot = _filter_snapshot_by_competitors(payload["current"], args.competitor)
        if count_competitor_overlap(previous_snapshot, current_snapshot) == 0:
            return 1

    if args.fail_on_overlap_below is not None:
        min_ratio = _overlap_min_ratio(report)
        if min_ratio is not None and min_ratio < args.fail_on_overlap_below:
            return 1

    if args.fail_on_coverage_below is not None:
        min_coverage_ratio = _coverage_min_current_ratio(report)
        if min_coverage_ratio is not None and min_coverage_ratio < args.fail_on_coverage_below:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
