# Change Detection (MVP)

`competitor-radar` now includes a deterministic field-level change detector for competitor snapshots.

## API

```python
from competitor_radar import detect_changes

changes = detect_changes(previous_snapshot, current_snapshot)
```

### Inputs
- `previous_snapshot`: list of competitor records
- `current_snapshot`: list of competitor records
- `tracked_fields` (optional): fields to compare (default: `positioning`, `pricing`, `feature_highlight`)

### Output
Returns a list of `ChangeRecord` entries:
- `competitor`
- `field`
- `previous`
- `current`

## Demo data
See `examples/snapshots.json` for before/after sample snapshots suitable for smoke tests and demos.
