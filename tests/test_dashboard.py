from decimal import Decimal

import pytest

from app.dashboard.report import render_html
from app.dashboard.snapshot import build_snapshot


def test_demo_snapshot():
    result = build_snapshot(
        mode="DEMO", broker_connected=True, data_fresh=True,
        risk_ready=True, trade_pnl=[Decimal("0.01"), Decimal("-0.005")]
    )
    assert result.healthy
    assert result.trades == 2
    assert result.net_profit_usd == "0.005"


def test_fail_closed_status():
    result = build_snapshot(
        mode="DEMO", broker_connected=False, data_fresh=True,
        risk_ready=True, trade_pnl=[]
    )
    assert not result.healthy
    assert "broker_disconnected" in result.blockers


def test_reject_live():
    with pytest.raises(ValueError):
        build_snapshot(
            mode="LIVE", broker_connected=True, data_fresh=True,
            risk_ready=True, trade_pnl=[]
        )


def test_html_escapes():
    result = build_snapshot(
        mode="DEMO", broker_connected=True, data_fresh=True,
        risk_ready=True, trade_pnl=[]
    )
    html = render_html(result)
    assert "<table>" in html
    assert "Not a trading control panel" in html
