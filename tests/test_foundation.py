from dataclasses import replace
from decimal import Decimal
import pytest
from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.broker.preflight import order_preflight
from app.config.policy import TradingPolicy
from app.risk.engine import RiskEngine, RiskDecision


def inspect(b):
    return CompatibilityChecker(b).inspect(now_epoch=b.tick.time)


def test_mock_compatible():
    assert inspect(MockAdapter()).eligible


def test_leverage_hard_locked():
    b = MockAdapter()
    b.account = replace(b.account, leverage=100)
    assert inspect(b).state == BrokerState.LEVERAGE_MISMATCH


def test_connection_offline():
    b = MockAdapter()
    b.connected = False
    assert inspect(b).state == BrokerState.BROKER_DISCONNECTED


def test_symbol_invalid():
    b = MockAdapter()
    b.symbol = replace(b.symbol, volume_step=Decimal("0"))
    assert inspect(b).state == BrokerState.INVALID_SYMBOL_SPECIFICATION


def test_stale_tick():
    b = MockAdapter()
    assert CompatibilityChecker(b).inspect(now_epoch=b.tick.time + 31).state == BrokerState.STALE_DATA


def test_account_disabled():
    b = MockAdapter()
    b.account = replace(b.account, trade_allowed=False)
    assert inspect(b).state == BrokerState.TRADING_DISABLED


def test_micro_capital_min_lot_rejected():
    b = MockAdapter()
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"), costs_usd=Decimal("0.005")
    )
    assert x.state == BrokerState.LOT_BELOW_MINIMUM


def test_margin_rejected_even_if_risk_fits():
    b = MockAdapter()
    b.symbol = replace(b.symbol, trade_contract_size=Decimal("0.01"))
    b.order_calc_margin = lambda *a: 4.0
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"), costs_usd=Decimal("0")
    )
    assert x.state == BrokerState.INSUFFICIENT_MARGIN


def test_mock_risk_can_pass():
    b = MockAdapter()
    b.symbol = replace(b.symbol, trade_contract_size=Decimal("0.01"))
    b.order_calc_margin = lambda *a: 0.05
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"), costs_usd=Decimal("0")
    )
    assert x.allowed
    assert x.estimated_loss_usd <= Decimal("0.025")


def test_daily_limit():
    b = MockAdapter()
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"),
        costs_usd=Decimal("0"), daily_loss_usd=Decimal("0.10")
    )
    assert x.state == BrokerState.RISK_LIMIT_EXCEEDED


def test_remaining_daily_budget():
    b = MockAdapter()
    b.symbol = replace(b.symbol, trade_contract_size=Decimal("0.01"))
    b.order_calc_margin = lambda *a: 0.05
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"),
        costs_usd=Decimal("0"), daily_loss_usd=Decimal("0.09999")
    )
    assert x.state == BrokerState.LOT_BELOW_MINIMUM


def test_open_position_limit():
    b = MockAdapter()
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.00"),
        costs_usd=Decimal("0"), open_positions=1
    )
    assert x.state == BrokerState.RISK_LIMIT_EXCEEDED


def test_stop_too_close():
    b = MockAdapter()
    x = RiskEngine(b).size_order(
        inspect(b), side="BUY", stop=Decimal("2999.95"), costs_usd=Decimal("0")
    )
    assert x.state == BrokerState.NO_TRADE


def test_order_check():
    b = MockAdapter()
    decision = RiskDecision(BrokerState.TRADE_ELIGIBLE, "sized")
    assert order_preflight(b, decision, {"sl": 2999.0}) == BrokerState.TRADE_ELIGIBLE
    b.order_check_result = type("Result", (), {"retcode": 10009})()
    assert order_preflight(b, decision, {"sl": 2999.0}) == BrokerState.ORDER_REJECTED
    assert order_preflight(b, decision, {}) == BrokerState.NO_TRADE


def test_invalid_policy():
    with pytest.raises(ValueError):
        TradingPolicy(required_leverage=100)
    with pytest.raises(ValueError):
        TradingPolicy(live_enabled=True)
