from decimal import Decimal
from types import SimpleNamespace

from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.validation.demo_diagnostic import run_demo_diagnostic


def demo_module(mode=0):
    return SimpleNamespace(
        ACCOUNT_TRADE_MODE_DEMO=0,
        account_info=lambda: SimpleNamespace(trade_mode=mode),
    )


def test_mock_min_lot_report_with_verified_demo():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time, mt5_module=demo_module(),
    )
    assert result.state == BrokerState.LOT_BELOW_MINIMUM.value
    assert result.verified_demo
    assert result.margin_min_lot_usd is not None
    assert result.leverage == 50


def test_live_mode_blocks_before_margin_calculation():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time, mt5_module=demo_module(2),
    )
    assert result.state == BrokerState.NO_TRADE.value
    assert not result.verified_demo
    assert result.margin_min_lot_usd is None


def test_missing_mode_blocks():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time,
    )
    assert result.state == BrokerState.NO_TRADE.value


def test_disconnect_is_fail_closed():
    adapter = MockAdapter()
    adapter.connected = False
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time, mt5_module=demo_module(),
    )
    assert result.state == BrokerState.BROKER_DISCONNECTED.value


def test_report_excludes_credentials():
    adapter = MockAdapter()
    result = run_demo_diagnostic(
        adapter, side="BUY", stop=Decimal("2999.00"),
        now_epoch=adapter.tick.time, mt5_module=demo_module(),
    )
    assert "password" not in result.public_dict()
    assert "login" not in result.public_dict()
