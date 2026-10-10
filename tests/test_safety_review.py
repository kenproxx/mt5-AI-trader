from dataclasses import replace
from decimal import Decimal

import pytest

from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.risk.engine import RiskEngine


@pytest.mark.parametrize("mode", [None, 1, 2, False])
def test_non_demo_mode_fails_closed(mode):
    broker = MockAdapter()
    broker.account = replace(broker.account, account_trade_mode=mode)
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    assert status.state == BrokerState.TRADING_DISABLED
    assert not status.eligible


@pytest.mark.parametrize("invalid", [None, 0.1, float("nan"), Decimal("NaN"), Decimal("Infinity")])
def test_invalid_stop_never_raises(invalid):
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    decision = RiskEngine(broker).size_order(
        status, side="BUY", stop=invalid, costs_usd=Decimal("0"),
    )
    assert decision.state == BrokerState.NO_TRADE


@pytest.mark.parametrize("invalid", [None, float("nan"), Decimal("NaN"), Decimal("Infinity")])
def test_invalid_daily_baseline_never_raises(invalid):
    broker = MockAdapter()
    status = CompatibilityChecker(broker).inspect(now_epoch=broker.tick.time)
    decision = RiskEngine(broker).size_order(
        status, side="BUY", stop=Decimal("2999"), costs_usd=Decimal("0"),
        daily_start_equity=invalid if invalid is not None else Decimal("NaN"),
    )
    assert decision.state == BrokerState.NO_TRADE


def test_mock_profit_is_decimal():
    broker = MockAdapter()
    result = broker.order_calc_profit("BUY", "XAUUSD", 0.01, 3000.2, 2999)
    assert result == Decimal("-1.200")


def test_mock_margin_is_decimal():
    broker = MockAdapter()
    result = broker.order_calc_margin("BUY", "XAUUSD", 0.01, 3000.2)
    assert result > Decimal("5")
