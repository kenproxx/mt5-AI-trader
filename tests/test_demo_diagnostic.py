from decimal import Decimal

from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.validation.demo_diagnostic import run_demo_diagnostic


def test_mock_min_lot_report():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time,
    )
    assert result.state == BrokerState.LOT_BELOW_MINIMUM.value
    assert result.margin_min_lot_usd is not None
    assert result.leverage == 50
    assert "DEMO mode not independently verified" in result.reason


def test_disconnect_is_fail_closed():
    adapter = MockAdapter()
    adapter.connected = False
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time,
    )
    assert result.state == BrokerState.BROKER_DISCONNECTED.value
    assert result.margin_min_lot_usd is None


def test_report_excludes_credentials():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time,
    )
    assert "password" not in result.public_dict()
    assert "login" not in result.public_dict()
