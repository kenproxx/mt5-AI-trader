"""Sanitized, bounded monitoring events; no secrets or order execution."""
import json
from datetime import UTC, datetime

ALLOWED = frozenset({"component", "state", "reason", "symbol", "mode", "correlation_id"})


def make_event(component, state, **fields):
    data = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "component": str(component)[:80],
        "state": str(state)[:80],
    }
    for key, value in fields.items():
        if key not in ALLOWED or key in ("component", "state"):
            raise ValueError(f"Disallowed monitoring field: {key}")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise ValueError("Only scalar monitoring fields allowed")
        data[key] = str(value)[:240] if value is not None else None
    return data


def serialize_event(event):
    return json.dumps(event, sort_keys=True, ensure_ascii=True)
