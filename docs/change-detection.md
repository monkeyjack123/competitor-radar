# Change Detection (MVP)

`competitor-radar` now includes deterministic field-level change detection for competitor snapshots, plus optional per-competitor summary output and presence deltas.

## API

```python
from competitor_radar import detect_changes, detect_presence_changes, summarize_changes

changes = detect_changes(previous_snapshot, current_snapshot)
summary = summarize_changes(changes)
presence = detect_presence_changes(previous_snapshot, current_snapshot)
```

### `detect_changes` inputs
- `previous_snapshot`: list of competitor records
- `current_snapshot`: list of competitor records
- `tracked_fields` (optional): fields to compare (default: `positioning`, `pricing`, `feature_highlight`)

### `detect_changes` output
Returns a list of `ChangeRecord` entries:
- `competitor`
- `field`
- `previous`
- `current`

Competitor matching is case-insensitive (whitespace-trimmed) across snapshots.

### `summarize_changes` output
Returns a list of `ChangeSummary` entries:
- `competitor`
- `changed_fields` (tuple of changed fields)
- `change_count` (number of changed fields)

### `detect_presence_changes` output
Returns a `PresenceDelta` entry:
- `added` (tuple of competitor names present only in current snapshot)
- `removed` (tuple of competitor names present only in previous snapshot)

## CLI change report
Run the CLI against a snapshot payload (`previous` + `current`) to generate a JSON change report:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json
```

You can scope comparison fields:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --field positioning
```

You can include a summary section:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --field positioning --summary
```

You can include presence changes (added/removed competitors):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --presence
```

You can also restrict report output to specific competitors (case-insensitive, repeat `--competitor`):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --competitor nova --competitor acme
```

`--summary` and `--presence` can be combined in the same run.

Use `--fail-on-change` to return exit code `1` if any change is detected (handy for CI guardrails):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --fail-on-change
```

## Demo data
See `examples/snapshots.json` for before/after sample snapshots suitable for smoke tests and demos.
