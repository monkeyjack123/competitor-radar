# competitor-radar

Automated competitor monitoring and change intelligence

## Why this exists
This project helps teams launch products faster with measurable outcomes.

## MVP scope (v0.1)
- Core workflow
- API/CLI interface
- Example demo data
- Quickstart docs

## Roadmap
- v0.1: baseline MVP
- v0.2: integrations
- v0.3: collaboration + analytics improvements

## Getting started

### Run tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### MVP change-detection example

```python
from competitor_radar import detect_changes

changes = detect_changes(previous_snapshot, current_snapshot)
for item in changes:
    print(item)
```

See `docs/change-detection.md` and `examples/snapshots.json` for the demo input/output shape.

### CLI demo

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json
```

Optional: track a custom field list by repeating `--field`:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --field positioning
```

Include a per-competitor summary (change count + changed fields):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --field positioning --summary
```

Include competitor presence deltas (added/removed competitors between snapshots):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --presence
```

Include snapshot diagnostics (duplicate competitors + rows missing `competitor`):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --diagnostics
```

Restrict output to one or more competitors (case-insensitive). Competitor matching in change detection/presence is also case-insensitive:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --competitor nova --competitor acme
```

Fail the command when changes are detected (useful in CI checks):

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --field pricing --fail-on-change
```

Write the JSON report to an artifact file while still printing to stdout:

```bash
PYTHONPATH=src python3 -m competitor_radar.cli examples/snapshots.json --summary --output artifacts/change-report.json
```

