from datetime import UTC, datetime

from app.broker.models import BrokerState
from app.validation.audit import build_audit
from app.validation.demo_diagnostic import DemoDiagnostic


def test_unverified_account_stays_blocked():
    d = DemoDiagnostic("TRADE_ELIGIBLE", "any message")
    result = build_audit(d, now=datetime(2026, 1, 1, tzinfo=UTC))
    assert result.mode == "UNVERIFIED"
    assert not result.can_trade


def test_report_does_not_copy_untrusted_reason():
    d = DemoDiagnostic(BrokerState.NO_TRADE.value, "token=secret")
    result = build_audit(d)
    assert "secret" not in str(result.public_dict())


def test_margin_and_loss_are_preserved():
    d = DemoDiagnostic(
        BrokerState.LOT_BELOW_MINIMUM.value, "too risky",
        verified_demo=True, volume_min="0.01",
        margin_min_lot_usd="60.004",
        stop_loss_min_lot_usd="1.20", risk_budget_usd="0.025",
    )
    result = build_audit(d)
    assert result.estimated_minimum_margin_usd == "60.004"
    assert result.risk_budget_usd == "0.025"
    assert not result.can_trade


def test_nonfinite_values_removed():
    d = DemoDiagnostic(BrokerState.NO_TRADE.value, "x", margin_min_lot_usd="NaN")
    assert build_audit(d).estimated_minimum_margin_usd is None
