from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .change_detector import ChangeRecord, detect_changes


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


def run_change_report(path: Path, tracked_fields: list[str] | None = None) -> list[dict[str, str]]:
    payload = _load_payload(path)
    changes = detect_changes(
        previous_snapshot=payload["previous"],
        current_snapshot=payload["current"],
        tracked_fields=tracked_fields,
    )
    return [_to_dict(item) for item in changes]


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = run_change_report(Path(args.snapshot_file), tracked_fields=args.field)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
