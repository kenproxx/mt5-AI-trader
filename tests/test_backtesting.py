from decimal import Decimal

import pytest

from app.backtesting.metrics import summarize
from app.backtesting.validation import chronological_split


def test_metrics():
    m = summarize([Decimal("0.02"), Decimal("-0.01")])
    assert m["net_profit"] == Decimal("0.01")
    assert m["trades"] == 2
    assert m["profit_factor"] == 2


def test_no_trades():
    assert summarize([])["win_rate"] is None


def test_drawdown():
    m = summarize([-1, 0.5])
    assert m["max_drawdown_pct"] == 20


def test_splits():
    records = [{"time": i} for i in range(100)]
    train, val, test = chronological_split(records, embargo=2)
    assert train[-1]["time"] < val[0]["time"]
    assert val[-1]["time"] < test[0]["time"]


def test_duplicate_rejected():
    with pytest.raises(ValueError):
        chronological_split([{"time": 1}] * 20)
