"""Atomic local guard state. Never reset corrupted state automatically."""
import json
import os
import tempfile
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from app.automation.guards import GuardState

_FIELDS = frozenset(GuardState.__dataclass_fields__)


def load_state(path: str | Path) -> GuardState | None:
    file = Path(path)
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if data.get("schema") != 1 or set(data) != _FIELDS | {"schema"}:
            raise ValueError("Unexpected guard state schema")
        for key in ("day_start_equity", "week_start_equity", "week_peak_equity"):
            if type(data[key]) is not str:
                raise ValueError("Expected Decimal string")
            data[key] = Decimal(data[key])
        for key in ("day_locked", "week_locked"):
            if type(data[key]) is not bool:
                raise ValueError("Lock flag has wrong type")
        for key in ("day", "week", "account_fingerprint"):
            if not isinstance(data[key], str):
                raise ValueError("State identity/date has wrong type")
        return GuardState(**{key: data[key] for key in _FIELDS})
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
        raise ValueError("Guard state unreadable; manual investigation required") from exc


def save_state(path: str | Path, state: GuardState) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    for field in ("day_start_equity", "week_start_equity", "week_peak_equity"):
        payload[field] = str(payload[field])
    payload["schema"] = 1
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=file.parent,
            prefix=".guard-", suffix=".tmp", delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            os.chmod(temp_path, 0o600)
            json.dump(payload, handle, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, file)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
