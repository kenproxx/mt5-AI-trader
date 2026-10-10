"""Integrity checks for non-authorizing, sanitized audit JSON."""
import hashlib
import json
from pathlib import Path

EXPECTED_FIELDS = frozenset({
    "checked_at_utc", "mode", "state", "reason", "risk_budget_usd",
    "estimated_minimum_margin_usd", "estimated_minimum_stop_loss_usd",
    "minimum_lot", "can_trade",
})


def verify_audit_file(path):
    destination = Path(path)
    if destination.is_symlink() or not destination.is_file():
        raise ValueError("Audit file unavailable or symlink")
    if destination.stat().st_size > 8192:
        raise ValueError("Audit file exceeds size limit")
    raw = destination.read_bytes()
    if len(raw) > 8192:
        raise ValueError("Audit file exceeds size limit")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid audit JSON") from exc
    if not isinstance(payload, dict) or frozenset(payload) != EXPECTED_FIELDS:
        raise ValueError("Unexpected audit schema")
    if payload["can_trade"] is not False or payload["mode"] not in ("DEMO", "UNVERIFIED"):
        raise ValueError("Audit authorization or mode invalid")
    if not all(isinstance(payload[key], str) for key in ("checked_at_utc", "state", "reason")):
        raise ValueError("Invalid audit metadata")
    for key in ("risk_budget_usd", "estimated_minimum_margin_usd",
                "estimated_minimum_stop_loss_usd", "minimum_lot"):
        if payload[key] is not None and not isinstance(payload[key], str):
            raise ValueError("Invalid audit amount")
    return hashlib.sha256(raw).hexdigest()
