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

