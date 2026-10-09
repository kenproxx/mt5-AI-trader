"""Exclusive-create JSON export for sanitized Demo diagnostic audits."""
import json
from pathlib import Path


def export_audit_json(audit, path):
    destination = Path(path)
    if destination.suffix.lower() != ".json":
        raise ValueError("Audit destination must be .json")
    if destination.is_symlink():
        raise ValueError("Symlink destination forbidden")
    payload = audit.public_dict()
    if payload.get("can_trade") is not False:
        raise ValueError("Audit must explicitly forbid trading")
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n"
    if len(encoded.encode("utf-8")) > 8192:
        raise ValueError("Audit exceeds size limit")
    # Exclusive creation prevents silently overwriting previous evidence.
    with destination.open("x", encoding="utf-8") as output:
        output.write(encoded)
    return destination
