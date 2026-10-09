import json
from datetime import UTC, datetime

import pytest

from app.validation.audit import build_audit
from app.validation.audit_export import export_audit_json
from app.validation.demo_diagnostic import DemoDiagnostic


def test_export_sanitized_json(tmp_path):
    audit = build_audit(
        DemoDiagnostic("NO_TRADE", "secret password=abc"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    path = export_audit_json(audit, tmp_path / "audit.json")
    data = json.loads(path.read_text())
    assert data["can_trade"] is False
    assert "password" not in path.read_text()
    assert data["mode"] == "UNVERIFIED"


def test_never_overwrite_existing_file(tmp_path):
    audit = build_audit(DemoDiagnostic("NO_TRADE", "x"))
    path = tmp_path / "audit.json"
    path.write_text("previous evidence")
    with pytest.raises(FileExistsError):
        export_audit_json(audit, path)
    assert path.read_text() == "previous evidence"


def test_wrong_extension_rejected(tmp_path):
    audit = build_audit(DemoDiagnostic("NO_TRADE", "x"))
    with pytest.raises(ValueError):
        export_audit_json(audit, tmp_path / "audit.txt")
