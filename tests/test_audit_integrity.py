import json

import pytest

from app.validation.audit import build_audit
from app.validation.audit_export import export_audit_json
from app.validation.audit_integrity import verify_audit_file
from app.validation.demo_diagnostic import DemoDiagnostic


def test_exported_report_verifies(tmp_path):
    audit = build_audit(DemoDiagnostic("NO_TRADE", "blocked"))
    path = export_audit_json(audit, tmp_path / "audit.json")
    digest = verify_audit_file(path)
    assert len(digest) == 64
    assert digest == verify_audit_file(path)


def test_tampered_authorization_rejected(tmp_path):
    audit = build_audit(DemoDiagnostic("NO_TRADE", "blocked"))
    path = export_audit_json(audit, tmp_path / "audit.json")
    data = json.loads(path.read_text())
    data["can_trade"] = True
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_audit_file(path)


def test_unknown_field_rejected(tmp_path):
    audit = build_audit(DemoDiagnostic("NO_TRADE", "blocked"))
    path = export_audit_json(audit, tmp_path / "audit.json")
    data = json.loads(path.read_text())
    data["password"] = "sensitive"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_audit_file(path)


def test_oversized_report_rejected(tmp_path):
    path = tmp_path / "audit.json"
    path.write_text(" " * 8193)
    with pytest.raises(ValueError):
        verify_audit_file(path)
