from decimal import Decimal

from app.broker.compatibility import CompatibilityChecker
from app.broker.mock import MockAdapter
from app.broker.models import BrokerState
from app.execution.paper import evaluate_paper_signal
from app.indicators.trend import atr, ema
from app.strategies.pullback import Signal, signal_from_closed_candles


def test_ema_causal():
    a = ema([1, 2, 3], 2)
    b = ema([1, 2, 3, 1000], 2)
    assert a == b[:3]


def test_atr_causal():
    candles = [{"high": 2, "low": 1, "close": 1.5}] * 4
    assert atr(candles, 2) == atr(candles + [{"high": 100, "low": 1, "close": 2}], 2)[:4]


def test_strategy_warmup():
    assert signal_from_closed_candles([], [], [], []).side == "HOLD"


def test_paper_rejects_min_lot():
    b = MockAdapter()
    status = CompatibilityChecker(b).inspect(now_epoch=b.tick.time)
    decision = evaluate_paper_signal(
        b, status, Signal("BUY", "test"), Decimal("2999"), Decimal("0.005")
    )
    assert decision.state == BrokerState.LOT_BELOW_MINIMUM


def test_paper_hold():
    b = MockAdapter()
    status = CompatibilityChecker(b).inspect(now_epoch=b.tick.time)
    assert evaluate_paper_signal(
        b, status, Signal("HOLD", "no signal"), Decimal("2999"), Decimal("0")
    ).state == BrokerState.NO_TRADE
